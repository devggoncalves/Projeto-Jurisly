from __future__ import annotations

from typing import Any
from uuid import UUID

from django.http import HttpRequest

from apps.auditoria.models import AcaoAuditoria, LogAuditoria

CAMPOS_SENSIVEIS = {
    "password",
    "senha",
    "token",
    "secret",
    "csrfmiddlewaretoken",
    "sessionid",
    "authorization",
}


def _sanitizar_metadados(metadados: dict[str, Any] | None) -> dict[str, Any]:
    if not metadados:
        return {}
    limpo: dict[str, Any] = {}
    for chave, valor in metadados.items():
        if str(chave).lower() in CAMPOS_SENSIVEIS:
            continue
        limpo[chave] = valor
    return limpo


def obter_ip_cliente(request: HttpRequest | None) -> str | None:
    if request is None:
        return None
    encaminhado = request.META.get("HTTP_X_FORWARDED_FOR")
    if encaminhado:
        return encaminhado.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def registrar_evento(
    *,
    acao: str,
    request: HttpRequest | None = None,
    usuario=None,
    organizacao=None,
    tipo_entidade: str = "",
    entidade_id: UUID | None = None,
    metadados: dict[str, Any] | None = None,
) -> LogAuditoria:
    """Persiste evento de auditoria sem dados sensíveis."""
    agente = ""
    if request is not None:
        agente = request.META.get("HTTP_USER_AGENT", "")[:1000]

    return LogAuditoria.objects.create(
        acao=acao,
        usuario=usuario,
        organizacao=organizacao,
        tipo_entidade=tipo_entidade,
        entidade_id=entidade_id,
        metadados=_sanitizar_metadados(metadados),
        endereco_ip=obter_ip_cliente(request),
        agente_usuario=agente,
    )


def registrar_login_sucesso(request: HttpRequest, usuario) -> LogAuditoria:
    return registrar_evento(
        acao=AcaoAuditoria.LOGIN_SUCESSO,
        request=request,
        usuario=usuario,
        tipo_entidade="usuario",
        entidade_id=usuario.id,
        metadados={"email": usuario.email},
    )


def registrar_login_falha(request: HttpRequest, email: str) -> LogAuditoria:
    return registrar_evento(
        acao=AcaoAuditoria.LOGIN_FALHA,
        request=request,
        tipo_entidade="usuario",
        metadados={"email": email},
    )


def registrar_logout(request: HttpRequest, usuario) -> LogAuditoria:
    return registrar_evento(
        acao=AcaoAuditoria.LOGOUT,
        request=request,
        usuario=usuario,
        tipo_entidade="usuario",
        entidade_id=getattr(usuario, "id", None),
        metadados={"email": getattr(usuario, "email", "")},
    )
