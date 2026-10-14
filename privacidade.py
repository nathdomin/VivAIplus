"""Remove dados pessoais do currículo antes de enviá-lo à IA (LGPD).

A IA só precisa de habilidades, cursos e experiências. Contato, documentos,
endereço, idade, estado civil e o próprio nome do candidato não entram no
prompt. O texto original continua sendo o que o candidato revisou e o que
fica salvo no Supabase; só a cópia enviada ao Gemini é anonimizada.
"""
import re
import unicodedata

# Campos rotulados ("Idade: 25", "Estado civil: solteiro" etc.): o rótulo fica,
# o valor some. O valor vai até o fim da linha ou até um separador | ; •
_ROTULOS = (
    r"nome|data\s+de\s+nascimento|nascimento|nascid[oa]\s+em|idade|estado\s+civil|"
    r"sexo|g[eê]nero|nacionalidade|naturalidade|endere[cç]o|resid[eê]ncia|bairro|"
    r"cidade\s*/\s*uf|cpf|rg|cnh|telefone|celular|whats\s*app|e-?mail|filhos|"
    r"religi[aã]o|ra[cç]a|cor|defici[eê]ncia|pcd"
)
_CAMPO_ROTULADO = re.compile(rf"(?im)^(\s*(?:{_ROTULOS}))\s*[:\-–]\s*[^\n|;•]+")
_CAMPO_NO_MEIO = re.compile(rf"(?i)(\b(?:{_ROTULOS}))\s*:\s*[^\n|;•]+")

_SUBSTITUICOES = [
    # e-mail
    (re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"), "[E-MAIL]"),
    # perfis pessoais
    (re.compile(r"(?i)(?:https?://)?(?:www\.)?(?:linkedin\.com|instagram\.com|facebook\.com|tiktok\.com|wa\.me)/\S*"), "[LINK PESSOAL]"),
    # CPF (com ou sem pontuação)
    (re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"), "[CPF]"),
    # telefone brasileiro: DDD obrigatório, celular ou fixo — "2019-2021" não casa
    (re.compile(r"(?:\+?55\s*)?\(?\b\d{2}\)?\s*9?\d{4}[-\s.]?\d{4}\b"), "[TELEFONE]"),
    # CEP (só no formato com hífen, para não confundir com outros números)
    (re.compile(r"\b\d{5}-\d{3}\b"), "[CEP]"),
    # idade solta: "25 anos de idade" — "2 anos de experiência" fica
    (re.compile(r"(?i)\b\d{1,2}\s+anos\s+de\s+idade\b"), "[IDADE]"),
    # estado civil solto: "brasileira, solteira, ..."
    (re.compile(r"(?i)\b(?:solteir[oa]|casad[oa]|divorciad[oa]|separad[oa]|vi[uú]v[oa]|uni[aã]o\s+est[aá]vel)\b"), "[ESTADO CIVIL]"),
]

# Partes do nome que não identificam ninguém sozinhas
_PARTICULAS = {"da", "de", "do", "das", "dos", "e", "di", "del", "van", "von"}


def _sem_acento(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def _remover_nome(texto, nome):
    partes = [p for p in re.split(r"\s+", nome.strip()) if len(p) >= 3 and p.lower() not in _PARTICULAS]
    if not partes:
        return texto
    # Nome completo primeiro, depois cada parte (ex.: só o sobrenome no rodapé)
    for alvo in [nome.strip()] + sorted(partes, key=len, reverse=True):
        variantes = {alvo, _sem_acento(alvo)}
        for v in variantes:
            texto = re.sub(rf"(?i)(?<![\w]){re.escape(v)}(?![\w])", "[NOME]", texto)
    # "[NOME] [NOME]" → "[NOME]"
    return re.sub(r"\[NOME\](?:\s+\[NOME\])+", "[NOME]", texto)


def anonimizar_curriculo(texto, nome=""):
    """Devolve uma cópia do texto sem dados pessoais identificáveis."""
    if nome:
        texto = _remover_nome(texto, nome)
    texto = _CAMPO_ROTULADO.sub(lambda m: f"{m.group(1)}: [REMOVIDO]", texto)
    texto = _CAMPO_NO_MEIO.sub(lambda m: f"{m.group(1)}: [REMOVIDO]", texto)
    for padrao, marcador in _SUBSTITUICOES:
        texto = padrao.sub(marcador, texto)
    return texto
