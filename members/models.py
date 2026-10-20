import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models import Sum
from django.utils import timezone

from .Calculate_monthly_payments import total_amount_of_monthly_payments
from .date import months_since


class Member(models.Model):
    """Ein Nutzer der App. Wird beim ersten Login automatisch zum User angelegt."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="member", null=True, blank=True)
    firstname = models.CharField(max_length=255)
    lastname = models.CharField(max_length=255)
    nickname = models.CharField(max_length=255, null=True, blank=True)
    phone = models.IntegerField(null=True)
    joined_date = models.DateField(null=True)
    monthly_salary = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True)   # letzte Aktivitaet (fuer "online")

    ONLINE_MINUTES = 5

    def __str__(self):
        return f"{self.firstname} {self.lastname}".strip()

    @property
    def is_online(self):
        if not self.last_seen:
            return False
        return self.last_seen >= timezone.now() - datetime.timedelta(minutes=self.ONLINE_MINUTES)


class MemberAttribute(models.Model):
    """Eine Kategorie bzw. ein Budgettopf (z.B. Auto, Urlaub) eines Members.

    monthly_amount speichert die Historie der monatlichen Rate als Liste von
    [betrag, jahr, monat]. Jeder Eintrag gilt ab seinem Monat bis zum Monat des
    naechsten Eintrags; der letzte Eintrag gilt bis heute (inklusive).
    """

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="attributes")
    key = models.CharField(max_length=50)
    category = models.CharField(max_length=36)

    monthly_amount = models.JSONField(default=list, blank=True, encoder=DjangoJSONEncoder)
    monthly_amount_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    index_monthly_amount = models.IntegerField(default=0)

    total_amount_of_money_in_the_category = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    withdrawal_addition_to_cash = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    total_monthly_payments = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    current_cash_balance_of_the_category = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    creation_date_of_the_category = models.DateField(null=True)
    comment = models.CharField(max_length=255, null=True, blank=True)
    date_now = models.DateTimeField(null=True)
    How_many_months_have_passed_since_the_category_was_created = models.IntegerField(null=True)
    number_of_changes_deposit_amount = models.IntegerField(null=True, blank=True)

    category_name_new = models.CharField(max_length=255, null=True, blank=True)
    new_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    false_var = models.BooleanField(default=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.member} – {self.category}"

    # ---- Historie der monatlichen Rate -------------------------------------

    @property
    def rate_history(self):
        """Liste von (Decimal betrag, int jahr, int monat), aelteste zuerst."""
        history = []
        for entry in self.monthly_amount or []:
            if entry and len(entry) >= 3:
                history.append((Decimal(str(entry[0])), int(entry[1]), int(entry[2])))
        return history

    def set_rate(self, amount, today=None):
        """Neue monatliche Rate ab diesem Monat. Innerhalb eines Monats wird
        der Eintrag ueberschrieben statt ein neuer angehaengt."""
        today = today or datetime.date.today()
        entries = [[str(a), y, m] for a, y, m in self.rate_history]
        if entries and entries[-1][1] == today.year and entries[-1][2] == today.month:
            entries[-1][0] = str(amount)
        else:
            entries.append([str(amount), today.year, today.month])
        self.monthly_amount = entries
        self.monthly_amount_value = amount

    # ---- Berechnete Werte (werden nicht gespeichert) ------------------------

    @property
    def current_rate(self):
        history = self.rate_history
        return history[-1][0] if history else Decimal("0")

    @property
    def months_active(self):
        if not self.creation_date_of_the_category:
            return 0
        return months_since(self.creation_date_of_the_category)

    @property
    def paid_rates(self):
        """Summe aller bisher eingezahlten Monatsraten."""
        return total_amount_of_monthly_payments(self.rate_history)

    @property
    def transactions_sum(self):
        return self.transactions.aggregate(s=Sum("amount"))["s"] or Decimal("0")

    @property
    def balance(self):
        """Aktueller Kontostand des Topfs = Monatsraten + Ein-/Auszahlungen."""
        return self.paid_rates + self.transactions_sum


class Transaction(models.Model):
    """Einmalige Einzahlung (+) oder Auszahlung (-) in einer Kategorie."""

    attribute = models.ForeignKey(MemberAttribute, on_delete=models.CASCADE, related_name="transactions")
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    comment = models.CharField(max_length=255, blank=True, default="")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created", "-id"]

    def __str__(self):
        return f"{self.attribute.category}: {self.amount}"


class PasswordResetRequest(models.Model):
    """Ein Nutzer hat sein Passwort vergessen und bittet den Admin um ein neues."""

    username = models.CharField(max_length=150)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="reset_requests")
    message = models.CharField(max_length=255, blank=True, default="")
    created = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["resolved", "-created"]

    def __str__(self):
        return f"{self.username} ({'erledigt' if self.resolved else 'offen'})"
