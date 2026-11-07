// Integração com o iframe da seção Carreira do site Viva+.
// Carregado no <head>, antes do CSS ser aplicado, para não "piscar":
// marca a página com .is-embedded para o CSS usar o layout compacto.
//
// Dentro do iframe, também conversa com o site (js/carreira.js lá):
//   { type: "vivaplus:altura", altura }  → o site ajusta a altura da moldura
//   { type: "vivaplus:etapa",  etapa }   → o site destaca o passo 01/02/03
//   { type: "vivaplus:abrir-setor", setorId } → o site abre o modal do setor
//   { type: "vivaplus:pedir-tema" }      → o site responde com vivaplus:tema
// E recebe do site:
//   { type: "vivaplus:tema", tema: "claro" | "escuro" }
(function () {
    "use strict";

    const html = document.documentElement;
    const embutido = window.self !== window.top;

    let origens = [];
    try {
        origens = JSON.parse(html.dataset.origens || "[]");
    } catch (e) { /* sem origens, não envia nada */ }

    // Só fala com o site se ele for o pai do iframe (ancestorOrigins existe
    // no Chrome/Safari; no Firefox, o postMessage com targetOrigin errado é
    // simplesmente descartado pelo navegador).
    const ancestrais = window.location.ancestorOrigins;
    const paiConhecido = embutido &&
        (!ancestrais || !ancestrais.length || origens.includes(ancestrais[0]));

    if (embutido) html.classList.add("is-embedded");

    function enviar(mensagem) {
        if (!paiConhecido) return false;
        origens.forEach((origem) => {
            try { window.parent.postMessage(mensagem, origem); } catch (e) { /* origem inválida */ }
        });
        return true;
    }

    window.vivaplusSite = { embutido: paiConhecido, enviar };

    /* ---------- Tema claro/escuro ----------
       Em outra aba: segue o sistema (e acompanha se ele mudar).
       Dentro do site: começa pelo sistema e, assim que o site avisa
       { type: "vivaplus:tema", tema: "claro" | "escuro" }, passa a seguir
       o botão de tema de lá. */
    const sistema = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)") : null;
    let temaDoSite = false;

    function aplicarTema(escuro) {
        if (escuro) html.setAttribute("data-theme", "dark");
        else html.removeAttribute("data-theme");
    }

    aplicarTema(Boolean(sistema && sistema.matches));
    if (sistema) {
        const seguirSistema = (e) => { if (!temaDoSite) aplicarTema(e.matches); };
        if (sistema.addEventListener) sistema.addEventListener("change", seguirSistema);
        else if (sistema.addListener) sistema.addListener(seguirSistema);
    }

    if (!paiConhecido) return;

    window.addEventListener("message", (e) => {
        if (e.source !== window.parent || !origens.includes(e.origin)) return;
        const dados = e.data || {};
        if (dados.type === "vivaplus:tema" && (dados.tema === "claro" || dados.tema === "escuro")) {
            temaDoSite = true;
            aplicarTema(dados.tema === "escuro");
        }
    });

    // Pede o tema já: o site pode ter carregado antes ou depois desta página
    enviar({ type: "vivaplus:pedir-tema" });

    document.addEventListener("DOMContentLoaded", () => {
        const etapa = Number(html.dataset.etapa) || 0;
        if (etapa) enviar({ type: "vivaplus:etapa", etapa });

        // Manda a altura do conteúdo sempre que ela muda, para o site
        // ajustar a moldura e evitar a rolagem dentro do iframe.
        let ultima = 0;
        const medir = () => {
            const altura = Math.ceil(document.body.getBoundingClientRect().height);
            if (Math.abs(altura - ultima) < 4) return;
            ultima = altura;
            enviar({ type: "vivaplus:altura", altura });
        };
        if ("ResizeObserver" in window) {
            new ResizeObserver(medir).observe(document.body);
        }
        window.addEventListener("load", medir);
        medir();
    });
})();
