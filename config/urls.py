from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    path("", include("apps.contas.urls")),
    path("", include("apps.advogados.urls")),
    path("", include("apps.integracoes.urls")),
    path("", include("apps.clientes.urls")),
]
