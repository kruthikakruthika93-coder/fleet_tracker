from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from drivers.models import DriverProfile
from vehicles.models import Vehicle, VehicleAssignment

User = get_user_model()


class WelcomePopupTests(TestCase):
    def setUp(self):
        today = timezone.localdate()
        self.user = User.objects.create_user(
            'ravi', password='Pass@12345', role='DRIVER', first_name='Ravi')
        self.driver = DriverProfile.objects.create(
            user=self.user, phone='1', license_number='DL-1',
            license_expiry=today + timedelta(days=400))
        self.vehicle = Vehicle.objects.create(
            registration_number='KA-01-POP-1', make='Tata', model='Ace', year=2022,
            fuel_type='DIESEL', current_odometer=1000, insurance_provider='ICICI',
            insurance_policy_number='P1', insurance_expiry=today + timedelta(days=5))
        VehicleAssignment.objects.create(
            vehicle=self.vehicle, driver=self.driver, start_date=today)

    def test_popup_opens_once_per_login(self):
        self.client.force_login(self.user)
        first = self.client.get(reverse('driver_dashboard'))
        self.assertContains(first, 'Welcome to FleetTracker')
        self.assertContains(first, 'data-auto-open="1"')
        second = self.client.get(reverse('driver_dashboard'))
        self.assertContains(second, 'data-auto-open="0"')

    def test_popup_opens_again_after_new_login(self):
        self.client.force_login(self.user)
        self.client.get(reverse('driver_dashboard'))
        self.client.logout()
        self.client.force_login(self.user)
        again = self.client.get(reverse('driver_dashboard'))
        self.assertContains(again, 'data-auto-open="1"')

    def test_popup_lists_notifications(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('driver_dashboard'))
        self.assertContains(response, 'Insurance for KA-01-POP-1')
        self.assertContains(response, 'Log your mileage')