// Integração com o iframe da seção Carreira do site Viva+.
// Carregado no <head>, antes do CSS ser aplicado, para não "piscar":
// marca a página com .is-embedded para o CSS usar o layout compacto.
//
// Dentro do iframe, também conversa com o site (js/carreira.js lá):
//   { type: "vivaplus:altura", altura }  → o site ajusta a altura da moldura
//   { type: "vivaplus:etapa",  etapa }   → o site destaca o passo 01/02/03
//   { type: "vivaplus:abrir-setor", setorId } → o site abre o modal do setor
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

    if (!paiConhecido) return;

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
