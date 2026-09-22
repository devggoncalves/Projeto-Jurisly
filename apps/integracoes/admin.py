from django.contrib import admin

from apps.integracoes.models import (
    ComunicacaoAdvogado,
    ComunicacaoJudicial,
    SincronizacaoIntegracao,
)


class ComunicacaoAdvogadoInline(admin.TabularInline):
    model = ComunicacaoAdvogado
    extra = 0
    autocomplete_fields = ("advogado", "inscricao_oab")
    readonly_fields = ("id", "data_criacao", "data_atualizacao")


@admin.register(ComunicacaoJudicial)
class ComunicacaoJudicialAdmin(admin.ModelAdmin):
    list_display = (
        "identificador_externo",
        "fonte",
        "tribunal",
        "tipo_comunicacao",
        "numero_processo",
        "data_disponibilizacao",
        "organizacao",
    )
    list_filter = ("fonte", "tribunal", "tipo_comunicacao", "organizacao")
    search_fields = ("hash", "identificador_externo", "numero_processo", "texto")
    readonly_fields = ("id", "data_criacao", "data_atualizacao", "dados_originais")
    autocomplete_fields = ("organizacao",)
    inlines = [ComunicacaoAdvogadoInline]


@admin.register(ComunicacaoAdvogado)
class ComunicacaoAdvogadoAdmin(admin.ModelAdmin):
    list_display = (
        "comunicacao",
        "advogado",
        "status",
        "numero_oab_origem",
        "uf_oab_origem",
        "organizacao",
    )
    list_filter = ("status", "organizacao")
    search_fields = (
        "nome_advogado_origem",
        "numero_oab_origem",
        "advogado__nome_completo",
    )
    autocomplete_fields = ("organizacao", "comunicacao", "advogado", "inscricao_oab")
    readonly_fields = ("id", "data_criacao", "data_atualizacao")


@admin.register(SincronizacaoIntegracao)
class SincronizacaoIntegracaoAdmin(admin.ModelAdmin):
    list_display = (
        "fonte",
        "status",
        "total_encontrado",
        "total_novos",
        "iniciado_em",
        "organizacao",
    )
    list_filter = ("fonte", "status", "organizacao")
    readonly_fields = (
        "id",
        "parametros",
        "detalhes",
        "data_criacao",
        "iniciado_em",
        "finalizado_em",
    )
    autocomplete_fields = ("organizacao",)
