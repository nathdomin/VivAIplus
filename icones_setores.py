"""Ícones e cores dos setores, iguais aos do site Viva+.

Cópia de vivaplus/js/icones-setores.js: o campo "icone" de cada setor em
data/setores.json escolhe o SVG. Ao incluir um ícone novo lá, replique aqui.
"""
import re

_SVG = '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{}</svg>'

ICONES_SETORES = {
    "geral": _SVG.format('<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>'),
    "estrela": _SVG.format('<path d="M12 2l3 6 7 1-5 5 1.5 7L12 17.5 5.5 21 7 14 2 9l7-1z"/>'),
    "pessoas": _SVG.format('<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>'),
    "capelo": _SVG.format('<path d="M22 10v6M2 10l10-5 10 5-10 5-10-5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/>'),
    "escudo": _SVG.format('<path d="M12 22s8-4.5 8-11V5l-8-3-8 3v6c0 6.5 8 11 8 11z"/><path d="M9 12l2 2 4-4"/>'),
    "balao": _SVG.format('<path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/>'),
    "monitor": _SVG.format('<rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/>'),
    "aperto": _SVG.format('<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="m17 11 2 2 4-4"/>'),
}

COR_PADRAO = "var(--color-blue)"

# corAccent vem do painel do site e vai para um atributo style: só aceita
# cores, var(--x) e gradientes simples, nada que feche a declaração CSS.
_COR_SEGURA = re.compile(r"^[\w\s#%(),.\-]+$")


def icone_do_setor(nome_icone: str) -> str:
    return ICONES_SETORES.get(nome_icone or "", ICONES_SETORES["geral"])


def cor_do_setor(cor: str) -> str:
    cor = (cor or "").strip()
    return cor if cor and _COR_SEGURA.match(cor) else COR_PADRAO
