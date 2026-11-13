import json
import math
from decimal import Decimal

from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from accounts.decorators import role_required
from drivers.models import DriverProfile
from vehicles.models import VehicleAssignment
from .models import DriverLocation


def clean_number(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError('not a number')
    if not math.isfinite(value) or value < low or value > high:
        raise ValueError('out of range')
    return value


@require_POST
@role_required('DRIVER')
def location_update(request):
    profile = DriverProfile.objects.filter(user=request.user).first()
    if profile is None:
        return JsonResponse({'ok': False, 'error': 'No driver profile.'}, status=403)
    try:
        data = json.loads(request.body or b'{}')
        lat = clean_number(data.get('latitude'), -90, 90)
        lng = clean_number(data.get('longitude'), -180, 180)
        if lat == 0 and lng == 0:
            raise ValueError('invalid position')
        accuracy = data.get('accuracy')
        if accuracy is not None:
            accuracy = float(clean_number(accuracy, 0, 100000))
    except (ValueError, TypeError, AttributeError):
        return JsonResponse({'ok': False, 'error': 'Invalid location data.'}, status=400)

    DriverLocation.objects.update_or_create(
        driver=profile,
        defaults={
            'latitude': Decimal(f'{lat:.6f}'),
            'longitude': Decimal(f'{lng:.6f}'),
            'accuracy': accuracy,
            'is_sharing': True,
            'updated_at': timezone.now(),
        },
    )
    return JsonResponse({'ok': True})


@require_POST
@role_required('DRIVER')
def location_stop(request):
    DriverLocation.objects.filter(driver__user=request.user).update(is_sharing=False)
    return JsonResponse({'ok': True})


@role_required('ADMIN')
def tracking_map(request):
    return render(request, 'tracking/map.html')


@never_cache
@role_required('ADMIN')
def tracking_data(request):
    vehicles = {
        a.driver_id: a.vehicle.registration_number
        for a in VehicleAssignment.objects.filter(end_date__isnull=True).select_related('vehicle')
    }
    now = timezone.now()
    rows = []
    for loc in DriverLocation.objects.select_related('driver__user'):
        rows.append({
            'driver': str(loc.driver),
            'username': loc.driver.user.username,
            'vehicle': vehicles.get(loc.driver_id, 'Unassigned'),
            'latitude': float(loc.latitude),
            'longitude': float(loc.longitude),
            'accuracy': loc.accuracy,
            'updated_at': timezone.localtime(loc.updated_at).strftime('%d %b %Y, %H:%M:%S'),
            'seconds_ago': int((now - loc.updated_at).total_seconds()),
            'status': loc.status,
        })
    return JsonResponse({'drivers': rows})