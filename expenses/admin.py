from django.contrib import admin
from .models import FuelLog, RepairExpense


@admin.register(FuelLog)
class FuelLogAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'driver', 'date', 'litres', 'total_cost', 'price_per_litre')
    list_filter = ('vehicle', 'driver')


@admin.register(RepairExpense)
class RepairExpenseAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'date', 'description', 'cost', 'workshop')
    list_filter = ('vehicle',)