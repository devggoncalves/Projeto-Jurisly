from __future__ import annotations

from apps.organizacoes.models import OrganizacaoUsuario, PerfilOrganizacao


def pode_gerenciar_usuarios(usuario) -> bool:
    """Staff/superuser ou perfil de administrador/proprietário na organização."""
    if not getattr(usuario, "is_authenticated", False):
        return False
    if usuario.is_staff or usuario.is_superuser:
        return True
    return OrganizacaoUsuario.objects.filter(
        usuario=usuario,
        ativo=True,
        organizacao__ativo=True,
        perfil__in=[PerfilOrganizacao.PROPRIETARIO, PerfilOrganizacao.ADMINISTRADOR],
    ).exists()
