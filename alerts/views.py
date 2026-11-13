from django.shortcuts import redirect, render

from accounts.decorators import role_required
from .models import Alert
from .services import generate_alerts


@role_required('ADMIN')
def alert_list(request):
    generate_alerts()
    alerts = Alert.objects.select_related('vehicle', 'driver__user')
    return render(request, 'alerts/alert_list.html', {'alerts': alerts})


@role_required('ADMIN')
def alert_read(request, pk):
    if request.method == 'POST':
        Alert.objects.filter(pk=pk).update(is_read=True)
    return redirect('alert_list')


@role_required('ADMIN')
def alert_read_all(request):
    if request.method == 'POST':
        Alert.objects.filter(is_read=False).update(is_read=True)
    return redirect('alert_list')