from __future__ import annotations

from django import forms

from apps.clientes.models import Cliente, Processo, normalizar_documento


class FormularioCliente(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ("nome", "documento", "email", "telefone", "observacoes", "ativo")
        widgets = {
            "nome": forms.TextInput(attrs={"class": "campo-texto", "placeholder": "Nome do cliente"}),
            "documento": forms.TextInput(
                attrs={"class": "campo-texto", "placeholder": "CPF ou CNPJ"}
            ),
            "email": forms.EmailInput(attrs={"class": "campo-texto", "placeholder": "E-mail"}),
            "telefone": forms.TextInput(
                attrs={"class": "campo-texto", "placeholder": "(11) 99999-9999"}
            ),
            "observacoes": forms.Textarea(
                attrs={"class": "campo-texto", "rows": 3, "placeholder": "Observações"}
            ),
            "ativo": forms.CheckboxInput(attrs={"class": "campo-check"}),
        }

    def clean_documento(self):
        return normalizar_documento(self.cleaned_data.get("documento", ""))


class FormularioProcesso(forms.ModelForm):
    class Meta:
        model = Processo
        fields = (
            "cliente",
            "numero",
            "numero_mascarado",
            "tribunal",
            "classe",
            "assunto",
            "ativo",
        )
        widgets = {
            "cliente": forms.Select(attrs={"class": "campo-select"}),
            "numero": forms.TextInput(
                attrs={"class": "campo-texto", "placeholder": "Número CNJ (só dígitos)"}
            ),
            "numero_mascarado": forms.TextInput(
                attrs={"class": "campo-texto", "placeholder": "0000000-00.0000.0.00.0000"}
            ),
            "tribunal": forms.TextInput(attrs={"class": "campo-texto", "placeholder": "Ex.: TJSP"}),
            "classe": forms.TextInput(attrs={"class": "campo-texto"}),
            "assunto": forms.TextInput(attrs={"class": "campo-texto"}),
            "ativo": forms.CheckboxInput(attrs={"class": "campo-check"}),
        }

    def __init__(self, *args, advogado=None, **kwargs):
        super().__init__(*args, **kwargs)
        if advogado is not None:
            self.fields["cliente"].queryset = Cliente.objects.filter(
                advogado=advogado, ativo=True
            ).order_by("nome")
