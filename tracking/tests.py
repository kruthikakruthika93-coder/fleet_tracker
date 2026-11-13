import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from drivers.models import DriverProfile
from .models import DriverLocation

User = get_user_model()


class TrackingTests(TestCase):
    def setUp(self):
        expiry = timezone.localdate() + timedelta(days=400)
        self.admin = User.objects.create_user('boss', password='Pass@12345', role='ADMIN')
        self.user1 = User.objects.create_user(
            'ravi', password='Pass@12345', role='DRIVER', first_name='Ravi')
        self.user2 = User.objects.create_user(
            'kiran', password='Pass@12345', role='DRIVER', first_name='Kiran')
        self.driver1 = DriverProfile.objects.create(
            user=self.user1, phone='1', license_number='DL-1', license_expiry=expiry)
        self.driver2 = DriverProfile.objects.create(
            user=self.user2, phone='2', license_number='DL-2', license_expiry=expiry)

    def send(self, payload):
        return self.client.post(
            reverse('location_update'), data=json.dumps(payload),
            content_type='application/json')

    def test_driver_cannot_open_map_or_data(self):
        self.client.force_login(self.user1)
        self.assertEqual(self.client.get(reverse('tracking_map')).status_code, 403)
        self.assertEqual(self.client.get(reverse('tracking_data')).status_code, 403)

    def test_anonymous_user_is_redirected_to_login(self):
        for name in ['tracking_map', 'tracking_data']:
            with self.subTest(page=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 302)
                self.assertIn('/login/', response['Location'])

    def test_admin_can_open_map_and_data(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('tracking_map')).status_code, 200)
        response = self.client.get(reverse('tracking_data'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['drivers'], [])

    def test_location_is_saved_for_own_profile_only(self):
        self.client.force_login(self.user1)
        response = self.send({
            'latitude': 12.5218, 'longitude': 76.8951,
            'accuracy': 15, 'driver': self.driver2.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(DriverLocation.objects.count(), 1)
        saved = DriverLocation.objects.get()
        self.assertEqual(saved.driver, self.driver1)
        self.assertTrue(saved.is_sharing)

    def test_invalid_coordinates_are_rejected(self):
        self.client.force_login(self.user1)
        bad = [
            {'latitude': 123, 'longitude': 10},
            {'latitude': 10, 'longitude': 200},
            {'latitude': 'abc', 'longitude': 10},
            {'latitude': 10},
            {'latitude': 0, 'longitude': 0},
            {'latitude': True, 'longitude': 10},
        ]
        for payload in bad:
            with self.subTest(payload=payload):
                self.assertEqual(self.send(payload).status_code, 400)
        self.assertEqual(DriverLocation.objects.count(), 0)

    def test_admin_cannot_post_a_location(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.send({'latitude': 12.5, 'longitude': 76.9}).status_code, 403)

    def test_stop_marks_driver_offline(self):
        self.client.force_login(self.user1)
        self.send({'latitude': 12.5, 'longitude': 76.9})
        response = self.client.post(reverse('location_stop'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(DriverLocation.objects.get().status, 'OFFLINE')

    def test_status_active_outdated_offline(self):
        loc = DriverLocation.objects.create(
            driver=self.driver1, latitude=12.5, longitude=76.9, is_sharing=True)
        self.assertEqual(loc.status, 'ACTIVE')
        loc.updated_at = timezone.now() - timedelta(minutes=10)
        self.assertEqual(loc.status, 'OUTDATED')
        loc.is_sharing = False
        self.assertEqual(loc.status, 'OFFLINE')

    def test_admin_sees_driver_location(self):
        self.client.force_login(self.user1)
        self.send({'latitude': 12.5218, 'longitude': 76.8951})
        self.client.force_login(self.admin)
        rows = self.client.get(reverse('tracking_data')).json()['drivers']
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['driver'], 'Ravi')
        self.assertEqual(rows[0]['status'], 'ACTIVE')
        self.assertEqual(rows[0]['vehicle'], 'Unassigned')