from .models import PasswordResetRequest


def admin_notices(request):
    """Zahl der offenen Passwort-Anfragen fuer die Kopfzeile (nur fuer Admins)."""
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated or not user.is_staff:
        return {}
    return {"open_reset_requests": PasswordResetRequest.objects.filter(resolved=False).count()}
