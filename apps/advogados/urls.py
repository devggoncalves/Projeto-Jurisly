from django.urls import path

from apps.advogados import views

app_name = "advogados"

urlpatterns = [
    path("meus-dados/", views.meus_dados, name="meus_dados"),
]
