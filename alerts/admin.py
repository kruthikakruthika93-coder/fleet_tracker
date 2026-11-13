from django.contrib import admin
from .models import Alert


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('message', 'alert_type', 'vehicle', 'due_date', 'is_read')
    list_filter = ('alert_type', 'is_read')