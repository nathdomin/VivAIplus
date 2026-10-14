# VivAIplus — agente de orientação de carreira da Viva+

Recebe o currículo do candidato (PDF ou DOCX), extrai o texto, deixa o
candidato revisar e pede ao Gemini um ranking dos setores da Viva+ com
maior aderência. Roda no Render e aparece dentro da seção **Carreira** do
site ([vivaplus](https://github.com/nathdomin/vivaplus)).

## Fluxo

1. `/` — formulário com aceite LGPD obrigatório.
2. `/upload` — salva o arquivo no Backblaze B2 e mostra o texto extraído.
3. `/analisar` — remove dados pessoais do texto, chama o Gemini, salva o
   resultado no Supabase e mostra o ranking com link para cada setor no site.

Os setores vêm de `data/setores.json` do site (mesmos ids do organograma).

## Variáveis de ambiente

| Variável | Obrigatória | Padrão | Para quê |
|---|---|---|---|
| `SUPABASE_URL`, `SUPABASE_KEY` | sim | — | Banco (tabela `candidatos`). A chave publishable basta: o agente só insere. |
| `B2_KEY_ID`, `B2_APPLICATION_KEY`, `B2_BUCKET_NAME` | sim | — | Armazenamento dos currículos. |
| `GEMINI_API_KEY` | sim | — | IA. |
| `GEMINI_MODEL` | não | `gemini-3.1-flash-lite` | Modelo do Gemini. |
| `GEMINI_TENTATIVAS` | não | `4` | Tentativas no servidor quando o Gemini está sobrecarregado (429/5xx/rede). |
| `GEMINI_ESPERA_BASE` | não | `2` | Espera inicial entre tentativas, em segundos (dobra a cada tentativa: 2, 4, 8...). |
| `SITE_URL` | não | `https://vivaplus.netlify.app` | De onde vêm os setores e para onde apontam os links. |
| `FRAME_ANCESTORS` | não | — | Origens extras que podem exibir o agente em iframe (ex.: `http://127.0.0.1:5501`). |
| `RETENCAO_DIAS` | não | `180` | Prazo para apagar currículos do B2. Mantenha igual ao do SQL abaixo. |

## LGPD

- **Consentimento:** o envio só é aceito com o checkbox marcado; a data do
  aceite vai para a coluna `consentimento_em`.
- **Minimização:** antes de ir para o Gemini, o texto passa por
  `privacidade.py`, que remove nome, e-mail, telefone, CPF/RG, endereço, CEP,
  links pessoais, idade, data de nascimento e estado civil. O texto revisado
  pelo candidato é o que fica salvo no Supabase.
- **Retenção:** o agente apaga do B2 os arquivos com mais de `RETENCAO_DIAS`
  dias (`retencao.py`, ao iniciar e a cada 24 h). No Supabase, um job do
  `pg_cron` apaga os registros com o mesmo prazo.

### Configuração única no Supabase

Rode [`supabase/fase3_lgpd.sql`](supabase/fase3_lgpd.sql) no SQL Editor do
painel. Ele cria as colunas `created_at` e `consentimento_em`, liga o RLS
(a chave do agente passa a só inserir, sem ler) e agenda a limpeza diária.

### Chave do B2

Use uma chave restrita ao bucket dos currículos, só com `listFiles`,
`readFiles`, `writeFiles` e `deleteFiles` — não a chave mestra da conta.

## Rodar localmente

```bash
pip install -r requerimentos.txt
uvicorn main:app --reload
```
