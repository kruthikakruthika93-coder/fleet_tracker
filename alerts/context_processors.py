from .models import Alert


def alert_count(request):
    user = request.user
    if user.is_authenticated and getattr(user, 'role', '') == 'ADMIN':
        return {'nav_alert_count': Alert.objects.filter(is_read=False).count()}
    return {}