from __future__ import annotations

from datetime import date, timedelta

from django import forms

from apps.advogados.models import UnidadeFederativa


class FormularioConsultaDjen(forms.Form):
    """Formulário temporário para testar a API pública do DJEN."""

    numero_oab = forms.CharField(
        label="Número OAB",
        max_length=16,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "campo-texto", "placeholder": "Ex.: 496901", "inputmode": "numeric"}
        ),
    )
    uf_oab = forms.ChoiceField(
        label="UF OAB",
        required=False,
        choices=[("", "—")] + list(UnidadeFederativa.choices),
        widget=forms.Select(attrs={"class": "campo-select"}),
    )
    nome_advogado = forms.CharField(
        label="Nome do advogado (API)",
        max_length=255,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "campo-texto", "placeholder": "Filtro nomeAdvogado"}
        ),
    )
    nome_parte = forms.CharField(
        label="Nome da parte",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "campo-texto", "placeholder": "Filtro nomeParte"}),
    )
    numero_processo = forms.CharField(
        label="Número do processo",
        max_length=40,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "campo-texto", "placeholder": "CNJ sem máscara"}
        ),
    )
    sigla_tribunal = forms.CharField(
        label="Sigla do tribunal",
        max_length=16,
        required=False,
        widget=forms.TextInput(attrs={"class": "campo-texto", "placeholder": "Ex.: TJSP"}),
    )
    texto = forms.CharField(
        label="Texto contém",
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "campo-texto", "placeholder": "Busca no texto"}),
    )
    data_inicio = forms.DateField(
        label="Disponibilização (início)",
        required=True,
        widget=forms.DateInput(attrs={"class": "campo-texto", "type": "date"}),
    )
    data_fim = forms.DateField(
        label="Disponibilização (fim)",
        required=True,
        widget=forms.DateInput(attrs={"class": "campo-texto", "type": "date"}),
    )
    pagina = forms.IntegerField(
        label="Página",
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={"class": "campo-texto", "min": "1"}),
    )
    itens_por_pagina = forms.IntegerField(
        label="Itens por página",
        min_value=1,
        max_value=100,
        initial=20,
        widget=forms.NumberInput(attrs={"class": "campo-texto", "min": "1", "max": "100"}),
    )
    usar_perfil = forms.BooleanField(
        label="Preencher OAB/nome a partir do meu perfil",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "campo-check"}),
    )
    persistir = forms.BooleanField(
        label="Persistir resultados (status PENDENTE)",
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={"class": "campo-check"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            hoje = date.today()
            self.fields["data_fim"].initial = hoje
            self.fields["data_inicio"].initial = hoje - timedelta(days=7)

    def clean(self):
        cleaned = super().clean()
        inicio = cleaned.get("data_inicio")
        fim = cleaned.get("data_fim")
        if inicio and fim and inicio > fim:
            self.add_error("data_fim", "A data final deve ser igual ou posterior à inicial.")

        oab = (cleaned.get("numero_oab") or "").strip()
        uf = cleaned.get("uf_oab") or ""
        nome = (cleaned.get("nome_advogado") or "").strip()
        processo = (cleaned.get("numero_processo") or "").strip()
        usar_perfil = cleaned.get("usar_perfil")
        if not usar_perfil and not any([oab and uf, nome, processo]):
            raise forms.ValidationError(
                "Informe OAB+UF, nome do advogado, número do processo, "
                "ou marque para usar o perfil."
            )
        if oab:
            cleaned["numero_oab"] = "".join(ch for ch in oab if ch.isdigit() or ch in "-OoAa")
        return cleaned
