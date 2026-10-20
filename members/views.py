import datetime
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .Check_whether_category_is_duplicated import Check_whether_category_is_duplicated
from .forms import SignupForm
from .models import Member, MemberAttribute, PasswordResetRequest, Transaction

MAX_CATEGORY_LENGTH = 25


def get_member(user):
    """Member zum eingeloggten User holen, beim ersten Mal anlegen."""
    member, _ = Member.objects.get_or_create(
        user=user, defaults={"firstname": user.username, "lastname": ""}
    )
    return member


def parse_amount(text):
    """'1.234,50' / '1234.50' / '-30' -> Decimal, sonst None."""
    text = (text or "").strip().replace(" ", "")
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        value = Decimal(text)
    except InvalidOperation:
        return None
    if not value.is_finite():
        return None
    return value.quantize(Decimal("0.01"))


def home(request):
    return redirect("dashboard")


def signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        get_member(user)
        login(request, user)
        messages.success(request, "Willkommen! Dein Konto wurde angelegt.")
        return redirect("dashboard")
    return render(request, "registration/signup.html", {"form": form})


@login_required
def dashboard(request):
    member = get_member(request.user)

    if request.method == "POST":
        # neue Kategorie anlegen
        name = (request.POST.get("category_name") or "").strip()
        comment = (request.POST.get("comment") or "").strip()
        rate = parse_amount(request.POST.get("monthly_amount"))

        if not name or len(name) > MAX_CATEGORY_LENGTH:
            messages.error(request, f"Der Kategoriename muss 1 bis {MAX_CATEGORY_LENGTH} Zeichen lang sein.")
        elif rate is None:
            messages.error(request, "Die monatliche Rate muss eine Zahl sein (positiv = in den Topf, negativ = aus dem Topf zurück).")
        elif Check_whether_category_is_duplicated(member, name):
            messages.error(request, f"Die Kategorie „{name}“ gibt es schon.")
        else:
            today = datetime.date.today()
            attribute = MemberAttribute(
                member=member,
                key="cathegory" + str(member.attributes.count() + 1),
                category=name,
                comment=comment,
                creation_date_of_the_category=today,
            )
            attribute.set_rate(rate, today)
            attribute.save()
            messages.success(request, f"Kategorie „{name}“ angelegt.")
        return redirect("dashboard")

    attributes = list(member.attributes.all())
    rates = [a.current_rate for a in attributes]
    sum_of_rates = sum(rates, Decimal("0"))                          # Netto-Umbuchung in die Toepfe pro Monat
    sum_of_deposits = sum((r for r in rates if r > 0), Decimal("0"))  # vom Gesamtguthaben in Toepfe zurueckgelegt
    sum_of_debits = sum((r for r in rates if r < 0), Decimal("0"))    # aus Toepfen zurueck ins Gesamtguthaben (negativ)
    total_balance = sum((a.balance for a in attributes), Decimal("0"))
    salary = member.monthly_salary
    # Die Monatsrate ist eine Umbuchung: +50 heisst 50 in den Topf (Gesamtguthaben -50),
    # -30 heisst 30 aus dem Topf zurueck (Gesamtguthaben +30).
    remaining = salary - sum_of_rates if salary is not None else None
    transactions = Transaction.objects.filter(attribute__member=member).select_related("attribute")

    return render(request, "dashboard.html", {
        "attributes": attributes,
        "transactions": transactions,
        "salary": salary,
        "sum_of_rates": sum_of_rates,
        "sum_of_deposits": sum_of_deposits,
        "sum_of_debits": sum_of_debits,
        "remaining": remaining,
        "total_balance": total_balance,
    })


