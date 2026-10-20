import datetime

from django.db.models import Q
from django.utils import timezone

from .models import Member


class LastSeenMiddleware:
    """Merkt sich bei jeder Anfrage eines angemeldeten Nutzers, wann er zuletzt aktiv war
    (hoechstens einmal pro Minute ein Schreibzugriff)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            now = timezone.now()
            Member.objects.filter(user=user).filter(
                Q(last_seen__isnull=True) | Q(last_seen__lt=now - datetime.timedelta(seconds=60))
            ).update(last_seen=now)
        return response
