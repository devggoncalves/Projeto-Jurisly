from __future__ import annotations

from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from apps.advogados.models import UnidadeFederativa, normalizar_numero_oab, validar_numero_oab
from apps.contas.managers import normalizar_login
from apps.contas.models import Usuario


class FormularioLogin(AuthenticationForm):
    username = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(
            attrs={
                "placeholder": "Seu e-mail",
                "autocomplete": "username",
                "class": "campo-input",
                "inputmode": "email",
            }
        ),
    )
    password = forms.CharField(
        label="Senha",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Sua senha",
                "autocomplete": "current-password",
                "class": "campo-input",
            }
        ),
    )
    lembrar = forms.BooleanField(
        label="Lembrar de mim",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "checkbox-lembrar"}),
    )

    error_messages = {
        "invalid_login": ("Não foi possível entrar. Verifique seus dados e tente novamente."),
        "inactive": ("Não foi possível entrar. Verifique seus dados e tente novamente."),
    }

    def clean_username(self) -> str:
        return normalizar_login(self.cleaned_data.get("username", ""))


class FormularioPrimeiroAcesso(forms.Form):
    """1º login: nova senha + OAB (e-mail já definido pelo admin)."""

    nome_completo = forms.CharField(
        label="Nome completo",
        max_length=255,
        widget=forms.TextInput(
            attrs={"class": "campo-texto", "placeholder": "Nome como na OAB"}
        ),
    )
    nova_senha = forms.CharField(
        label="Nova senha",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"class": "campo-texto", "autocomplete": "new-password"}
        ),
    )
    confirmar_senha = forms.CharField(
        label="Confirmar nova senha",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"class": "campo-texto", "autocomplete": "new-password"}
        ),
    )
    numero_oab = forms.CharField(
        label="Número da OAB",
        max_length=16,
        widget=forms.TextInput(
            attrs={
                "class": "campo-texto",
                "placeholder": "Número OAB",
                "inputmode": "numeric",
            }
        ),
    )
    uf_oab = forms.ChoiceField(
        label="UF da OAB",
        choices=[("", "Selecione a UF")] + list(UnidadeFederativa.choices),
        widget=forms.Select(attrs={"class": "campo-select"}),
    )

    def __init__(self, *args, usuario: Usuario | None = None, **kwargs):
        self.usuario = usuario
        super().__init__(*args, **kwargs)

    def clean_numero_oab(self):
        numero = normalizar_numero_oab(self.cleaned_data["numero_oab"])
        validar_numero_oab(numero)
        return numero

    def clean(self):
        cleaned = super().clean()
        senha = cleaned.get("nova_senha")
        confirmacao = cleaned.get("confirmar_senha")
        if senha and confirmacao and senha != confirmacao:
            self.add_error("confirmar_senha", "As senhas não coincidem.")
        if senha:
            validate_password(senha, user=self.usuario)
        return cleaned


# Compatibilidade com import antigo
FormularioCompletarCadastro = FormularioPrimeiroAcesso


class FormularioRecuperacaoSenha(PasswordResetForm):
    email = forms.EmailField(
        label="E-mail",
        max_length=254,
        widget=forms.EmailInput(
            attrs={
                "placeholder": "Seu e-mail",
                "autocomplete": "email",
                "class": "campo-input",
            }
        ),
    )

    def get_users(self, email: str):
        email_normalizado = Usuario.objects.normalizar_email(email)
        return Usuario.objects.filter(email__iexact=email_normalizado, ativo=True)


class FormularioNovaSenha(SetPasswordForm):
    new_password1 = forms.CharField(
        label="Nova senha",
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Nova senha",
                "autocomplete": "new-password",
                "class": "campo-input",
            }
        ),
        strip=False,
    )
    new_password2 = forms.CharField(
        label="Confirmar nova senha",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Confirme a nova senha",
                "autocomplete": "new-password",
                "class": "campo-input",
            }
        ),
    )

    def clean_new_password2(self):
        senha1 = self.cleaned_data.get("new_password1")
        senha2 = self.cleaned_data.get("new_password2")
        if senha1 and senha2 and senha1 != senha2:
            raise ValidationError("As senhas não coincidem.", code="password_mismatch")
        return senha2
