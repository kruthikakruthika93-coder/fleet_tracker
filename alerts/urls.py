from django.urls import path
from . import views

urlpatterns = [
    path('', views.alert_list, name='alert_list'),
    path('read-all/', views.alert_read_all, name='alert_read_all'),
    path('<int:pk>/read/', views.alert_read, name='alert_read'),
]