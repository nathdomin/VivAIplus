from fastapi import FastAPI, Request, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from b2sdk.v2 import InMemoryAccountInfo, B2Api
import uuid
import os
import io
import pdfplumber
import docx
import requests

load_dotenv()

from database import supabase 

app = FastAPI(title="Sistema de Orientação Viva+")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

b2_bucket = None

# --- Configuração do Backblaze B2 ---
try:
    print("\nTentando conectar ao Backblaze B2...")
    info = InMemoryAccountInfo()
    b2_api = B2Api(info)
    
    key_id = os.getenv("B2_KEY_ID")
    app_key = os.getenv("B2_APPLICATION_KEY")
    bucket_name = os.getenv("B2_BUCKET_NAME")
    
    if not key_id or not app_key or not bucket_name:
        print("❌ ERRO: Faltam credenciais no arquivo .env!")
    else:
        b2_api.authorize_account("production", key_id, app_key)
        b2_bucket = b2_api.get_bucket_by_name(bucket_name)
        print(f"✅ Conectado com sucesso ao bucket: {bucket_name}\n")
except Exception as e:
    print(f"\n❌ ERRO GRAVE AO CONECTAR NO BACKBLAZE:")
    print(f"Detalhe: {str(e)}\n")

# --- Função de Extração de Texto ---
def extrair_texto_arquivo(conteudo_bytes, extensao):
    texto_extraido = ""
    arquivo_memoria = io.BytesIO(conteudo_bytes)
    
    try:
        if extensao == 'pdf':
            with pdfplumber.open(arquivo_memoria) as pdf:
                for pagina in pdf.pages:
                    texto_pagina = pagina.extract_text()
                    if texto_pagina:
                        texto_extraido += texto_pagina + "\n"
        elif extensao == 'docx':
            doc = docx.Document(arquivo_memoria)
            for paragrafo in doc.paragraphs:
                texto_extraido += paragrafo.text + "\n"
    except Exception as e:
        print(f"Erro na extração de texto: {e}")
        texto_extraido = "Erro ao tentar ler o texto do documento."
        
    return texto_extraido.strip()


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="index.html"
    )


