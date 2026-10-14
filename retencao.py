"""Retenção de dados (LGPD): apaga do B2 os currículos mais antigos que o prazo.

Os registros da tabela "candidatos" no Supabase são apagados pelo próprio
banco (job do pg_cron em supabase/fase3_lgpd.sql), com o mesmo prazo.
Aqui o agente cuida dos arquivos: roda ao iniciar e depois a cada 24 h,
numa thread em segundo plano. Como o Render hiberna o serviço, a limpeza
também acontece sempre que ele acorda.
"""
import os
import threading
import time

RETENCAO_DIAS = int(os.getenv("RETENCAO_DIAS", "180"))
INTERVALO_SEGUNDOS = 24 * 60 * 60


def limpar_arquivos_antigos(bucket, dias=RETENCAO_DIAS, agora=None):
    """Apaga todas as versões de arquivo enviadas há mais de `dias` dias.

    Retorna quantas versões foram apagadas.
    """
    limite_ms = ((agora or time.time()) - dias * 24 * 60 * 60) * 1000
    apagados = 0
    for versao, _ in bucket.ls(latest_only=False, recursive=True):
        if versao.upload_timestamp < limite_ms:
            bucket.delete_file_version(versao.id_, versao.file_name)
            apagados += 1
    return apagados


def iniciar_limpeza_periodica(bucket):
    if bucket is None:
        print("Retenção: B2 não configurado, limpeza de arquivos desativada.")
        return

    def ciclo():
        while True:
            try:
                apagados = limpar_arquivos_antigos(bucket)
                print(f"Retenção: {apagados} currículo(s) com mais de {RETENCAO_DIAS} dias apagado(s) do B2.")
            except Exception as e:
                print(f"Retenção: erro ao limpar arquivos antigos do B2: {e}")
            time.sleep(INTERVALO_SEGUNDOS)

    threading.Thread(target=ciclo, name="retencao-b2", daemon=True).start()
