from django.contrib import messages
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import role_required
from .forms import VehicleForm,AssignmentForm
from .models import Vehicle, VehicleAssignment,MileageLog


@role_required('ADMIN')
def vehicle_list(request):
    query = request.GET.get('q', '')
    vehicles = Vehicle.objects.order_by('registration_number')
    if query:
        vehicles = vehicles.filter(
            Q(registration_number__icontains=query)
            | Q(make__icontains=query)
            | Q(model__icontains=query)
        )
    return render(request, 'vehicles/vehicle_list.html', {'vehicles': vehicles, 'query': query})


@role_required('ADMIN')
def vehicle_create(request):
    form = VehicleForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Vehicle added.')
        return redirect('vehicle_list')
    return render(request, 'vehicles/vehicle_form.html', {'form': form, 'title': 'Add vehicle'})


@role_required('ADMIN')
def vehicle_update(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    form = VehicleForm(request.POST or None, instance=vehicle)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Vehicle updated.')
        return redirect('vehicle_list')
    return render(request, 'vehicles/vehicle_form.html', {'form': form, 'title': 'Edit vehicle'})


@role_required('ADMIN')
def vehicle_delete(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if request.method == 'POST':
        vehicle.delete()
        messages.success(request, 'Vehicle deleted.')
        return redirect('vehicle_list')
    return render(request, 'vehicles/vehicle_confirm_delete.html', {'vehicle': vehicle})
@role_required('ADMIN')
def vehicle_detail(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)

    current_assignment = (
        vehicle.assignments.filter(end_date__isnull=True)
        .select_related('driver__user')
        .first()
    )

    fuel_total = vehicle.fuel_logs.aggregate(t=Sum('total_cost'))['t'] or 0
    repair_total = vehicle.repair_expenses.aggregate(t=Sum('cost'))['t'] or 0
    service_total = (
        vehicle.maintenance_records.filter(status='APPROVED')
        .aggregate(t=Sum('cost'))['t'] or 0
    )

    days_to_expiry = (vehicle.insurance_expiry - timezone.localdate()).days

    context = {
        'vehicle': vehicle,
        'current_assignment': current_assignment,
        'days_to_expiry': days_to_expiry,
        'schedules': vehicle.schedules.all(),
        'records': vehicle.maintenance_records.all()[:10],
        'mileage_logs': vehicle.mileage_logs.all()[:5],
        'fuel_total': fuel_total,
        'repair_total': repair_total,
        'service_total': service_total,
        'grand_total': fuel_total + repair_total + service_total,
    }
    return render(request, 'vehicles/vehicle_detail.html', context)
@role_required('ADMIN')
def assignment_list(request):
    base = VehicleAssignment.objects.select_related('vehicle', 'driver__user')
    context = {
        'active': base.filter(end_date__isnull=True),
        'past': base.filter(end_date__isnull=False).order_by('-end_date')[:20],
    }
    return render(request, 'vehicles/assignment_list.html', context)


@role_required('ADMIN')
def assignment_create(request):
    form = AssignmentForm(request.POST or None, initial={'start_date': timezone.localdate()})
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Driver assigned.')
        return redirect('assignment_list')
    return render(request, 'vehicles/assignment_form.html', {'form': form})


@role_required('ADMIN')
def assignment_end(request, pk):
    assignment = get_object_or_404(VehicleAssignment, pk=pk, end_date__isnull=True)
    if request.method == 'POST':
        assignment.end_date = max(timezone.localdate(), assignment.start_date)
        assignment.save()
        messages.success(request, 'Assignment ended.')
    return redirect('assignment_list')
@role_required('ADMIN')
def mileage_list(request):
    logs = MileageLog.objects.select_related('vehicle', 'driver__user')
    vehicle_id = request.GET.get('vehicle', '')
    if vehicle_id:
        logs = logs.filter(vehicle_id=vehicle_id)
    context = {
        'logs': logs[:100],
        'vehicles': Vehicle.objects.order_by('registration_number'),
        'selected': vehicle_id,
    }
    return render(request, 'vehicles/mileage_list.html', context)