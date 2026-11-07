// Comportamentos das telas do agente: upload com arrastar e soltar,
// tela de carregamento nos envios, contador de caracteres da revisão,
// links dos setores e botões de voltar/imprimir.
(function () {
    "use strict";

    const site = window.vivaplusSite || { embutido: false, enviar: () => false };

    /* ---------- Tela de carregamento ---------- */
    const overlay = document.getElementById("carregando");
    const overlayTitulo = document.getElementById("carregandoTitulo");
    const overlayTexto = document.getElementById("carregandoTexto");
    let timerPassos;

    function mostrarCarregando(form) {
        if (!overlay) return;
        overlayTitulo.textContent = form.dataset.carregando || "Processando…";
        overlayTexto.textContent = form.dataset.carregandoTexto || "";
        overlay.hidden = false;
        // No site, a moldura pode estar rolada para baixo: pede para mostrar o topo
        site.enviar({ type: "vivaplus:rolar-topo" });

        let passos = [];
        try { passos = JSON.parse(form.dataset.carregandoPassos || "[]"); } catch (e) { /* sem passos */ }
        if (passos.length) {
            let i = 0;
            overlayTitulo.textContent = passos[0];
            timerPassos = setInterval(() => {
                i = Math.min(i + 1, passos.length - 1);
                overlayTitulo.textContent = passos[i];
            }, 6000);
        }
    }

    function esconderCarregando() {
        if (overlay) overlay.hidden = true;
        clearInterval(timerPassos);
        document.querySelectorAll("form [type=submit]").forEach((b) => { b.disabled = false; });
    }

    document.querySelectorAll("form[data-carregando]").forEach((form) => {
        form.addEventListener("submit", (e) => {
            if (form.dataset.enviando === "1") { e.preventDefault(); return; }
            form.dataset.enviando = "1";
            form.querySelectorAll("[type=submit]").forEach((b) => { b.disabled = true; });
            mostrarCarregando(form);
        });
    });

    // Ao voltar com o botão do navegador, a página pode vir do cache já com
    // a tela de carregamento aberta: libera o formulário de novo.
    window.addEventListener("pageshow", (e) => {
        if (!e.persisted) return;
        document.querySelectorAll("form[data-carregando]").forEach((f) => { delete f.dataset.enviando; });
        esconderCarregando();
    });

    /* ---------- Upload do currículo ---------- */
    const dropzone = document.getElementById("dropzone");
    const inputArquivo = document.getElementById("curriculo");
    if (dropzone && inputArquivo) {
        const titulo = document.getElementById("dropzoneTitulo");
        const dica = document.getElementById("dropzoneDica");
        const erro = document.getElementById("erroCurriculo");
        const tituloOriginal = titulo.innerHTML;
        const dicaOriginal = dica.textContent;
        const limiteBytes = Number(inputArquivo.dataset.limiteMb || 5) * 1024 * 1024;

        const formatarTamanho = (bytes) =>
            bytes < 1024 * 1024 ? `${Math.max(1, Math.round(bytes / 1024))} KB`
                                : `${(bytes / 1024 / 1024).toFixed(1).replace(".", ",")} MB`;

        function validar(arquivo) {
            if (!arquivo) return "";
            const extensao = arquivo.name.toLowerCase().split(".").pop();
            if (!["pdf", "docx"].includes(extensao)) return "Envie o currículo em PDF ou DOCX.";
            if (arquivo.size > limiteBytes) return `O arquivo tem ${formatarTamanho(arquivo.size)}; o limite é ${inputArquivo.dataset.limiteMb} MB.`;
            if (arquivo.size === 0) return "O arquivo está vazio.";
            return "";
        }

        function atualizar() {
            const arquivo = inputArquivo.files[0];
            const mensagem = validar(arquivo);
            inputArquivo.setCustomValidity(mensagem);
            erro.textContent = mensagem;
            erro.hidden = !mensagem;
            dropzone.classList.toggle("tem-erro", Boolean(mensagem));
            dropzone.classList.toggle("tem-arquivo", Boolean(arquivo) && !mensagem);

            if (arquivo && !mensagem) {
                titulo.textContent = arquivo.name;
                dica.textContent = `${formatarTamanho(arquivo.size)} · clique para trocar`;
            } else {
                titulo.innerHTML = tituloOriginal;
                dica.textContent = dicaOriginal;
            }
        }

        inputArquivo.addEventListener("change", atualizar);
        ["dragenter", "dragover"].forEach((ev) =>
            dropzone.addEventListener(ev, () => dropzone.classList.add("arrastando")));
        ["dragleave", "drop"].forEach((ev) =>
            dropzone.addEventListener(ev, () => dropzone.classList.remove("arrastando")));
        atualizar();
    }

    /* ---------- Contador de caracteres da revisão ---------- */
    const textarea = document.getElementById("texto_curriculo");
    const contador = document.getElementById("contadorCaracteres");
    if (textarea && contador) {
        const maximo = Number(textarea.getAttribute("maxlength"));
        const minimo = Number(textarea.getAttribute("minlength"));
        const contar = () => {
            const n = textarea.value.length;
            contador.textContent = `${n.toLocaleString("pt-BR")} / ${maximo.toLocaleString("pt-BR")}`;
            contador.classList.toggle("is-alerta", n < minimo || n > maximo * 0.95);
        };
        textarea.addEventListener("input", contar);
        contar();
    }

    /* ---------- Links dos setores no resultado ---------- */
    // Dentro do iframe do site, pede ao próprio site para abrir o modal do
    // setor (sem recarregar a página). Fora dele, o link segue normal e abre
    // o site já com o modal aberto.
    document.querySelectorAll(".link-setor").forEach((link) => {
        link.addEventListener("click", (e) => {
            if (!site.embutido) return;
            e.preventDefault();
            site.enviar({ type: "vivaplus:abrir-setor", setorId: link.dataset.setor });
        });
    });

    /* ---------- Botões utilitários ---------- */
    document.querySelectorAll("[data-imprimir]").forEach((b) =>
        b.addEventListener("click", () => window.print()));

    document.querySelectorAll("[data-voltar]").forEach((b) =>
        b.addEventListener("click", () => {
            if (history.length > 1) history.back(); else window.location.href = "/";
        }));
})();