@login_required
def change_data(request):
    """Monatliche Rate und Kommentar einer Kategorie aendern."""
    member = get_member(request.user)
    category = request.POST.get("category") if request.method == "POST" else request.GET.get("category")
    attribute = member.attributes.filter(category=category).first()
    if attribute is None:
        messages.error(request, "Diese Kategorie gibt es nicht.")
        return redirect("dashboard")

    if request.method == "POST":
        rate = parse_amount(request.POST.get("monthly_amount_new"))
        if rate is None:
            messages.error(request, "Die monatliche Rate muss eine Zahl sein (positiv = in den Topf, negativ = aus dem Topf zurück).")
            return redirect(f"{request.path}?category={attribute.category}")
        attribute.set_rate(rate)
        comment = (request.POST.get("comment_change") or "").strip()
        if comment:
            attribute.comment = comment
        attribute.save()
        messages.success(request, f"Rate für „{attribute.category}“ auf {rate} € geändert.")
        return redirect("dashboard")

    return render(request, "change_data.html", {"attribute": attribute})


@login_required
@require_POST
def add_transaction(request):
    """Einmalige Einzahlung (+) oder Auszahlung (-) in einer Kategorie."""
    member = get_member(request.user)
    amount = parse_amount(request.POST.get("amount"))
    comment = (request.POST.get("comment") or "").strip()
    attribute = member.attributes.filter(category=request.POST.get("category")).first()

    if attribute is None:
        messages.error(request, "Bitte eine vorhandene Kategorie wählen.")
    elif amount is None or amount == 0:
        messages.error(request, "Der Betrag muss eine Zahl ungleich 0 sein (negativ = Auszahlung).")
    else:
        Transaction.objects.create(attribute=attribute, amount=amount, comment=comment)
        messages.success(request, f"{'Einzahlung' if amount > 0 else 'Auszahlung'} von {abs(amount)} € in „{attribute.category}“ gebucht.")
    return redirect("dashboard")


@login_required
@require_POST
def delete_transaction(request):
    member = get_member(request.user)
    transaction = get_object_or_404(
        Transaction, id=request.POST.get("transaction_id"), attribute__member=member
    )
    transaction.delete()
    messages.success(request, "Buchung gelöscht.")
    return redirect("dashboard")


@login_required
@require_POST
def set_salary(request):
    member = get_member(request.user)
    salary = parse_amount(request.POST.get("monthly_salary"))
    if salary is None or salary < 0:
        messages.error(request, "Das Gehalt muss eine Zahl ≥ 0 sein.")
    else:
        member.monthly_salary = salary
        member.save()
        messages.success(request, "Monatliches Einkommen gespeichert.")
    return redirect("dashboard")


@login_required
@require_POST
def delete_category(request):
    member = get_member(request.user)
    attribute = get_object_or_404(MemberAttribute, id=request.POST.get("attribute_id"), member=member)
    name = attribute.category
    attribute.delete()
    messages.success(request, f"Kategorie „{name}“ gelöscht.")
    return redirect("dashboard")


# =====================================================================
# Passwort vergessen -> Anfrage an den Admin
# =====================================================================

def password_request(request):
    """Nutzer ohne Passwort bittet den Admin um ein neues (kein E-Mail-Versand noetig)."""
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        message = (request.POST.get("message") or "").strip()[:255]
        if not username:
            messages.error(request, "Bitte den Benutzernamen angeben.")
            return redirect("password_request")
        user = User.objects.filter(username__iexact=username).first()
        if not PasswordResetRequest.objects.filter(username__iexact=username, resolved=False).exists():
            PasswordResetRequest.objects.create(username=username, user=user, message=message)
        messages.success(request, "Deine Anfrage wurde an den Admin gesendet. Er setzt dir ein neues Passwort und teilt es dir mit.")
        return redirect("login")
    return render(request, "registration/password_request.html")


# =====================================================================
# Adminboard
# =====================================================================

