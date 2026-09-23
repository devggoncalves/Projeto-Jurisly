document.addEventListener("DOMContentLoaded", () => {
  const raiz = document.querySelector(".dashboard-page");
  const botaoCollapse = document.getElementById("collapseSidebar");
  const botaoMenu = document.getElementById("menuToggle");
  const backdrop = document.getElementById("navBackdrop");
  const sidebar = document.getElementById("sidebar");
  if (!raiz) return;

  const mqMobile = window.matchMedia("(max-width: 760px)");

  function isMobile() {
    return mqMobile.matches;
  }

  function setNavOpen(aberto) {
    raiz.classList.toggle("nav-open", aberto);
    if (botaoMenu) {
      botaoMenu.setAttribute("aria-expanded", aberto ? "true" : "false");
      botaoMenu.setAttribute("aria-label", aberto ? "Fechar menu" : "Abrir menu");
    }
    if (backdrop) {
      backdrop.hidden = !aberto;
    }
    document.body.style.overflow = aberto && isMobile() ? "hidden" : "";
  }

  function fecharNav() {
    setNavOpen(false);
  }

  if (botaoCollapse) {
    botaoCollapse.addEventListener("click", () => {
      if (isMobile()) {
        fecharNav();
        return;
      }
      raiz.classList.toggle("sidebar-collapsed");
      const recolhido = raiz.classList.contains("sidebar-collapsed");
      botaoCollapse.textContent = recolhido ? "»" : "«";
      botaoCollapse.setAttribute("aria-label", recolhido ? "Expandir menu" : "Recolher menu");
    });
  }

  if (botaoMenu) {
    botaoMenu.addEventListener("click", () => {
      setNavOpen(!raiz.classList.contains("nav-open"));
    });
  }

  if (backdrop) {
    backdrop.addEventListener("click", fecharNav);
  }

  if (sidebar) {
    sidebar.querySelectorAll("a.nav-item").forEach((link) => {
      link.addEventListener("click", () => {
        if (isMobile()) fecharNav();
      });
    });
  }

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && raiz.classList.contains("nav-open")) {
      fecharNav();
    }
  });

  const onViewportChange = () => {
    if (!isMobile()) {
      fecharNav();
    }
  };
  if (typeof mqMobile.addEventListener === "function") {
    mqMobile.addEventListener("change", onViewportChange);
  } else if (typeof mqMobile.addListener === "function") {
    mqMobile.addListener(onViewportChange);
  }
});
