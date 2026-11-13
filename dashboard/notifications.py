from datetime import timedelta

from django.utils import timezone

from maintenance.models import IssueReport, MaintenanceRecord

ICONS = {
    'INSURANCE': 'bi-shield-exclamation',
    'LICENSE': 'bi-person-vcard',
    'SERVICE_KM': 'bi-tools',
    'SERVICE_DATE': 'bi-tools',
}


def build_driver_notices(user, profile, vehicle, alerts):
    today = timezone.localdate()
    notices = []

    for a in sorted(alerts, key=lambda item: item.level != 'danger'):
        if a.alert_type in ('SERVICE_KM', 'SERVICE_DATE'):
            title = 'Maintenance reminder'
        else:
            title = a.get_alert_type_display()
        notices.append({
            'level': a.level,
            'icon': ICONS.get(a.alert_type, 'bi-bell'),
            'title': title,
            'text': a.message,
        })

    if vehicle is None:
        notices.append({
            'level': 'info', 'icon': 'bi-info-circle',
            'title': 'No vehicle assigned',
            'text': 'The company admin has not assigned a vehicle to you yet.',
        })
    else:
        if vehicle.status == 'IN_SERVICE':
            notices.append({
                'level': 'info', 'icon': 'bi-wrench-adjustable',
                'title': 'Vehicle in service',
                'text': f'{vehicle.registration_number} is currently marked as in service.',
            })
        last = vehicle.mileage_logs.first()
        if last is None or (today - last.date).days >= 2:
            notices.append({
                'level': 'info', 'icon': 'bi-speedometer2',
                'title': 'Log your mileage',
                'text': 'Please submit your latest odometer reading.',
            })

    for record in MaintenanceRecord.objects.filter(submitted_by=user, status='PENDING'):
        notices.append({
            'level': 'info', 'icon': 'bi-hourglass-split',
            'title': 'Service waiting for approval',
            'text': f'Your service entry dated {record.service_date:%d %b %Y} is waiting for admin approval.',
        })

    recent = today - timedelta(days=7)
    for record in MaintenanceRecord.objects.filter(
            submitted_by=user, status='APPROVED', service_date__gte=recent):
        notices.append({
            'level': 'success', 'icon': 'bi-check-circle',
            'title': 'Service approved',
            'text': f'Your service entry dated {record.service_date:%d %b %Y} was approved.',
        })

    if profile:
        for issue in IssueReport.objects.filter(driver=profile, status='OPEN'):
            notices.append({
                'level': 'info', 'icon': 'bi-exclamation-octagon',
                'title': 'Issue still open',
                'text': f'You reported: {issue.description[:80]}',
            })

    return notices