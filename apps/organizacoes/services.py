from __future__ import annotations

from apps.organizacoes.models import Organizacao, OrganizacaoUsuario


def organizacoes_do_usuario(usuario, *, apenas_ativas: bool = True):
    """Retorna organizações vinculadas ao usuário autenticado."""
    if not getattr(usuario, "is_authenticated", False):
        return Organizacao.objects.none()

    qs = Organizacao.objects.filter(
        membros__usuario=usuario,
        membros__ativo=True,
    )
    if apenas_ativas:
        qs = qs.filter(ativo=True)
    return qs.distinct()


def usuario_pertence_a_organizacao(usuario, organizacao_id) -> bool:
    if not getattr(usuario, "is_authenticated", False):
        return False
    return OrganizacaoUsuario.objects.filter(
        usuario=usuario,
        organizacao_id=organizacao_id,
        ativo=True,
        organizacao__ativo=True,
    ).exists()


def filtrar_por_organizacoes_do_usuario(queryset, usuario, campo: str = "organizacao_id"):
    """Aplica filtro multi-tenant a partir dos vínculos do usuário."""
    ids = organizacoes_do_usuario(usuario).values_list("id", flat=True)
    return queryset.filter(**{f"{campo}__in": ids})
