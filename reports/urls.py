from django.urls import path
from . import views

urlpatterns = [
    path('', views.report_summary, name='report_summary'),
    path('csv/', views.report_csv, name='report_csv'),
]