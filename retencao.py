"""Retenção de dados (LGPD): apaga do Supabase Storage os currículos mais
antigos que o prazo.

Os registros da tabela "candidatos" são apagados pelo próprio banco (job do
pg_cron em supabase/fase3_lgpd.sql), com o mesmo prazo. Os arquivos não podem
ser apagados por SQL (o Storage exige a API), então o agente cuida deles: roda
ao iniciar e depois a cada 24 h, numa thread em segundo plano. Como o Render
hiberna o serviço, a limpeza também acontece sempre que ele acorda.

Apagar e listar arquivos exige a chave secreta do Supabase
(SUPABASE_SERVICE_KEY). Ela é usada SÓ aqui: o resto do agente continua com a
chave publishable, que pelo RLS só consegue inserir. Sem a chave secreta, a
limpeza fica desligada e o aviso aparece no log.
"""
import os
import threading
import time
from datetime import datetime, timedelta, timezone

RETENCAO_DIAS = int(os.getenv("RETENCAO_DIAS", "180"))
BUCKET_CURRICULOS = os.getenv("SUPABASE_BUCKET", "curriculos")
INTERVALO_SEGUNDOS = 24 * 60 * 60
POR_PAGINA = 1000


def _data(texto):
    # O Storage devolve "2026-11-06T15:00:00.123Z"
    return datetime.fromisoformat(texto.replace("Z", "+00:00"))


def limpar_arquivos_antigos(bucket, dias=RETENCAO_DIAS, agora=None):
    """Apaga os arquivos enviados há mais de `dias` dias. Retorna quantos."""
    limite = (agora or datetime.now(timezone.utc)) - timedelta(days=dias)
    antigos = []
    offset = 0
    while True:
        # Do mais antigo para o mais novo: para de listar ao passar do limite
        pagina = bucket.list("", {
            "limit": POR_PAGINA,
            "offset": offset,
            "sortBy": {"column": "created_at", "order": "asc"},
        })
        arquivos = [a for a in pagina if a.get("created_at")]  # pastas não têm data
        vencidos = [a["name"] for a in arquivos if _data(a["created_at"]) < limite]
        antigos.extend(vencidos)
        if len(pagina) < POR_PAGINA or len(vencidos) < len(arquivos):
            break
        offset += POR_PAGINA

    for i in range(0, len(antigos), 100):
        bucket.remove(antigos[i:i + 100])
    return len(antigos)


def iniciar_limpeza_periodica():
    url = os.getenv("SUPABASE_URL")
    chave_secreta = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not chave_secreta:
        print("Retenção: SUPABASE_SERVICE_KEY não definida, limpeza automática dos currículos desativada.")
        return

    from supabase import create_client
    bucket = create_client(url, chave_secreta).storage.from_(BUCKET_CURRICULOS)

    def ciclo():
        while True:
            try:
                apagados = limpar_arquivos_antigos(bucket)
                print(f"Retenção: {apagados} currículo(s) com mais de {RETENCAO_DIAS} dias apagado(s) do Storage.")
            except Exception as e:
                print(f"Retenção: erro ao limpar currículos antigos do Storage: {e}")
            time.sleep(INTERVALO_SEGUNDOS)

    threading.Thread(target=ciclo, name="retencao-storage", daemon=True).start()
