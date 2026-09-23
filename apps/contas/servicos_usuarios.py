from __future__ import annotations

import re
import unicodedata

from django.utils import timezone

from apps.contas.models import Usuario
from apps.organizacoes.services import organizacoes_do_usuario


def senha_padrao_usuario(usuario: Usuario) -> str:
    """
    Senha padrão: prefixo do nome (3 letras) + ano atual + #.
    Ex.: nome "Gabriel Souza" → Gab2026#
    """
    base = (usuario.nome or "").strip()
    if not base:
        base = (usuario.email or usuario.login or "Usr").split("@", 1)[0]
    primeiro = base.split()[0] if base else "Usr"
    sem_acento = "".join(
        ch for ch in unicodedata.normalize("NFKD", primeiro) if not unicodedata.combining(ch)
    )
    prefixo = re.sub(r"[^A-Za-z0-9]", "", sem_acento)[:3]
    if not prefixo:
        prefixo = "Usr"
    prefixo = prefixo[0].upper() + prefixo[1:].lower()
    return f"{prefixo}{timezone.now().year}#"


def usuarios_gerenciaveis_por(admin_user):
    """Queryset de usuários que o admin pode gerenciar."""
    orgs = organizacoes_do_usuario(admin_user)
    if admin_user.is_staff or admin_user.is_superuser:
        if orgs.exists():
            return (
                Usuario.objects.filter(vinculos_organizacao__organizacao__in=orgs)
                .distinct()
                .order_by("login")
            )
        return Usuario.objects.filter(is_staff=False).order_by("login")
    return (
        Usuario.objects.filter(vinculos_organizacao__organizacao__in=orgs)
        .distinct()
        .order_by("login")
    )


def pode_atuar_sobre(admin_user, alvo: Usuario) -> bool:
    if alvo.pk == admin_user.pk:
        return False
    if alvo.is_superuser and not admin_user.is_superuser:
        return False
    return usuarios_gerenciaveis_por(admin_user).filter(pk=alvo.pk).exists()
