from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import role_required
from drivers.models import DriverProfile
from vehicles.models import VehicleAssignment
from .forms import ScheduleForm, RecordForm, IssueForm
from .models import MaintenanceSchedule, MaintenanceRecord, IssueReport


def get_driver_vehicle(user):
    profile = DriverProfile.objects.filter(user=user).first()
    if not profile:
        return None, None
    assignment = (
        VehicleAssignment.objects
        .filter(driver=profile, end_date__isnull=True)
        .select_related('vehicle')
        .first()
    )
    return profile, (assignment.vehicle if assignment else None)


def apply_record(record):
    vehicle = record.vehicle
    if record.odometer > vehicle.current_odometer:
        vehicle.current_odometer = record.odometer
        vehicle.save(update_fields=['current_odometer'])
    schedule = record.schedule
    if schedule:
        schedule.last_service_km = record.odometer
        schedule.last_service_date = record.service_date
        schedule.save()


@role_required('ADMIN')
def maintenance_home(request):
    today = timezone.localdate()
    rows = []
    for s in MaintenanceSchedule.objects.select_related('vehicle'):
        km_left = None
        if s.next_due_km is not None:
            km_left = s.next_due_km - s.vehicle.current_odometer
        days_left = None
        if s.next_due_date:
            days_left = (s.next_due_date - today).days
        overdue = (km_left is not None and km_left <= 0) or (days_left is not None and days_left < 0)
        soon = (km_left is not None and km_left <= 500) or (days_left is not None and days_left <= 14)
        rows.append({'s': s, 'km_left': km_left, 'days_left': days_left,
                     'overdue': overdue, 'soon': soon})
    context = {
        'rows': rows,
        'pending': MaintenanceRecord.objects.filter(status='PENDING').select_related('vehicle', 'submitted_by'),
        'issues': IssueReport.objects.filter(status='OPEN').select_related('vehicle', 'driver__user'),
        'recent': MaintenanceRecord.objects.filter(status='APPROVED').select_related('vehicle')[:10],
    }
    return render(request, 'maintenance/maintenance_home.html', context)


@role_required('ADMIN')
def schedule_create(request):
    form = ScheduleForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Schedule added.')
        return redirect('maintenance_home')
    return render(request, 'form_page.html', {
        'form': form, 'title': 'Add maintenance schedule', 'cancel_url': 'maintenance_home'})


@role_required('ADMIN')
def schedule_delete(request, pk):
    schedule = get_object_or_404(MaintenanceSchedule, pk=pk)
    if request.method == 'POST':
        schedule.delete()
        messages.success(request, 'Schedule deleted.')
    return redirect('maintenance_home')


@role_required('ADMIN')
def record_create(request):
    form = RecordForm(request.POST or None, initial={'service_date': timezone.localdate()})
    if request.method == 'POST' and form.is_valid():
        record = form.save(commit=False)
        record.status = 'APPROVED'
        record.submitted_by = request.user
        record.save()
        apply_record(record)
        messages.success(request, 'Service record saved.')
        return redirect('maintenance_home')
    return render(request, 'form_page.html', {
        'form': form, 'title': 'Add service record', 'cancel_url': 'maintenance_home'})


@role_required('ADMIN')
def record_approve(request, pk):
    record = get_object_or_404(MaintenanceRecord, pk=pk, status='PENDING')
    if request.method == 'POST':
        record.status = 'APPROVED'
        record.save()
        apply_record(record)
        messages.success(request, 'Service approved.')
    return redirect('maintenance_home')


@role_required('ADMIN')
def issue_resolve(request, pk):
    issue = get_object_or_404(IssueReport, pk=pk, status='OPEN')
    if request.method == 'POST':
        issue.status = 'RESOLVED'
        issue.save()
        messages.success(request, 'Issue resolved.')
    return redirect('maintenance_home')


@role_required('DRIVER')
def driver_service(request):
    profile, vehicle = get_driver_vehicle(request.user)
    if not vehicle:
        messages.warning(request, 'No vehicle is assigned to you yet.')
        return redirect('driver_dashboard')
    form = RecordForm(request.POST or None, vehicle=vehicle,
                      initial={'service_date': timezone.localdate()})
    if request.method == 'POST' and form.is_valid():
        record = form.save(commit=False)
        record.vehicle = vehicle
        record.status = 'PENDING'
        record.submitted_by = request.user
        record.save()
        messages.success(request, 'Service submitted. Waiting for admin approval.')
        return redirect('driver_dashboard')
    return render(request, 'form_page.html', {
        'form': form, 'title': 'Submit completed service', 'cancel_url': 'driver_dashboard'})


@role_required('DRIVER')
def driver_issue(request):
    profile, vehicle = get_driver_vehicle(request.user)
    if not vehicle:
        messages.warning(request, 'No vehicle is assigned to you yet.')
        return redirect('driver_dashboard')
    form = IssueForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        issue = form.save(commit=False)
        issue.vehicle = vehicle
        issue.driver = profile
        issue.save()
        messages.success(request, 'Issue reported to the admin.')
        return redirect('driver_dashboard')
    return render(request, 'form_page.html', {
        'form': form, 'title': 'Report an issue', 'cancel_url': 'driver_dashboard'})