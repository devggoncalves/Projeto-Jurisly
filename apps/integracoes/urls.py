from django.urls import path

from apps.integracoes import views, views_comunicacoes

app_name = "integracoes"

urlpatterns = [
    path("consultas/djen/", views.consultas_djen, name="consultas_djen"),
    path(
        "comunicacoes/",
        views_comunicacoes.lista_comunicacoes,
        name="lista_comunicacoes",
    ),
    path(
        "comunicacoes/<uuid:vinculo_id>/",
        views_comunicacoes.detalhe_comunicacao,
        name="detalhe_comunicacao",
    ),
    path(
        "comunicacoes/sincronizar/",
        views_comunicacoes.sincronizar_djen,
        name="sincronizar_djen",
    ),
]
