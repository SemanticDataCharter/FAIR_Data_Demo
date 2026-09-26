from django.urls import path

from . import views

app_name = 'console'

urlpatterns = [
    path('', views.index, name='index'),
    path('question/', views.question, name='question'),
    path('instance/<str:ct_id>/<str:instance_id>/', views.instance, name='instance'),
    path('instance/<str:ct_id>/<str:instance_id>/pane/<str:pane>/', views.pane, name='pane'),
]
