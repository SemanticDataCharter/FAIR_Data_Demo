"""URL configuration for demo landing page."""

from django.urls import path

from . import views

app_name = "demo"

urlpatterns = [
    path("", views.landing, name="landing"),
    path("sparql/", views.sparql_query, name="sparql"),
]
