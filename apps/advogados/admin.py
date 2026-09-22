from django.contrib import admin

from apps.advogados.models import Advogado, InscricaoOab


class InscricaoOabInline(admin.TabularInline):
    model = InscricaoOab
    extra = 1
    fields = ("numero", "uf", "tipo", "principal", "ativo")


@admin.register(Advogado)
class AdvogadoAdmin(admin.ModelAdmin):
    list_display = (
        "nome_completo",
        "email",
        "cpf",
        "usuario",
        "organizacao",
        "ativo",
    )
    list_filter = ("ativo", "organizacao")
    search_fields = ("nome_completo", "nome_consulta", "email", "cpf", "usuario__email")
    autocomplete_fields = ("organizacao", "usuario")
    readonly_fields = ("id", "data_criacao", "data_atualizacao")
    inlines = [InscricaoOabInline]


@admin.register(InscricaoOab)
class InscricaoOabAdmin(admin.ModelAdmin):
    list_display = ("numero", "uf", "tipo", "principal", "ativo", "advogado")
    list_filter = ("uf", "tipo", "principal", "ativo")
    search_fields = ("numero", "advogado__nome_completo")
    autocomplete_fields = ("advogado",)
    readonly_fields = ("id", "data_criacao", "data_atualizacao")
