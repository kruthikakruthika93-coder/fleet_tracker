from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('vehicles/', include('vehicles.urls')),
    path('maintenance/', include('maintenance.urls')),
    path('alerts/', include('alerts.urls')),
    path('reports/', include('reports.urls')),
    path('expenses/', include('expenses.urls')),
    path('drivers/', include('drivers.urls')),
    path('tracking/', include('tracking.urls')),
]