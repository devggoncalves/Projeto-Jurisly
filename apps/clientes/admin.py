from django.contrib import admin

from apps.clientes.models import Cliente, Processo


class ProcessoInline(admin.TabularInline):
    model = Processo
    extra = 0
    fields = ("numero", "numero_mascarado", "tribunal", "ativo")


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "documento", "email", "advogado", "organizacao", "ativo")
    list_filter = ("ativo", "organizacao")
    search_fields = ("nome", "documento", "email")
    autocomplete_fields = ("organizacao", "advogado")
    inlines = [ProcessoInline]


@admin.register(Processo)
class ProcessoAdmin(admin.ModelAdmin):
    list_display = ("numero", "cliente", "tribunal", "advogado", "ativo")
    list_filter = ("ativo", "tribunal", "organizacao")
    search_fields = ("numero", "numero_mascarado", "cliente__nome")
    autocomplete_fields = ("organizacao", "cliente", "advogado")
