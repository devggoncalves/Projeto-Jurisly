document.addEventListener("DOMContentLoaded", () => {
  const botao = document.getElementById("collapseSidebar");
  const raiz = document.querySelector(".dashboard-page");
  if (!botao || !raiz) return;

  botao.addEventListener("click", () => {
    raiz.classList.toggle("sidebar-collapsed");
    const recolhido = raiz.classList.contains("sidebar-collapsed");
    botao.textContent = recolhido ? "»" : "«";
    botao.setAttribute("aria-label", recolhido ? "Expandir menu" : "Recolher menu");
  });
});
