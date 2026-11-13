from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from alerts.models import Alert
from alerts.services import generate_alerts
from drivers.models import DriverProfile
from maintenance.models import MaintenanceRecord, MaintenanceSchedule
from vehicles.forms import AssignmentForm, MileageForm
from vehicles.models import MileageLog, Vehicle, VehicleAssignment

User = get_user_model()


class FleetTestCase(TestCase):
    def setUp(self):
        self.today = timezone.localdate()
        self.admin = User.objects.create_user('boss', password='Pass@12345', role='ADMIN')
        self.driver_user = User.objects.create_user(
            'ravi', password='Pass@12345', role='DRIVER', first_name='Ravi')
        self.driver = DriverProfile.objects.create(
            user=self.driver_user, phone='9999999999', license_number='DL-1',
            license_expiry=self.today + timedelta(days=400))
        self.vehicle = Vehicle.objects.create(
            registration_number='KA-01-TEST-1', make='Tata', model='Ace', year=2022,
            fuel_type='DIESEL', current_odometer=1000, insurance_provider='ICICI',
            insurance_policy_number='P1', insurance_expiry=self.today + timedelta(days=400))


class AccessControlTests(FleetTestCase):
    def test_anonymous_user_is_sent_to_login(self):
        response = self.client.get(reverse('vehicle_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])

    def test_driver_is_blocked_from_admin_pages(self):
        self.client.force_login(self.driver_user)
        for name in ['vehicle_list', 'driver_list', 'maintenance_home',
                     'expense_home', 'report_summary', 'alert_list']:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 403)

    def test_admin_is_blocked_from_driver_dashboard(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('driver_dashboard')).status_code, 403)

    def test_home_redirects_by_role(self):
        self.client.force_login(self.admin)
        self.assertRedirects(self.client.get(reverse('home')), reverse('admin_dashboard'))
        self.client.force_login(self.driver_user)
        self.assertRedirects(self.client.get(reverse('home')), reverse('driver_dashboard'))

    def test_driver_cannot_approve_service(self):
        record = MaintenanceRecord.objects.create(
            vehicle=self.vehicle, service_date=self.today, odometer=1500,
            cost=Decimal('1800'), workshop='Sri Auto', status='PENDING')
        self.client.force_login(self.driver_user)
        response = self.client.post(reverse('record_approve', args=[record.pk]))
        self.assertEqual(response.status_code, 403)
        record.refresh_from_db()
        self.assertEqual(record.status, 'PENDING')


class ValidationTests(FleetTestCase):
    def test_mileage_rejects_lower_reading(self):
        form = MileageForm(
            {'date': self.today.isoformat(), 'odometer_reading': 500, 'notes': ''},
            vehicle=self.vehicle)
        self.assertFalse(form.is_valid())
        self.assertIn('odometer_reading', form.errors)

    def test_mileage_rejects_future_date(self):
        future = self.today + timedelta(days=3)
        form = MileageForm(
            {'date': future.isoformat(), 'odometer_reading': 1200, 'notes': ''},
            vehicle=self.vehicle)
        self.assertFalse(form.is_valid())
        self.assertIn('date', form.errors)

    def test_vehicle_cannot_have_two_active_drivers(self):
        VehicleAssignment.objects.create(
            vehicle=self.vehicle, driver=self.driver, start_date=self.today)
        other_user = User.objects.create_user('kiran', password='x', role='DRIVER')
        other = DriverProfile.objects.create(
            user=other_user, phone='1', license_number='DL-2',
            license_expiry=self.today + timedelta(days=400))
        form = AssignmentForm({
            'vehicle': self.vehicle.pk, 'driver': other.pk,
            'start_date': self.today.isoformat()})
        self.assertFalse(form.is_valid())


class BusinessLogicTests(FleetTestCase):
    def make_schedule(self):
        return MaintenanceSchedule.objects.create(
            vehicle=self.vehicle, service_type='OIL', interval_km=5000,
            interval_days=180, last_service_km=0, last_service_date=self.today)

    def test_next_due_is_calculated(self):
        schedule = MaintenanceSchedule.objects.create(
            vehicle=self.vehicle, service_type='OIL', interval_km=5000,
            interval_days=180, last_service_km=44000, last_service_date=self.today)
        self.assertEqual(schedule.next_due_km, 49000)
        self.assertEqual(schedule.next_due_date, self.today + timedelta(days=180))

    def test_driver_mileage_updates_odometer(self):
        VehicleAssignment.objects.create(
            vehicle=self.vehicle, driver=self.driver, start_date=self.today)
        self.client.force_login(self.driver_user)
        response = self.client.post(reverse('driver_dashboard'), {
            'date': self.today.isoformat(), 'odometer_reading': 1200, 'notes': ''})
        self.assertRedirects(response, reverse('driver_dashboard'))
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.current_odometer, 1200)
        self.assertEqual(MileageLog.objects.count(), 1)

    def test_approval_resets_schedule(self):
        schedule = self.make_schedule()
        record = MaintenanceRecord.objects.create(
            vehicle=self.vehicle, schedule=schedule, service_date=self.today,
            odometer=1500, cost=Decimal('1800'), workshop='Sri Auto', status='PENDING')
        self.client.force_login(self.admin)
        self.client.post(reverse('record_approve', args=[record.pk]))
        record.refresh_from_db()
        schedule.refresh_from_db()
        self.vehicle.refresh_from_db()
        self.assertEqual(record.status, 'APPROVED')
        self.assertEqual(schedule.last_service_km, 1500)
        self.assertEqual(schedule.next_due_km, 6500)
        self.assertEqual(self.vehicle.current_odometer, 1500)

    def test_insurance_alert_is_created_and_cleared(self):
        self.vehicle.insurance_expiry = self.today + timedelta(days=5)
        self.vehicle.save()
        generate_alerts()
        self.assertTrue(Alert.objects.filter(
            alert_type='INSURANCE', vehicle=self.vehicle).exists())
        self.vehicle.insurance_expiry = self.today + timedelta(days=200)
        self.vehicle.save()
        generate_alerts()
        self.assertFalse(Alert.objects.filter(alert_type='INSURANCE').exists())

    def test_service_alert_when_close_to_due_km(self):
        self.make_schedule()
        self.vehicle.current_odometer = 4800
        self.vehicle.save()
        generate_alerts()
        self.assertTrue(Alert.objects.filter(
            alert_type='SERVICE_KM', vehicle=self.vehicle).exists())

    def test_csv_report_contains_vehicle(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse('report_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response['Content-Type'].startswith('text/csv'))
        self.assertIn('KA-01-TEST-1', response.content.decode())

    def test_deleting_vehicle_removes_related_records(self):
        MileageLog.objects.create(
            vehicle=self.vehicle, driver=self.driver, date=self.today, odometer_reading=1100)
        self.make_schedule()
        self.vehicle.delete()
        self.assertEqual(MileageLog.objects.count(), 0)
        self.assertEqual(MaintenanceSchedule.objects.count(), 0)