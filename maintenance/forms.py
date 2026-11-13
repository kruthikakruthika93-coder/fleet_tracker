from django import forms
from django.utils import timezone

from .models import MaintenanceSchedule, MaintenanceRecord, IssueReport


def style_fields(form):
    for field in form.fields.values():
        if isinstance(field.widget, forms.Select):
            field.widget.attrs['class'] = 'form-select'
        else:
            field.widget.attrs['class'] = 'form-control'


class ScheduleForm(forms.ModelForm):
    class Meta:
        model = MaintenanceSchedule
        fields = ['vehicle', 'service_type', 'interval_km', 'interval_days',
                  'last_service_km', 'last_service_date']
        widgets = {
            'last_service_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('interval_km') and not cleaned.get('interval_days'):
            raise forms.ValidationError('Enter an interval in km, in days, or both.')
        return cleaned


class RecordForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRecord
        fields = ['vehicle', 'schedule', 'service_date', 'odometer',
                  'cost', 'workshop', 'notes']
        widgets = {
            'service_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, vehicle=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fixed_vehicle = vehicle
        if vehicle:
            del self.fields['vehicle']
            self.fields['schedule'].queryset = MaintenanceSchedule.objects.filter(vehicle=vehicle)
        style_fields(self)

    def clean(self):
        cleaned = super().clean()
        vehicle = self.fixed_vehicle or cleaned.get('vehicle')
        schedule = cleaned.get('schedule')
        if vehicle and schedule and schedule.vehicle_id != vehicle.id:
            raise forms.ValidationError('That schedule belongs to a different vehicle.')
        return cleaned

    def clean_service_date(self):
        date = self.cleaned_data['service_date']
        if date > timezone.localdate():
            raise forms.ValidationError('Date cannot be in the future.')
        return date


class IssueForm(forms.ModelForm):
    class Meta:
        model = IssueReport
        fields = ['description']
        widgets = {'description': forms.Textarea(attrs={'rows': 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)