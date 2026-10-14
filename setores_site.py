import os
import time
import requests
from typing import List

from models import Setor

# O site Viva+ é a fonte única dos setores: o agente lê o mesmo
# data/setores.json que alimenta o organograma e os modais do site.
SITE_URL = os.getenv("SITE_URL", "https://vivaplus.netlify.app").rstrip("/")
CACHE_SEGUNDOS = 300

_cache = {"setores": [], "carregado_em": 0.0}


def carregar_setores() -> List[Setor]:
    """Retorna os setores do site, com cache de alguns minutos.

    Se o site estiver fora do ar, usa a última lista carregada com sucesso.
    """
    if _cache["setores"] and time.time() - _cache["carregado_em"] < CACHE_SEGUNDOS:
        return _cache["setores"]

    try:
        resposta = requests.get(f"{SITE_URL}/data/setores.json", timeout=10)
        resposta.raise_for_status()
        setores = [Setor(**s) for s in resposta.json().get("setores", [])]
        if not setores:
            raise ValueError("data/setores.json não tem nenhum setor.")
        _cache["setores"] = setores
        _cache["carregado_em"] = time.time()
    except Exception as e:
        print(f"Erro ao buscar setores do site ({SITE_URL}): {e}")
        if not _cache["setores"]:
            raise

    return _cache["setores"]


def link_do_setor(setor_id: str) -> str:
    """Link que abre o modal do setor no site."""
    return f"{SITE_URL}/?setor={setor_id}#setores"
