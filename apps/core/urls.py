from django.urls import path

from apps.core import views

app_name = "core"

urlpatterns = [
    path("", views.raiz, name="raiz"),
    path("health/", views.health, name="health"),
    path("dashboard/", views.dashboard, name="dashboard"),
]
