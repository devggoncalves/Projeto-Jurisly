from __future__ import annotations

from django import forms
from django.forms import inlineformset_factory

from apps.advogados.models import (
    Advogado,
    InscricaoOab,
    TipoInscricaoOab,
    UnidadeFederativa,
    normalizar_cpf,
    normalizar_numero_oab,
)


class FormularioMeusDadosAdvogado(forms.ModelForm):
    """Cadastro enriquecido com campos úteis às consultas DJEN."""

    class Meta:
        model = Advogado
        fields = (
            "nome_completo",
            "nome_consulta",
            "cpf",
            "email",
            "telefone",
        )
        widgets = {
            "nome_completo": forms.TextInput(
                attrs={"class": "campo-texto", "placeholder": "Nome completo como na OAB"}
            ),
            "nome_consulta": forms.TextInput(
                attrs={
                    "class": "campo-texto",
                    "placeholder": "Opcional — filtro nomeAdvogado no DJEN",
                }
            ),
            "cpf": forms.TextInput(
                attrs={"class": "campo-texto", "placeholder": "000.000.000-00"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "campo-texto", "placeholder": "E-mail profissional"}
            ),
            "telefone": forms.TextInput(
                attrs={"class": "campo-texto", "placeholder": "(11) 99999-9999"}
            ),
        }
        labels = {
            "nome_completo": "Nome completo",
            "nome_consulta": "Nome para consulta DJEN",
            "cpf": "CPF",
            "email": "E-mail",
            "telefone": "Telefone",
        }
        help_texts = {
            "nome_consulta": "Usado no parâmetro nomeAdvogado da API pública, se preenchido.",
            "cpf": "Armazenado no Jurisly (a API DJEN pública não filtra por CPF).",
        }

    def clean_cpf(self):
        return normalizar_cpf(self.cleaned_data.get("cpf", ""))

    def clean_nome_completo(self):
        return (self.cleaned_data.get("nome_completo") or "").strip()


class FormularioInscricaoOab(forms.ModelForm):
    class Meta:
        model = InscricaoOab
        fields = ("numero", "uf", "tipo", "principal", "ativo")
        widgets = {
            "numero": forms.TextInput(
                attrs={
                    "class": "campo-texto",
                    "placeholder": "Número OAB",
                    "inputmode": "numeric",
                }
            ),
            "uf": forms.Select(attrs={"class": "campo-select"}),
            "tipo": forms.Select(attrs={"class": "campo-select"}),
            "principal": forms.CheckboxInput(attrs={"class": "campo-check"}),
            "ativo": forms.CheckboxInput(attrs={"class": "campo-check"}),
        }
        labels = {
            "numero": "Número OAB",
            "uf": "UF",
            "tipo": "Tipo",
            "principal": "Principal",
            "ativo": "Ativa",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["uf"].choices = [("", "UF")] + list(UnidadeFederativa.choices)
        self.fields["tipo"].choices = list(TipoInscricaoOab.choices)
        self.fields["numero"].required = False
        self.fields["uf"].required = False

    def clean_numero(self):
        valor = self.cleaned_data.get("numero", "")
        if not valor:
            return ""
        return normalizar_numero_oab(valor)

    def clean(self):
        cleaned = super().clean()
        numero = cleaned.get("numero") or ""
        uf = cleaned.get("uf") or ""
        # Linha vazia = ignorar (formset)
        if not numero and not uf:
            return cleaned
        if not numero:
            self.add_error("numero", "Informe o número da OAB.")
        if not uf:
            self.add_error("uf", "Informe a UF.")
        return cleaned


InscricaoOabFormSet = inlineformset_factory(
    Advogado,
    InscricaoOab,
    form=FormularioInscricaoOab,
    extra=2,
    can_delete=True,
    min_num=1,
    validate_min=True,
)
