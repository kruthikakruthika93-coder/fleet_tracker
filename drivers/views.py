from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import role_required
from vehicles.models import VehicleAssignment
from .forms import DriverCreateForm, DriverUpdateForm
from .models import DriverProfile


@role_required('ADMIN')
def driver_list(request):
    drivers = DriverProfile.objects.select_related('user').order_by('user__first_name', 'user__username')
    current = {
        a.driver_id: a.vehicle
        for a in VehicleAssignment.objects.filter(end_date__isnull=True).select_related('vehicle')
    }
    today = timezone.localdate()
    rows = [
        {'d': d, 'vehicle': current.get(d.pk), 'days': (d.license_expiry - today).days}
        for d in drivers
    ]
    return render(request, 'drivers/driver_list.html', {'rows': rows})


@role_required('ADMIN')
def driver_create(request):
    form = DriverCreateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Driver added. They can now log in.')
        return redirect('driver_list')
    return render(request, 'form_page.html', {
        'form': form, 'title': 'Add driver', 'cancel_url': 'driver_list'})


@role_required('ADMIN')
def driver_update(request, pk):
    profile = get_object_or_404(DriverProfile, pk=pk)
    form = DriverUpdateForm(request.POST or None, instance=profile)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Driver updated.')
        return redirect('driver_list')
    return render(request, 'form_page.html', {
        'form': form, 'title': 'Edit driver', 'cancel_url': 'driver_list'})


@role_required('ADMIN')
def driver_delete(request, pk):
    profile = get_object_or_404(DriverProfile, pk=pk)
    if request.method == 'POST':
        profile.user.delete()
        messages.success(request, 'Driver deleted.')
    return redirect('driver_list')