from django import forms
from django.contrib.auth.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from apps.contas.models import Usuario
from apps.organizacoes.models import Organizacao, OrganizacaoUsuario, PerfilOrganizacao


class FormularioCriacaoUsuarioAdmin(UserCreationForm):
    """Admin cria usuário só com login + senha (+ organização opcional)."""

    organizacao = forms.ModelChoiceField(
        label="Organização",
        queryset=Organizacao.objects.filter(ativo=True),
        required=False,
        help_text="Se informada, vincula o usuário como advogado dessa organização.",
    )

    class Meta:
        model = Usuario
        fields = ("login",)

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.nome = usuario.nome or ""
        usuario.email = None
        if commit:
            usuario.save()
            org = self.cleaned_data.get("organizacao")
            if org:
                OrganizacaoUsuario.objects.get_or_create(
                    organizacao=org,
                    usuario=usuario,
                    defaults={"perfil": PerfilOrganizacao.ADVOGADO, "ativo": True},
                )
        return usuario


class FormularioAlteracaoUsuarioAdmin(UserChangeForm):
    class Meta:
        model = Usuario
        fields = "__all__"


class FormularioSenhaUsuarioAdmin(AdminPasswordChangeForm):
    class Meta:
        model = Usuario
