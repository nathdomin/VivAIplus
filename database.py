import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Carrega as variáveis do arquivo .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Credenciais do Supabase ausentes. Verifique o arquivo .env.")

# Inicializa o cliente do Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)