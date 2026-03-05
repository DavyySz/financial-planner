from typing import List

from django.db import models
from django.contrib.auth.models import User
from datetime import date
from django.db.models import F
from django.contrib.postgres.fields import ArrayField
from decimal import Decimal


# Create your models here.
class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="member", null=True, blank=True)
    firstname = models.CharField(max_length=255)
    lastname = models.CharField(max_length=255)
    nickname = models.CharField(max_length=255, null=True, blank=True)
    phone = models.IntegerField(null=True)
    joined_date = models.DateField(null=True)

    def __str__(self):
        return f"{self.firstname} {self.lastname}"
    
class MemberAttribute(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="attributes")
    key = models.CharField(max_length=50)
    category = models.CharField(max_length=36)

    monthly_amount = ArrayField(models.DecimalField(max_digits=15, decimal_places=2), default=list, blank=True)
    monthly_amount_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    index_monthly_amount = models.IntegerField(default=0)

    total_amount_of_money_in_the_category = models.DecimalField(max_digits=15,decimal_places=2, null=True, blank=True)
    withdrawal_addition_to_cash = models.DecimalField(max_digits=15,decimal_places=2, null=True, blank=True)
    current_cash_balance_of_the_category = models.DecimalField(max_digits=15,decimal_places=2, null=True, blank=True)
    creation_date_of_the_category = models.DateField(null=True)
    comment = models.CharField(max_length=255, null=True, blank=True)
    date_now = models.DateTimeField(null=True)
    How_many_months_have_passed_since_the_category_was_created = models.IntegerField(null=True)
    number_of_changes_deposit_amount = models.IntegerField(null=True, blank=True)

    false_var = models.BooleanField(default=True)

