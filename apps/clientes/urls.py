from django.urls import path

from apps.clientes import views

app_name = "clientes"

urlpatterns = [
    path("clientes/", views.lista_clientes, name="lista"),
    path("clientes/novo/", views.novo_cliente, name="novo"),
    path("clientes/<uuid:cliente_id>/editar/", views.editar_cliente, name="editar"),
    path("clientes/processos/", views.lista_processos, name="processos"),
    path("clientes/processos/novo/", views.novo_processo, name="novo_processo"),
]
