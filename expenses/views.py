from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import role_required
from maintenance.views import get_driver_vehicle
from vehicles.models import Vehicle
from .forms import FuelForm, RepairForm
from .models import FuelLog, RepairExpense
from .utils import apply_range, parse_range


def bump_odometer(vehicle, reading):
    if reading > vehicle.current_odometer:
        vehicle.current_odometer = reading
        vehicle.save(update_fields=['current_odometer'])


@role_required('ADMIN')
def expense_home(request):
    start, end = parse_range(request)
    vehicle_id = request.GET.get('vehicle', '')

    fuel = FuelLog.objects.select_related('vehicle', 'driver__user')
    repairs = RepairExpense.objects.select_related('vehicle')
    if vehicle_id:
        fuel = fuel.filter(vehicle_id=vehicle_id)
        repairs = repairs.filter(vehicle_id=vehicle_id)
    fuel = apply_range(fuel, 'date', start, end)
    repairs = apply_range(repairs, 'date', start, end)

    fuel_total = fuel.aggregate(t=Sum('total_cost'))['t'] or 0
    repair_total = repairs.aggregate(t=Sum('cost'))['t'] or 0

    context = {
        'fuel': fuel[:100],
        'repairs': repairs[:100],
        'fuel_total': fuel_total,
        'repair_total': repair_total,
        'grand_total': fuel_total + repair_total,
        'vehicles': Vehicle.objects.order_by('registration_number'),
        'selected': vehicle_id,
        'start_str': start.isoformat() if start else '',
        'end_str': end.isoformat() if end else '',
    }
    return render(request, 'expenses/expense_home.html', context)


@role_required('ADMIN')
def fuel_create(request):
    form = FuelForm(request.POST or None, initial={'date': timezone.localdate()})
    if request.method == 'POST' and form.is_valid():
        log = form.save()
        bump_odometer(log.vehicle, log.odometer)
        messages.success(request, 'Fuel entry saved.')
        return redirect('expense_home')
    return render(request, 'form_page.html', {
        'form': form, 'title': 'Add fuel entry', 'cancel_url': 'expense_home'})


@role_required('ADMIN')
def repair_create(request):
    form = RepairForm(request.POST or None, initial={'date': timezone.localdate()})
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Repair expense saved.')
        return redirect('expense_home')
    return render(request, 'form_page.html', {
        'form': form, 'title': 'Add repair expense', 'cancel_url': 'expense_home'})


@role_required('ADMIN')
def fuel_delete(request, pk):
    entry = get_object_or_404(FuelLog, pk=pk)
    if request.method == 'POST':
        entry.delete()
        messages.success(request, 'Fuel entry deleted.')
    return redirect('expense_home')


@role_required('ADMIN')
def repair_delete(request, pk):
    entry = get_object_or_404(RepairExpense, pk=pk)
    if request.method == 'POST':
        entry.delete()
        messages.success(request, 'Repair expense deleted.')
    return redirect('expense_home')


@role_required('DRIVER')
def driver_fuel(request):
    profile, vehicle = get_driver_vehicle(request.user)
    if not vehicle:
        messages.warning(request, 'No vehicle is assigned to you yet.')
        return redirect('driver_dashboard')
    form = FuelForm(request.POST or None, fixed=True,
                    initial={'date': timezone.localdate(), 'odometer': vehicle.current_odometer})
    if request.method == 'POST' and form.is_valid():
        log = form.save(commit=False)
        log.vehicle = vehicle
        log.driver = profile
        log.save()
        bump_odometer(vehicle, log.odometer)
        messages.success(request, 'Fuel entry saved.')
        return redirect('driver_dashboard')
    return render(request, 'form_page.html', {
        'form': form, 'title': 'Add fuel entry', 'cancel_url': 'driver_dashboard'})