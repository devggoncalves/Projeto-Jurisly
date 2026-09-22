document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-toggle-password]").forEach((botao) => {
    botao.addEventListener("click", () => {
      const id = botao.getAttribute("data-toggle-password");
      const campo = document.getElementById(id);
      if (!campo) return;

      const oculto = campo.type === "password";
      campo.type = oculto ? "text" : "password";
      botao.setAttribute("aria-label", oculto ? "Ocultar senha" : "Mostrar senha");

      const olho = botao.querySelector('[data-icon="eye"]');
      const olhoOff = botao.querySelector('[data-icon="eye-off"]');
      if (olho) olho.style.display = oculto ? "none" : "block";
      if (olhoOff) olhoOff.style.display = oculto ? "block" : "none";
    });
  });

  document.querySelectorAll("[data-login-form]").forEach((form) => {
    form.addEventListener("submit", () => {
      const botao = form.querySelector("[data-loading-button]");
      if (!botao) return;
      botao.classList.add("is-loading");
      botao.setAttribute("disabled", "disabled");
    });
  });
});
