from symtable import Class

from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField

def Calculate_monthly_payments(attributes):
    for x in attributes:
        x.monthly_amount_value = float(x.monthly_amount[x.index_monthly_amount])

    x.save()








