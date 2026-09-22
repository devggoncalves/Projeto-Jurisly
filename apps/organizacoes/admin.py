from django.contrib import admin

from apps.organizacoes.models import Organizacao, OrganizacaoUsuario


@admin.register(Organizacao)
class OrganizacaoAdmin(admin.ModelAdmin):
    list_display = ("nome", "slug", "ativo", "data_criacao")
    list_filter = ("ativo",)
    search_fields = ("nome", "slug")
    prepopulated_fields = {"slug": ("nome",)}
    readonly_fields = ("id", "data_criacao", "data_atualizacao")


@admin.register(OrganizacaoUsuario)
class OrganizacaoUsuarioAdmin(admin.ModelAdmin):
    list_display = ("organizacao", "usuario", "perfil", "ativo", "data_criacao")
    list_filter = ("perfil", "ativo")
    search_fields = ("organizacao__nome", "usuario__email", "usuario__nome")
    autocomplete_fields = ("organizacao", "usuario")
    readonly_fields = ("id", "data_criacao", "data_atualizacao")
