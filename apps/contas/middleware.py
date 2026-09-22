from __future__ import annotations

from django.shortcuts import redirect
from django.urls import reverse


class MiddlewareCadastroObrigatorio:
    """
    Bloqueia o uso do app até o usuário informar e-mail e OAB.
    Admin/staff e rotas públicas ficam liberados.
    """

    PREFIXOS_LIVRES = (
        "/login/",
        "/logout/",
        "/completar-cadastro/",
        "/esqueci-minha-senha/",
        "/redefinir-senha/",
        "/admin/",
        "/static/",
        "/health/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        usuario = getattr(request, "user", None)
        if (
            usuario is not None
            and getattr(usuario, "is_authenticated", False)
            and getattr(usuario, "precisa_completar_cadastro", False)
        ):
            path = request.path
            livre = path == "/" or any(path.startswith(p) for p in self.PREFIXOS_LIVRES)
            if not livre:
                return redirect(reverse("contas:completar_cadastro"))
        return self.get_response(request)
