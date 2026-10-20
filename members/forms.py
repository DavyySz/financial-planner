from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class SignupForm(UserCreationForm):
    """Registrierung: Benutzername + Passwort (zweimal)."""

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username",)