@app.post("/upload")
async def processar_candidatura(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    areas_interesse: str = Form(...),
    curriculo: UploadFile = File(...)
):
    if b2_bucket is None:
        raise HTTPException(status_code=500, detail="Erro de configuração no servidor.")

    extensao = curriculo.filename.lower().split('.')[-1]
    if extensao not in ['pdf', 'docx']:
        raise HTTPException(status_code=400, detail="Erro: Apenas arquivos PDF ou DOCX são permitidos.")
    
    conteudo_arquivo = await curriculo.read()
    
    LIMITE_5MB = 5 * 1024 * 1024
    if len(conteudo_arquivo) > LIMITE_5MB:
        raise HTTPException(status_code=400, detail="Erro: O arquivo ultrapassa o limite de 5MB.")
        
    nome_seguro = f"{uuid.uuid4()}.{extensao}"
    
    # Extrai o texto do arquivo recebido
    texto_curriculo = extrair_texto_arquivo(conteudo_arquivo, extensao)
    
    try:
        b2_bucket.upload_bytes(
            data_bytes=conteudo_arquivo,
            file_name=nome_seguro,
            file_infos={'content-type': curriculo.content_type}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno ao salvar arquivo: {str(e)}")
    
    # Redireciona para a tela de revisão
    return templates.TemplateResponse(
        request=request,
        name="revisao.html",
        context={
            "candidato": nome,
            "arquivo_salvo": nome_seguro,
            "texto_extraido": texto_curriculo
        }
    )


@app.post("/analisar")
async def analisar_candidato(
    request: Request,
    nome: str = Form(...),
    arquivo_salvo: str = Form(...),
    texto_curriculo: str = Form(...)
):
    # 1. Buscar os setores disponíveis no Supabase
    try:
        resposta_setores = supabase.table("setores").select("*").execute()
        setores_disponiveis = resposta_setores.data
    except Exception as e:
        print(f"Erro ao buscar setores no banco: {e}")
        setores_disponiveis = []

    # 2. Formatar os setores para a IA
    texto_vagas = ""
    for setor in setores_disponiveis:
        texto_vagas += f"- {setor['nome']}: {setor['descricao']} (Requisitos principais: {setor['requisitos']})\n"

    if not texto_vagas:
        texto_vagas = "- Nenhuma vaga específica cadastrada. Avalie o perfil de forma geral."

    # 3. Análise ética da IA
    prompt = f"""
    Você é um assistente de recrutamento ético e imparcial da empresa Viva+.
    Sua função é analisar o currículo abaixo e recomendar o setor administrativo mais adequado para o candidato.
    
    Abaixo estão os ÚNICOS setores disponíveis na Viva+ atualmente:
    {texto_vagas}
    
    Regras de Privacidade e Ética (LGPD):
    - Baseie-se ESTRITAMENTE nas habilidades técnicas, cursos e experiências descritas.
    - Ignore idade, gênero, estado civil ou qualquer dado pessoal sensível.
    - É EXPRESSAMENTE PROIBIDO utilizar critérios de "fit cultural".
    - REGRA CRÍTICA: Você DEVE escolher obrigatoriamente UM dos setores listados acima. Não invente setores que não estão na lista.
    
    Currículo do candidato:
    {texto_curriculo}
    
    Retorne a sua análise EXATAMENTE com a seguinte estrutura:
    SETOR RECOMENDADO: [Nome Exato do Setor Escolhido]
    JUSTIFICATIVA TÉCNICA: [Explique brevemente quais habilidades e experiências do currículo levaram a essa recomendação. Seja claro e objetivo.]
    """
    
    api_key = os.getenv("GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={api_key}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    try:
        # TIMEOUT de 60 segundos
        resposta = requests.post(url, headers=headers, json=payload, timeout=60)
        resposta_json = resposta.json()
        
        # Detecta Alta Demanda
        if resposta.status_code == 503 or resposta_json.get('error', {}).get('code') == 503:
            print("⏳ Alta demanda detectada. Redirecionando para auto-reenvio...")
            return templates.TemplateResponse(
                request=request,
                name="alta_demanda.html",
                context={
                    "nome": nome,
                    "arquivo_salvo": arquivo_salvo,
                    "texto_curriculo": texto_curriculo
                }
            )
        
        if resposta.status_code != 200:
            raise Exception(f"Erro da API do Google: {resposta_json}")
            
        resultado_texto = resposta_json['candidates'][0]['content']['parts'][0]['text']
        
    except requests.exceptions.ReadTimeout:
        print("⏳ Timeout de rede. Redirecionando para auto-reenvio...")
        return templates.TemplateResponse(
            request=request,
            name="alta_demanda.html",
            context={
                "nome": nome,
                "arquivo_salvo": arquivo_salvo,
                "texto_curriculo": texto_curriculo
            }
        )
    except Exception as e:
        print(f"\n--- ERRO NA API DO GEMINI ---")
        print(str(e))
        print("-----------------------------\n")
        raise HTTPException(status_code=500, detail=f"Erro ao processar a Inteligência Artificial: {str(e)}")

    # 4. Salvar no Supabase
    try:
        dados_candidato = {
            "nome": nome,
            "arquivo_salvo": arquivo_salvo,
            "curriculo_texto": texto_curriculo,
            "analise_ia": resultado_texto
        }
        supabase.table("candidatos").insert(dados_candidato).execute()
    except Exception as e:
        print(f"Erro ao salvar no banco de dados: {e}")

    # 5. Mostrar tela final
    return templates.TemplateResponse(
        request=request,
        name="resultado.html",
        context={
            "candidato": nome.split(' ')[0],
            "analise": resultado_texto
        }
    )