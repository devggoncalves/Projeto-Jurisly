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
    list_display = (
        "login",
        "email",
        "nome",
        "deve_alterar_senha",
        "ativo",
        "is_staff",
        "ultimo_acesso",
    )
    list_filter = ("ativo", "deve_alterar_senha", "is_staff", "is_superuser")
    search_fields = ("login", "email", "nome", "sobrenome")
    readonly_fields = ("id", "data_criacao", "data_atualizacao", "ultimo_acesso", "last_login")

    fieldsets = (
        (None, {"fields": ("login", "password")}),
        (_("Dados pessoais"), {"fields": ("email", "nome", "sobrenome")}),
        (
            _("Acesso"),
            {"fields": ("deve_alterar_senha", "ativo", "is_staff", "is_superuser")},
        ),
        (_("Permissões"), {"fields": ("groups", "user_permissions")}),
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
                "fields": ("email", "password1", "password2", "organizacao", "ativo"),
                "description": (
                    "Crie o advogado com e-mail e senha provisória. "
                    "No primeiro login ele será obrigado a alterar a senha e cadastrar a OAB."
                ),
            },
        ),
    )

    filter_horizontal = ("groups", "user_permissions")
