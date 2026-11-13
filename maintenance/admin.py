from django.contrib import admin
from .models import MaintenanceSchedule, MaintenanceRecord, IssueReport


@admin.register(MaintenanceSchedule)
class MaintenanceScheduleAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'service_type', 'next_due_km', 'next_due_date')
    list_filter = ('service_type', 'vehicle')


@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'service_date', 'odometer', 'cost', 'status')
    list_filter = ('status', 'vehicle')


@admin.register(IssueReport)
class IssueReportAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'driver', 'description', 'status', 'created_at')
    list_filter = ('status', 'vehicle')