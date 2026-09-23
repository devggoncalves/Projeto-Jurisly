from django.urls import path

from apps.contas import views

app_name = "contas"

urlpatterns = [
    path("login/", views.ViewLogin.as_view(), name="login"),
    path("logout/", views.ViewLogout.as_view(), name="logout"),
    path("completar-cadastro/", views.completar_cadastro, name="completar_cadastro"),
    path("usuarios/", views.lista_usuarios, name="lista_usuarios"),
    path("usuarios/novo/", views.novo_usuario, name="novo_usuario"),
    path(
        "usuarios/<uuid:usuario_id>/acao/",
        views.acao_usuario,
        name="acao_usuario",
    ),
    path("esqueci-minha-senha/", views.ViewEsqueciSenha.as_view(), name="esqueci_senha"),
    path(
        "esqueci-minha-senha/enviado/",
        views.ViewRecuperacaoEnviada.as_view(),
        name="recuperacao_enviada",
    ),
    path(
        "redefinir-senha/<uidb64>/<token>/",
        views.ViewRedefinirSenha.as_view(),
        name="redefinir_senha",
    ),
    path(
        "redefinir-senha/concluido/",
        views.ViewSenhaRedefinida.as_view(),
        name="senha_redefinida",
    ),
]
