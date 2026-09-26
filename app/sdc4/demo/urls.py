from django.urls import path
from . import views

app_name = 'demo'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('narrative/', views.narrative, name='narrative'),
    path('explorer/', views.explorer, name='explorer'),
    path('run-query/', views.run_query, name='run-query'),
]
