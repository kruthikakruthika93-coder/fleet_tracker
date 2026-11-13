from django.contrib import admin
from .models import Vehicle, VehicleAssignment, MileageLog


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('registration_number', 'make', 'model', 'status', 'current_odometer', 'insurance_expiry')
    list_filter = ('status', 'fuel_type')
    search_fields = ('registration_number', 'make', 'model')


@admin.register(VehicleAssignment)
class VehicleAssignmentAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'driver', 'start_date', 'end_date')
    list_filter = ('vehicle', 'driver')


@admin.register(MileageLog)
class MileageLogAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'driver', 'date', 'odometer_reading')
    list_filter = ('vehicle', 'driver')