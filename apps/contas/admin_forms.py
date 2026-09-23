from django import forms
from django.contrib.auth.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from django.contrib.auth.password_validation import validate_password

from apps.contas.managers import normalizar_login
from apps.contas.models import Usuario
from apps.organizacoes.models import Organizacao, OrganizacaoUsuario, PerfilOrganizacao


class FormularioCriacaoUsuarioAdmin(UserCreationForm):
    """Admin cria advogado com e-mail + senha (+ organização)."""

    email = forms.EmailField(
        label="E-mail",
        help_text="Será o login do advogado. No primeiro acesso ele troca a senha e cadastra a OAB.",
    )
    organizacao = forms.ModelChoiceField(
        label="Organização",
        queryset=Organizacao.objects.filter(ativo=True),
        required=True,
        help_text="Obrigaória para vincular o advogado ao escritório.",
    )

    class Meta:
        model = Usuario
        fields = ("email",)

    def clean_email(self):
        email = Usuario.objects.normalizar_email(self.cleaned_data["email"])
        login = normalizar_login(email)
        if Usuario.objects.filter(email=email).exists() or Usuario.objects.filter(login=login).exists():
            raise forms.ValidationError("Já existe um usuário com este e-mail.")
        return email

    def save(self, commit=True):
        usuario = super().save(commit=False)
        email = self.cleaned_data["email"]
        usuario.login = normalizar_login(email)
        usuario.email = email
        usuario.nome = ""
        usuario.deve_alterar_senha = True
        usuario.is_staff = False
        usuario.is_superuser = False
        if commit:
            usuario.save()
            OrganizacaoUsuario.objects.get_or_create(
                organizacao=self.cleaned_data["organizacao"],
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


class FormularioNovoAdvogadoApp(forms.Form):
    """Formulário no app (menu Usuários) para o admin criar advogado."""

    email = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(
            attrs={"class": "campo-texto", "placeholder": "advogado@escritorio.com"}
        ),
    )
    senha = forms.CharField(
        label="Senha provisória",
        widget=forms.PasswordInput(attrs={"class": "campo-texto", "autocomplete": "new-password"}),
        strip=False,
    )
    senha_confirmacao = forms.CharField(
        label="Confirmar senha",
        widget=forms.PasswordInput(attrs={"class": "campo-texto", "autocomplete": "new-password"}),
        strip=False,
    )
    organizacao = forms.ModelChoiceField(
        label="Organização",
        queryset=Organizacao.objects.filter(ativo=True),
        widget=forms.Select(attrs={"class": "campo-select"}),
    )

    def __init__(self, *args, organizacoes_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        if organizacoes_queryset is not None:
            self.fields["organizacao"].queryset = organizacoes_queryset

    def clean_email(self):
        email = Usuario.objects.normalizar_email(self.cleaned_data["email"])
        login = normalizar_login(email)
        if Usuario.objects.filter(email=email).exists() or Usuario.objects.filter(login=login).exists():
            raise forms.ValidationError("Já existe um usuário com este e-mail.")
        return email

    def clean(self):
        cleaned = super().clean()
        senha = cleaned.get("senha")
        confirmacao = cleaned.get("senha_confirmacao")
        if senha and confirmacao and senha != confirmacao:
            self.add_error("senha_confirmacao", "As senhas não coincidem.")
        if senha:
            validate_password(senha)
        return cleaned
