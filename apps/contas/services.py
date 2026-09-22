from __future__ import annotations

import logging

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.http import HttpRequest

from apps.auditoria.services import (
    registrar_login_falha,
    registrar_login_sucesso,
    registrar_logout,
)

logger = logging.getLogger(__name__)

MENSAGEM_LOGIN_FALHA = "Não foi possível entrar. Verifique seus dados e tente novamente."


class ServicoAutenticacao:
    """Orquestra autenticação, sessão e auditoria."""

    @staticmethod
    def autenticar(request: HttpRequest, login_id: str, senha: str, lembrar: bool = False):
        usuario = authenticate(request, login=login_id, password=senha)
        if usuario is None:
            registrar_login_falha(request, email=login_id)
            logger.info("Login inválido.")
            return None, MENSAGEM_LOGIN_FALHA

        login(request, usuario)
        ServicoAutenticacao.configurar_sessao(request, lembrar=lembrar)
        usuario.registrar_acesso()
        registrar_login_sucesso(request, usuario)
        logger.info("Login realizado com sucesso.")

        # Busca DJEN ao logar (não bloqueia o login se falhar)
        if not usuario.precisa_completar_cadastro:
            try:
                from apps.integracoes.djen.sincronizacao import sincronizar_advogado_do_usuario

                resultado = sincronizar_advogado_do_usuario(usuario)
                request.session["ultima_sync_djen"] = {
                    "ok": resultado.ok,
                    "novos": resultado.total_novos,
                    "mensagem": resultado.mensagem,
                }
            except Exception:  # noqa: BLE001
                logger.exception("Falha na sincronização DJEN pós-login.")

        return usuario, None

    @staticmethod
    def configurar_sessao(request: HttpRequest, *, lembrar: bool) -> None:
        if lembrar:
            request.session.set_expiry(settings.SESSION_COOKIE_AGE)
        else:
            request.session.set_expiry(0)
        request.session["lembrar_de_mim"] = lembrar

    @staticmethod
    def encerrar_sessao(request: HttpRequest) -> None:
        usuario = request.user if getattr(request.user, "is_authenticated", False) else None
        if usuario is not None:
            registrar_logout(request, usuario)
            logger.info("Logout realizado.")
        logout(request)
