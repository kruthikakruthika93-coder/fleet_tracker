from django.urls import path
from . import views

urlpatterns = [
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('driver/', views.driver_dashboard, name='driver_dashboard'),
]