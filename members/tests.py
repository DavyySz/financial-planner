import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .Calculate_monthly_payments import months_between, total_amount_of_monthly_payments
from .date import months_since
from .models import Member, MemberAttribute, PasswordResetRequest, Transaction


class CalculationTests(TestCase):
    def test_months_between(self):
        self.assertEqual(months_between(2026, 1, 2026, 1), 0)
        self.assertEqual(months_between(2025, 11, 2026, 2), 3)

    def test_months_since_counts_creation_month(self):
        today = datetime.date(2026, 10, 20)
        self.assertEqual(months_since(datetime.date(2026, 10, 1), today), 1)
        self.assertEqual(months_since(datetime.date(2026, 3, 8), today), 8)

    def test_total_paid_rates_with_rate_change(self):
        today = datetime.date(2026, 10, 20)
        # 50 € ab 03/2026 (4 Monate: 3,4,5,6), dann 100 € ab 07/2026 (4 Monate: 7,8,9,10)
        history = [(Decimal("50"), 2026, 3), (Decimal("100"), 2026, 7)]
        self.assertEqual(total_amount_of_monthly_payments(history, today), Decimal("600"))

    def test_total_paid_rates_single_entry(self):
        today = datetime.date(2026, 10, 20)
        self.assertEqual(total_amount_of_monthly_payments([(Decimal("200"), 2026, 10)], today), Decimal("200"))
        self.assertEqual(total_amount_of_monthly_payments([], today), Decimal("0"))


class ModelTests(TestCase):
    def setUp(self):
        self.member = Member.objects.create(firstname="Test", lastname="")

    def test_set_rate_overwrites_within_same_month(self):
        a = MemberAttribute(member=self.member, key="k", category="Auto",
                            creation_date_of_the_category=datetime.date(2026, 10, 1))
        a.set_rate(Decimal("100"), datetime.date(2026, 10, 1))
        a.set_rate(Decimal("150"), datetime.date(2026, 10, 20))
        a.save()
        a.refresh_from_db()
        self.assertEqual(a.rate_history, [(Decimal("150"), 2026, 10)])
        a.set_rate(Decimal("200"), datetime.date(2026, 11, 1))
        self.assertEqual(len(a.rate_history), 2)
        self.assertEqual(a.current_rate, Decimal("200"))

    def test_balance_includes_transactions(self):
        a = MemberAttribute(member=self.member, key="k", category="Auto",
                            creation_date_of_the_category=datetime.date.today())
        a.set_rate(Decimal("100"))
        a.save()
        Transaction.objects.create(attribute=a, amount=Decimal("-30"), comment="Reparatur")
        Transaction.objects.create(attribute=a, amount=Decimal("5.50"))
        self.assertEqual(a.paid_rates, Decimal("100"))
        self.assertEqual(a.transactions_sum, Decimal("-24.50"))
        self.assertEqual(a.balance, Decimal("75.50"))


class ViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("anna", password="geheim-1234")
        self.client.login(username="anna", password="geheim-1234")

    def test_home_redirects_to_login_when_anonymous(self):
        self.client.logout()
        response = self.client.get("/", follow=True)
        self.assertEqual(response.redirect_chain[-1][0], "/login/?next=/dashboard/")

    def test_signup_creates_user_and_member(self):
        self.client.logout()
        response = self.client.post(reverse("signup"), {
            "username": "ben", "password1": "sehr-sicher-99", "password2": "sehr-sicher-99"})
        self.assertRedirects(response, reverse("dashboard"))
        self.assertTrue(Member.objects.filter(user__username="ben").exists())

    def test_full_flow(self):
        r = self.client.post(reverse("dashboard"), {"category_name": "Auto", "monthly_amount": "100", "comment": "x"})
        self.assertRedirects(r, reverse("dashboard"))
        # doppelter Name wird abgelehnt
        self.client.post(reverse("dashboard"), {"category_name": "auto", "monthly_amount": "5"})
        self.assertEqual(MemberAttribute.objects.count(), 1)

        self.client.post(reverse("change_data"), {"category": "Auto", "monthly_amount_new": "150,50"})
        self.client.post(reverse("add_transaction"), {"category": "Auto", "amount": "-30", "comment": "Reparatur"})
        self.client.post(reverse("set_salary"), {"monthly_salary": "2000"})

        a = MemberAttribute.objects.get(category="Auto")
        self.assertEqual(a.current_rate, Decimal("150.50"))
        self.assertEqual(a.balance, Decimal("120.50"))

        r = self.client.get(reverse("dashboard"))
        self.assertContains(r, "Auto")
        self.assertContains(r, "Reparatur")
        self.assertEqual(r.context["remaining"], Decimal("1849.50"))

        r = self.client.get(reverse("change_data") + "?category=Auto")
        self.assertContains(r, "Verlauf der Rate")

        tx = Transaction.objects.get()
        self.client.post(reverse("delete_transaction"), {"transaction_id": tx.id})
        self.assertEqual(Transaction.objects.count(), 0)
        self.client.post(reverse("delete_category"), {"attribute_id": a.id})
        self.assertEqual(MemberAttribute.objects.count(), 0)

    def test_rate_is_a_transfer_between_total_and_pot(self):
        """+50 Auto: Topf +50/Monat, Gesamtguthaben -50. -30 Alt: Topf -30/Monat, Gesamtguthaben +30."""
        self.client.post(reverse("set_salary"), {"monthly_salary": "2500"})
        self.client.post(reverse("dashboard"), {"category_name": "Auto", "monthly_amount": "50"})
        self.client.post(reverse("dashboard"), {"category_name": "Alt", "monthly_amount": "-30"})
        auto = MemberAttribute.objects.get(category="Auto")
        alt = MemberAttribute.objects.get(category="Alt")
        self.assertEqual(auto.balance, Decimal("50"))
        self.assertEqual(alt.balance, Decimal("-30"))
        r = self.client.get(reverse("dashboard"))
        self.assertEqual(r.context["sum_of_deposits"], Decimal("50"))
        self.assertEqual(r.context["sum_of_debits"], Decimal("-30"))
        self.assertEqual(r.context["remaining"], Decimal("2480"))   # 2500 - 50 + 30
        self.assertEqual(r.context["total_balance"], Decimal("20"))
        # Entnahme aus dem Autotopf per Buchung
        self.client.post(reverse("add_transaction"), {"category": "Auto", "amount": "-20", "comment": "Reifen"})
        self.assertEqual(MemberAttribute.objects.get(category="Auto").balance, Decimal("30"))

    def test_invalid_amount_shows_error(self):
        r = self.client.post(reverse("dashboard"), {"category_name": "Auto", "monthly_amount": "abc"}, follow=True)
        self.assertContains(r, "muss eine Zahl")
        self.assertEqual(MemberAttribute.objects.count(), 0)

    def test_users_cannot_touch_each_others_data(self):
        other = User.objects.create_user("eve", password="geheim-1234")
        member = Member.objects.create(user=other, firstname="eve", lastname="")
        a = MemberAttribute(member=member, key="k", category="Geheim", creation_date_of_the_category=datetime.date.today())
        a.set_rate(Decimal("10"))
        a.save()
        r = self.client.get(reverse("dashboard"))
        self.assertNotContains(r, "Geheim")
        r = self.client.post(reverse("delete_category"), {"attribute_id": a.id})
        self.assertEqual(r.status_code, 404)
        self.assertTrue(MemberAttribute.objects.filter(id=a.id).exists())


class AdminboardTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user("chef", password="chef-pass-2026", is_staff=True, is_superuser=True)
        self.user = User.objects.create_user("anna", password="anna-pass-2026")
        Member.objects.create(user=self.user, firstname="anna", lastname="")

    def test_password_request_creates_entry_and_admin_sees_it(self):
        r = self.client.post(reverse("password_request"), {"username": "Anna", "message": "bitte neu"})
        self.assertRedirects(r, reverse("login"))
        req = PasswordResetRequest.objects.get()
        self.assertEqual(req.user, self.user)
        self.assertFalse(req.resolved)
        # doppelte offene Anfrage wird nicht angelegt
        self.client.post(reverse("password_request"), {"username": "anna"})
        self.assertEqual(PasswordResetRequest.objects.count(), 1)

        self.client.login(username="chef", password="chef-pass-2026")
        r = self.client.get(reverse("dashboard"))
        self.assertContains(r, "1 offene Passwort-Anfrage")
        r = self.client.get(reverse("adminboard"))
        self.assertContains(r, "bitte neu")
        self.assertEqual(r.context["stats"]["users"], 2)

        # Admin setzt neues Passwort -> Anfrage erledigt, Login mit neuem Passwort klappt
        self.client.post(reverse("adminboard"), {"action": "set_password", "user_id": self.user.id, "password": "neues-pass-2026"})
        req.refresh_from_db()
        self.assertTrue(req.resolved)
        self.client.logout()
        self.assertTrue(self.client.login(username="anna", password="neues-pass-2026"))

    def test_adminboard_forbidden_for_normal_users(self):
        self.client.login(username="anna", password="anna-pass-2026")
        self.assertEqual(self.client.get(reverse("adminboard")).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(reverse("adminboard")).status_code, 302)

    def test_online_status_and_lock(self):
        self.client.login(username="anna", password="anna-pass-2026")
        self.client.get(reverse("dashboard"))          # Middleware setzt last_seen
        self.assertTrue(Member.objects.get(user=self.user).is_online)
        self.client.logout()

        self.client.login(username="chef", password="chef-pass-2026")
        r = self.client.get(reverse("adminboard"))
        self.assertEqual(r.context["stats"]["online"], 1)
        self.client.post(reverse("adminboard"), {"action": "toggle_active", "user_id": self.user.id})
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        # sich selbst sperren geht nicht
        self.client.post(reverse("adminboard"), {"action": "toggle_active", "user_id": self.admin.id})
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)
