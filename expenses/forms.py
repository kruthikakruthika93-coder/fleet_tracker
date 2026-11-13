from django import forms
from django.utils import timezone

from .models import FuelLog, RepairExpense


def style_fields(form):
    for field in form.fields.values():
        if isinstance(field.widget, forms.Select):
            field.widget.attrs['class'] = 'form-select'
        else:
            field.widget.attrs['class'] = 'form-control'


class FuelForm(forms.ModelForm):
    class Meta:
        model = FuelLog
        fields = ['vehicle', 'driver', 'date', 'litres', 'total_cost', 'odometer']
        widgets = {'date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')}

    def __init__(self, *args, fixed=False, **kwargs):
        super().__init__(*args, **kwargs)
        if fixed:
            del self.fields['vehicle']
            del self.fields['driver']
        style_fields(self)

    def clean_litres(self):
        value = self.cleaned_data['litres']
        if value <= 0:
            raise forms.ValidationError('Litres must be more than zero.')
        return value

    def clean_total_cost(self):
        value = self.cleaned_data['total_cost']
        if value <= 0:
            raise forms.ValidationError('Cost must be more than zero.')
        return value

    def clean_date(self):
        value = self.cleaned_data['date']
        if value > timezone.localdate():
            raise forms.ValidationError('Date cannot be in the future.')
        return value


class RepairForm(forms.ModelForm):
    class Meta:
        model = RepairExpense
        fields = ['vehicle', 'date', 'description', 'cost', 'workshop']
        widgets = {'date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)

    def clean_cost(self):
        value = self.cleaned_data['cost']
        if value <= 0:
            raise forms.ValidationError('Cost must be more than zero.')
        return value

    def clean_date(self):
        value = self.cleaned_data['date']
        if value > timezone.localdate():
            raise forms.ValidationError('Date cannot be in the future.')
        return value