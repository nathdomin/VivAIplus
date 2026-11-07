# VivAIplus — agente de orientação de carreira da Viva+

Recebe o currículo do candidato (PDF ou DOCX), extrai o texto, deixa o
candidato revisar e pede ao Gemini um ranking dos setores da Viva+ com
maior aderência. Roda no Render e aparece dentro da seção **Carreira** do
site ([vivaplus](https://github.com/nathdomin/vivaplus)).

## Fluxo

1. `/` — formulário (nome, e-mail, áreas de interesse em chips com os
   setores do site, currículo) com aceite LGPD obrigatório.
2. `/upload` — confere tipo e assinatura do arquivo, salva no Supabase Storage (bucket privado `curriculos`) e
   mostra o texto extraído (inclusive tabelas do DOCX) para revisão. Se o
   arquivo não tiver texto legível (PDF escaneado), pede para colar o texto.
3. `/analisar` — remove dados pessoais do texto, chama o Gemini, salva o
   resultado no Supabase e mostra o ranking com link para cada setor no site.

Os setores vêm de `data/setores.json` do site (mesmos ids, ícones e cores do
organograma). As áreas de interesse **não** entram no prompt: a aderência se
baseia só no currículo; elas aparecem como selo no resultado e ficam para o RH.

Erros aparecem numa página no estilo do site (`templates/erro.html`), e cada
IP pode fazer até `LIMITE_REQUISICOES` envios por minuto em cada etapa.

### Integração com o site (iframe)

`static/embed.js` detecta o iframe e troca mensagens com `js/carreira.js` do
site (`postMessage`, só para as origens de `SITE_URL` e `FRAME_ANCESTORS`):

| Mensagem | Para quê |
|---|---|
| `vivaplus:altura` | O site ajusta a altura da moldura ao conteúdo. |
| `vivaplus:etapa` | O site destaca o passo 01/02/03 ao lado da moldura. |
| `vivaplus:rolar-topo` | Ao enviar um formulário, o site rola até o topo da moldura. |
| `vivaplus:abrir-setor` | "Conhecer o setor" abre o modal do setor no site. |

## Variáveis de ambiente

| Variável | Obrigatória | Padrão | Para quê |
|---|---|---|---|
| `SUPABASE_URL`, `SUPABASE_KEY` | sim | — | Banco (tabela `candidatos`) e Storage (currículos). A chave publishable basta: o agente só insere linhas e envia arquivos. |
| `SUPABASE_SERVICE_KEY` | não | — | Chave secreta, usada **só** pela limpeza de 180 dias dos arquivos (`retencao.py`). Sem ela, a limpeza automática fica desligada. |
| `SUPABASE_BUCKET` | não | `curriculos` | Bucket do Storage onde ficam os currículos. |
| `GEMINI_API_KEY` | sim | — | IA. |
| `GEMINI_MODEL` | não | `gemini-3.1-flash-lite` | Modelo do Gemini. |
| `GEMINI_TENTATIVAS` | não | `4` | Tentativas no servidor quando o Gemini está sobrecarregado (429/5xx/rede). |
| `GEMINI_ESPERA_BASE` | não | `2` | Espera inicial entre tentativas, em segundos (dobra a cada tentativa: 2, 4, 8...). |
| `SITE_URL` | não | `https://vivaplus.netlify.app` | De onde vêm os setores e para onde apontam os links. |
| `FRAME_ANCESTORS` | não | — | Origens extras que podem exibir o agente em iframe (ex.: `http://127.0.0.1:5501`). |
| `RETENCAO_DIAS` | não | `180` | Prazo para apagar os currículos do Storage. Mantenha igual ao do SQL abaixo. |
| `LIMITE_REQUISICOES` | não | `6` | Envios por minuto, por IP, em `/upload` e em `/analisar`. |

## LGPD

- **Consentimento:** o envio só é aceito com o checkbox marcado; a data do
  aceite vai para a coluna `consentimento_em`.
- **E-mail e interesses:** guardados nas colunas `email` e `areas_interesse`
  só para o RH retornar contato; nunca vão para o Gemini.
- **Minimização:** antes de ir para o Gemini, o texto passa por
  `privacidade.py`, que remove nome, e-mail, telefone, CPF/RG, endereço, CEP,
  links pessoais, idade, data de nascimento e estado civil. O texto revisado
  pelo candidato é o que fica salvo no Supabase.
- **Retenção:** o agente apaga do Storage os arquivos com mais de `RETENCAO_DIAS`
  dias (`retencao.py`, ao iniciar e a cada 24 h). No Supabase, um job do
  `pg_cron` apaga os registros com o mesmo prazo.

### Configuração única no Supabase

Rode no SQL Editor do painel, nesta ordem:

1. [`supabase/fase3_lgpd.sql`](supabase/fase3_lgpd.sql) — cria as colunas
   `created_at` e `consentimento_em`, liga o RLS (a chave do agente passa a só
   inserir, sem ler) e agenda a limpeza diária.
2. [`supabase/fase4_contato.sql`](supabase/fase4_contato.sql) — cria as
   colunas `email` e `areas_interesse`.
3. [`supabase/fase5_storage.sql`](supabase/fase5_storage.sql) — cria o
   bucket privado `curriculos` (até 5 MB, só PDF/DOCX), onde a chave do
   agente só consegue enviar arquivos. **Obrigatório**: sem ele o upload falha.

Sem os dois primeiros o agente continua funcionando: só deixa de gravar
essas colunas.

### Onde o RH vê os currículos

No painel do Supabase: **Table Editor → candidatos** para os dados e a
análise, e **Storage → curriculos** para o arquivo original. O nome do
arquivo é o valor da coluna `arquivo_salvo`.

O plano gratuito tem 1 GB de Storage. Com currículos de 100–500 KB e
retenção de 180 dias, isso cobre alguns milhares de candidatos.

## Rodar localmente

```bash
pip install -r requerimentos.txt
uvicorn main:app --reload
```
