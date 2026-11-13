from django.urls import path
from . import views

urlpatterns = [
    path('', views.expense_home, name='expense_home'),
    path('fuel/add/', views.fuel_create, name='fuel_create'),
    path('fuel/<int:pk>/delete/', views.fuel_delete, name='fuel_delete'),
    path('repair/add/', views.repair_create, name='repair_create'),
    path('repair/<int:pk>/delete/', views.repair_delete, name='repair_delete'),
    path('fuel/new/', views.driver_fuel, name='driver_fuel'),
]