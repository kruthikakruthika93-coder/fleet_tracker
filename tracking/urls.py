from django.urls import path

from . import views

urlpatterns = [
    path('', views.tracking_map, name='tracking_map'),
    path('data/', views.tracking_data, name='tracking_data'),
    path('update/', views.location_update, name='location_update'),
    path('stop/', views.location_stop, name='location_stop'),
]