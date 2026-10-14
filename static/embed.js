// Marca a página quando o agente está dentro do iframe da seção Carreira
// do site Viva+, para o CSS usar o layout compacto (.is-embedded).
// Carregado no <head>, antes do CSS ser aplicado, para não "piscar".
if (window.self !== window.top) {
    document.documentElement.classList.add("is-embedded");
}
