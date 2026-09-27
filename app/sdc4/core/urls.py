"""
URL configuration for core app.
"""
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('<str:doc_name>/', views.render_markdown, name='docs'),
]
