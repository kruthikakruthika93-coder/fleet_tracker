from django import forms
from django.utils import timezone

from .models import Vehicle, VehicleAssignment, MileageLog


class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = [
            'registration_number', 'make', 'model', 'year', 'fuel_type',
            'current_odometer', 'status', 'insurance_provider',
            'insurance_policy_number', 'insurance_expiry',
        ]
        widgets = {
            'insurance_expiry': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = VehicleAssignment
        fields = ['vehicle', 'driver', 'start_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'

    def clean(self):
        cleaned = super().clean()
        vehicle = cleaned.get('vehicle')
        driver = cleaned.get('driver')
        active = VehicleAssignment.objects.filter(end_date__isnull=True)
        if vehicle and active.filter(vehicle=vehicle).exists():
            raise forms.ValidationError('This vehicle already has an active driver. End that assignment first.')
        if driver and active.filter(driver=driver).exists():
            raise forms.ValidationError('This driver already has an active vehicle. End that assignment first.')
        return cleaned


class MileageForm(forms.ModelForm):
    class Meta:
        model = MileageLog
        fields = ['date', 'odometer_reading', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, vehicle=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.vehicle = vehicle
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_odometer_reading(self):
        reading = self.cleaned_data['odometer_reading']
        if self.vehicle and reading < self.vehicle.current_odometer:
            raise forms.ValidationError(
                f'Reading cannot be lower than the current odometer ({self.vehicle.current_odometer} km).'
            )
        return reading

    def clean_date(self):
        date = self.cleaned_data['date']
        if date > timezone.localdate():
            raise forms.ValidationError('Date cannot be in the future.')
        return date