from django.utils import timezone

from drivers.models import DriverProfile
from maintenance.models import MaintenanceSchedule
from vehicles.models import Vehicle
from .models import Alert

INSURANCE_DAYS = 30
LICENSE_DAYS = 30
SERVICE_DAYS = 14
SERVICE_KM = 500


def generate_alerts():
    today = timezone.localdate()
    wanted = {}

    def want(alert_type, message, vehicle=None, driver=None, due_date=None):
        key = (alert_type, vehicle.pk if vehicle else None, driver.pk if driver else None, message)
        wanted[key] = due_date

    for v in Vehicle.objects.exclude(status='INACTIVE'):
        days = (v.insurance_expiry - today).days
        if days < 0:
            want('INSURANCE', f'Insurance for {v.registration_number} expired on {v.insurance_expiry:%d %b %Y}',
                 vehicle=v, due_date=v.insurance_expiry)
        elif days <= INSURANCE_DAYS:
            want('INSURANCE', f'Insurance for {v.registration_number} expires on {v.insurance_expiry:%d %b %Y}',
                 vehicle=v, due_date=v.insurance_expiry)

    for d in DriverProfile.objects.select_related('user'):
        days = (d.license_expiry - today).days
        if days < 0:
            want('LICENSE', f'Licence of {d} expired on {d.license_expiry:%d %b %Y}',
                 driver=d, due_date=d.license_expiry)
        elif days <= LICENSE_DAYS:
            want('LICENSE', f'Licence of {d} expires on {d.license_expiry:%d %b %Y}',
                 driver=d, due_date=d.license_expiry)

    schedules = MaintenanceSchedule.objects.select_related('vehicle').exclude(vehicle__status='INACTIVE')
    for s in schedules:
        v = s.vehicle
        name = s.get_service_type_display()
        if s.next_due_km is not None and s.next_due_km - v.current_odometer <= SERVICE_KM:
            want('SERVICE_KM', f'{name} for {v.registration_number} is due at {s.next_due_km} km', vehicle=v)
        if s.next_due_date and (s.next_due_date - today).days <= SERVICE_DAYS:
            want('SERVICE_DATE', f'{name} for {v.registration_number} is due on {s.next_due_date:%d %b %Y}',
                 vehicle=v, due_date=s.next_due_date)

    existing = {}
    for a in Alert.objects.all():
        existing[(a.alert_type, a.vehicle_id, a.driver_id, a.message)] = a

    for key, due in wanted.items():
        if key not in existing:
            alert_type, vehicle_id, driver_id, message = key
            Alert.objects.create(
                alert_type=alert_type, vehicle_id=vehicle_id,
                driver_id=driver_id, message=message, due_date=due,
            )

    for key, alert in existing.items():
        if key not in wanted:
            alert.delete()