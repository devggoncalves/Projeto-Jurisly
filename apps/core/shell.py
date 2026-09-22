from __future__ import annotations

from apps.organizacoes.models import OrganizacaoUsuario, PerfilOrganizacao
from apps.organizacoes.services import organizacoes_do_usuario


def iniciais_usuario(usuario) -> str:
    nome = (usuario.nome or "").strip()
    sobrenome = (usuario.sobrenome or "").strip()
    if nome and sobrenome:
        return f"{nome[0]}{sobrenome[0]}".upper()
    if nome:
        partes = nome.split()
        if len(partes) >= 2:
            return f"{partes[0][0]}{partes[1][0]}".upper()
        return nome[:2].upper()
    return (usuario.login or usuario.email or "U")[:2].upper()


def perfil_label_usuario(usuario) -> str:
    vinculo = (
        OrganizacaoUsuario.objects.filter(usuario=usuario, ativo=True, organizacao__ativo=True)
        .select_related("organizacao")
        .order_by("data_criacao")
        .first()
    )
    if vinculo is not None:
        return vinculo.get_perfil_display()
    if usuario.is_superuser or usuario.is_staff:
        return PerfilOrganizacao.ADMINISTRADOR.label
    return "Usuário"


def contexto_shell(usuario) -> dict:
    nao_visualizados = 0
    try:
        advogado = getattr(usuario, "advogado", None)
        if advogado is not None:
            from apps.integracoes.models import ComunicacaoAdvogado

            nao_visualizados = ComunicacaoAdvogado.objects.filter(
                advogado=advogado, visualizado=False
            ).count()
    except Exception:  # noqa: BLE001
        nao_visualizados = 0

    return {
        "usuario": usuario,
        "nome_exibicao": usuario.get_full_name() or usuario.login,
        "perfil_label": perfil_label_usuario(usuario),
        "iniciais": iniciais_usuario(usuario),
        "organizacoes": organizacoes_do_usuario(usuario),
        "nao_visualizados": nao_visualizados,
    }


def organizacao_padrao(usuario):
    return organizacoes_do_usuario(usuario).order_by("nome").first()
