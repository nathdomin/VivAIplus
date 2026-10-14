from pydantic import BaseModel, Field
from typing import List


class Setor(BaseModel):
    """Setor como publicado pelo site Viva+ em data/setores.json."""
    id: str
    nome: str
    resumo: str = ""
    objetivo: List[str] = []
    atividades: List[str] = []
    competencias: List[str] = []
    requisitos: List[str] = []


class RecomendacaoSetor(BaseModel):
    setor_id: str
    aderencia: int = Field(ge=0, le=100)
    justificativa: str
    evidencias: List[str] = []


class AnaliseCurriculo(BaseModel):
    resumo_perfil: str
    recomendacoes: List[RecomendacaoSetor]
