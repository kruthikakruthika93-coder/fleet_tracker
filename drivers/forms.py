from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction

from .models import DriverProfile

User = get_user_model()


def style_fields(form):
    for field in form.fields.values():
        field.widget.attrs['class'] = 'form-control'


class DriverCreateForm(forms.Form):
    username = forms.CharField(max_length=150)
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)
    password = forms.CharField(widget=forms.PasswordInput, help_text='Minimum 8 characters, not too common.')
    phone = forms.CharField(max_length=15)
    license_number = forms.CharField(max_length=30)
    license_expiry = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)

    def clean_username(self):
        value = self.cleaned_data['username']
        if User.objects.filter(username__iexact=value).exists():
            raise forms.ValidationError('This username is already taken.')
        return value

    def clean_license_number(self):
        value = self.cleaned_data['license_number']
        if DriverProfile.objects.filter(license_number=value).exists():
            raise forms.ValidationError('A driver with this licence number already exists.')
        return value

    def clean_password(self):
        value = self.cleaned_data['password']
        validate_password(value)
        return value

    @transaction.atomic
    def save(self):
        d = self.cleaned_data
        user = User.objects.create_user(
            username=d['username'], password=d['password'],
            first_name=d['first_name'], last_name=d['last_name'],
            email=d['email'], role='DRIVER',
        )
        return DriverProfile.objects.create(
            user=user, phone=d['phone'],
            license_number=d['license_number'], license_expiry=d['license_expiry'],
        )


class DriverUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=False)

    field_order = ['first_name', 'last_name', 'email', 'phone', 'license_number', 'license_expiry']

    class Meta:
        model = DriverProfile
        fields = ['phone', 'license_number', 'license_expiry']
        widgets = {
            'license_expiry': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.instance.user
        self.initial.update(first_name=user.first_name, last_name=user.last_name, email=user.email)
        style_fields(self)

    @transaction.atomic
    def save(self, commit=True):
        profile = super().save(commit)
        user = profile.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.save()
        return profile