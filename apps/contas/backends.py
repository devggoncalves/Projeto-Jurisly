from __future__ import annotations

from django.contrib.auth.backends import ModelBackend

from apps.contas.managers import normalizar_login
from apps.contas.models import Usuario


class BackendAutenticacaoEmail(ModelBackend):
    """Autenticação por login (ou e-mail legado) + senha."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        identificador = kwargs.get("login") or kwargs.get("email") or username
        if identificador is None or password is None:
            return None

        identificador = normalizar_login(str(identificador))
        usuario = (
            Usuario.objects.filter(login=identificador).first()
            or Usuario.objects.filter(email=identificador).first()
        )
        if usuario is None:
            Usuario().set_password(password)
            return None

        if usuario.check_password(password) and self.user_can_authenticate(usuario):
            return usuario
        return None

    def user_can_authenticate(self, user) -> bool:
        return bool(getattr(user, "ativo", False))
