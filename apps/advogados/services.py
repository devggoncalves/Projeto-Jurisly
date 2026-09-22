from __future__ import annotations

from apps.advogados.models import Advogado
from apps.core.shell import organizacao_padrao


def obter_perfil_advogado(usuario) -> Advogado | None:
    return (
        Advogado.objects.filter(usuario=usuario)
        .select_related("organizacao")
        .prefetch_related("inscricoes")
        .first()
    )


def obter_ou_preparar_perfil(usuario) -> Advogado | None:
    """
    Retorna o perfil do usuário.
    Se ainda não existir, prepara instância em memória (não salva)
    com organização e dados básicos do usuário.
    """
    existente = obter_perfil_advogado(usuario)
    if existente is not None:
        return existente

    organizacao = organizacao_padrao(usuario)
    if organizacao is None:
        return None

    nome_completo = usuario.get_full_name() or usuario.nome or ""
    return Advogado(
        usuario=usuario,
        organizacao=organizacao,
        nome_completo=nome_completo,
        email=usuario.email or "",
    )
