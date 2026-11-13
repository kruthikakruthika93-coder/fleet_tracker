from datetime import date

from django.contrib import messages
from django.db.models import Q, Sum
from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.decorators import role_required
from alerts.models import Alert
from alerts.services import generate_alerts
from drivers.models import DriverProfile
from expenses.models import FuelLog, RepairExpense
from maintenance.models import IssueReport, MaintenanceRecord
from vehicles.forms import MileageForm
from vehicles.models import Vehicle, VehicleAssignment
from .notifications import build_driver_notices

def monthly_expenses(months=6):
    first = timezone.localdate().replace(day=1)
    labels, fuel, repair = [], [], []
    for i in range(months - 1, -1, -1):
        year, month = first.year, first.month - i
        while month <= 0:
            month += 12
            year -= 1
        start = date(year, month, 1)
        end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
        f = FuelLog.objects.filter(date__gte=start, date__lt=end).aggregate(t=Sum('total_cost'))['t'] or 0
        r = RepairExpense.objects.filter(date__gte=start, date__lt=end).aggregate(t=Sum('cost'))['t'] or 0
        labels.append(start.strftime('%b %Y'))
        fuel.append(float(f))
        repair.append(float(r))
    return {'labels': labels, 'fuel': fuel, 'repair': repair}


@role_required('ADMIN')
def admin_dashboard(request):
    generate_alerts()
    unread = Alert.objects.filter(is_read=False).select_related('vehicle', 'driver__user')
    context = {
        'vehicle_count': Vehicle.objects.count(),
        'driver_count': DriverProfile.objects.count(),
        'unread_count': unread.count(),
        'pending_count': MaintenanceRecord.objects.filter(status='PENDING').count(),
        'issue_count': IssueReport.objects.filter(status='OPEN').count(),
        'alerts': unread[:5],
        'active_count': Vehicle.objects.filter(status='ACTIVE').count(),
        'service_count': Vehicle.objects.filter(status='IN_SERVICE').count(),
        'inactive_count': Vehicle.objects.filter(status='INACTIVE').count(),
        'chart_data': monthly_expenses(),
    }
    return render(request, 'dashboard/admin_dashboard.html', context)

@role_required('DRIVER')
def driver_dashboard(request):
    profile = DriverProfile.objects.filter(user=request.user).first()
    assignment = None
    if profile:
        assignment = (
            VehicleAssignment.objects
            .filter(driver=profile, end_date__isnull=True)
            .select_related('vehicle')
            .first()
        )
    vehicle = assignment.vehicle if assignment else None

    form = None
    logs = []
    if vehicle:
        form = MileageForm(
            request.POST or None,
            vehicle=vehicle,
            initial={'date': timezone.localdate()},
        )
        if request.method == 'POST' and form.is_valid():
            log = form.save(commit=False)
            log.vehicle = vehicle
            log.driver = profile
            log.save()
            if log.odometer_reading > vehicle.current_odometer:
                vehicle.current_odometer = log.odometer_reading
                vehicle.save(update_fields=['current_odometer'])
            messages.success(request, 'Mileage saved.')
            return redirect('driver_dashboard')
        logs = vehicle.mileage_logs.all()[:5]

    generate_alerts()
    alert_filter = Q(pk__in=[])
    if profile:
        alert_filter |= Q(driver=profile)
    if vehicle:
        alert_filter |= Q(vehicle=vehicle)
    alerts = Alert.objects.filter(alert_filter)

    notices = build_driver_notices(request.user, profile, vehicle, alerts)
    show_welcome = not request.session.get('welcome_shown', False)
    request.session['welcome_shown'] = True

    context = {
        'profile': profile, 'vehicle': vehicle, 'form': form, 'logs': logs,
        'alerts': alerts, 'notices': notices, 'show_welcome': show_welcome,
    }
    return render(request, 'dashboard/driver_dashboard.html', context)