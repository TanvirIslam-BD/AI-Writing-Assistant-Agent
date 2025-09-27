from django.urls import path
from . import views

app_name = 'writing_assistant'

urlpatterns = [
    path('', views.index, name='index'),
    path('improve/', views.improve_text, name='improve_text'),
    path('analyze/', views.analyze_text, name='analyze_text'),
    path('history/', views.history, name='history'),
    path('stats/', views.stats, name='stats'),
]