from django.urls import path
from . import views

urlpatterns = [
    path('', views.maintenance_home, name='maintenance_home'),
    path('schedules/add/', views.schedule_create, name='schedule_create'),
    path('schedules/<int:pk>/delete/', views.schedule_delete, name='schedule_delete'),
    path('records/add/', views.record_create, name='record_create'),
    path('records/<int:pk>/approve/', views.record_approve, name='record_approve'),
    path('issues/<int:pk>/resolve/', views.issue_resolve, name='issue_resolve'),
    path('service/new/', views.driver_service, name='driver_service'),
    path('issue/new/', views.driver_issue, name='driver_issue'),
]