def staff_only(view):
    """Nur fuer Admins (is_staff); alle anderen bekommen 403."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    wrapper.__name__ = view.__name__
    return wrapper


@staff_only
def adminboard(request):
    if request.method == "POST":
        return _adminboard_action(request)

    users = User.objects.select_related("member").order_by("-date_joined")
    rows = []
    for u in users:
        member = getattr(u, "member", None)
        attributes = list(member.attributes.all()) if member else []
        rows.append({
            "user": u,
            "member": member,
            "online": member.is_online if member else False,
            "last_seen": member.last_seen if member else None,
            "salary": member.monthly_salary if member else None,
            "categories": len(attributes),
            "balance": sum((a.balance for a in attributes), Decimal("0")),
            "transactions": sum(a.transactions.count() for a in attributes),
            "open_request": PasswordResetRequest.objects.filter(user=u, resolved=False).exists(),
        })

    open_requests = PasswordResetRequest.objects.filter(resolved=False)
    done_requests = PasswordResetRequest.objects.filter(resolved=True)[:10]
    online_count = sum(1 for r in rows if r["online"])
    week_ago = timezone.now() - datetime.timedelta(days=7)

    return render(request, "adminboard.html", {
        "rows": rows,
        "open_requests": open_requests,
        "done_requests": done_requests,
        "stats": {
            "users": len(rows),
            "online": online_count,
            "admins": sum(1 for r in rows if r["user"].is_staff),
            "new_this_week": sum(1 for r in rows if r["user"].date_joined >= week_ago),
            "active_this_week": sum(1 for r in rows if r["last_seen"] and r["last_seen"] >= week_ago),
            "categories": MemberAttribute.objects.count(),
            "transactions": Transaction.objects.count(),
            "open_requests": open_requests.count(),
        },
        "online_minutes": Member.ONLINE_MINUTES,
        "recent_transactions": Transaction.objects.select_related("attribute__member__user").order_by("-created")[:10],
    })


def _adminboard_action(request):
    action = request.POST.get("action")
    user_id = request.POST.get("user_id")
    target = User.objects.filter(id=user_id).first() if user_id else None

    if action == "set_password" and target:
        password = request.POST.get("password") or ""
        try:
            validate_password(password, target)
        except ValidationError as e:
            messages.error(request, " ".join(e.messages))
            return redirect("adminboard")
        target.set_password(password)
        target.save()
        PasswordResetRequest.objects.filter(user=target, resolved=False).update(resolved=True, resolved_at=timezone.now())
        messages.success(request, f"Neues Passwort für „{target.username}“ gesetzt. Bitte dem Nutzer mitteilen.")

    elif action == "toggle_active" and target:
        if target == request.user:
            messages.error(request, "Du kannst dich nicht selbst sperren.")
        else:
            target.is_active = not target.is_active
            target.save()
            messages.success(request, f"„{target.username}“ wurde {'entsperrt' if target.is_active else 'gesperrt'}.")

    elif action == "toggle_staff" and target:
        if target == request.user:
            messages.error(request, "Du kannst dir nicht selbst die Admin-Rechte nehmen.")
        else:
            target.is_staff = not target.is_staff
            target.is_superuser = target.is_staff
            target.save()
            messages.success(request, f"„{target.username}“ ist jetzt {'Admin' if target.is_staff else 'normaler Nutzer'}.")

    elif action == "delete_user" and target:
        if target == request.user:
            messages.error(request, "Du kannst dich nicht selbst löschen.")
        else:
            name = target.username
            target.delete()
            messages.success(request, f"Nutzer „{name}“ mit allen Daten gelöscht.")

    elif action == "resolve_request":
        req = get_object_or_404(PasswordResetRequest, id=request.POST.get("request_id"))
        req.resolved = True
        req.resolved_at = timezone.now()
        req.save()
        messages.success(request, f"Anfrage von „{req.username}“ als erledigt markiert.")

    elif action == "delete_request":
        PasswordResetRequest.objects.filter(id=request.POST.get("request_id")).delete()
        messages.success(request, "Anfrage gelöscht.")

    else:
        messages.error(request, "Unbekannte Aktion.")
    return redirect("adminboard")
