from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


@login_required
def home(request):
    if request.user.role == 'ADMIN':
        return redirect('admin_dashboard')
    return redirect('driver_dashboard')