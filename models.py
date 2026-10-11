from pydantic import BaseModel
from typing import List

class Competencia(BaseModel):
    nome: str
    justificativa: str

class Requisito(BaseModel):
    nome: str
    justificativa: str

class PerfilSetor(BaseModel):
    nome: str
    descricao: str
    objetivos: str
    tarefas_comuns: List[str]
    competencias_desejaveis: List[Competencia]
    preferencias_trabalho: List[str]
    requisitos_essenciais: List[Requisito]
    versao: str
    data_revisao: str
    responsavel_aprovacao: str