from django.contrib import admin

from apps.auditoria.models import LogAuditoria


@admin.register(LogAuditoria)
class LogAuditoriaAdmin(admin.ModelAdmin):
    list_display = ("acao", "usuario", "organizacao", "endereco_ip", "data_criacao")
    list_filter = ("acao", "data_criacao")
    search_fields = ("acao", "usuario__email", "endereco_ip", "tipo_entidade")
    readonly_fields = (
        "id",
        "organizacao",
        "usuario",
        "acao",
        "tipo_entidade",
        "entidade_id",
        "metadados",
        "endereco_ip",
        "agente_usuario",
        "data_criacao",
    )
    ordering = ("-data_criacao",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
