from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from apps.contas.admin_forms import FormularioAlteracaoUsuarioAdmin, FormularioCriacaoUsuarioAdmin
from apps.contas.models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(DjangoUserAdmin):
    form = FormularioAlteracaoUsuarioAdmin
    add_form = FormularioCriacaoUsuarioAdmin
    ordering = ("login",)
    list_display = ("login", "email", "nome", "ativo", "is_staff", "ultimo_acesso")
    list_filter = ("ativo", "is_staff", "is_superuser")
    search_fields = ("login", "email", "nome", "sobrenome")
    readonly_fields = ("id", "data_criacao", "data_atualizacao", "ultimo_acesso", "last_login")

    fieldsets = (
        (None, {"fields": ("login", "password")}),
        (_("Dados pessoais"), {"fields": ("email", "nome", "sobrenome")}),
        (
            _("Permissões"),
            {"fields": ("ativo", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        (
            _("Datas"),
            {"fields": ("last_login", "ultimo_acesso", "data_criacao", "data_atualizacao", "id")},
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("login", "password1", "password2", "organizacao", "ativo"),
                "description": (
                    "Informe apenas login e senha. No primeiro acesso o usuário "
                    "deverá preencher e-mail e OAB."
                ),
            },
        ),
    )

    filter_horizontal = ("groups", "user_permissions")
