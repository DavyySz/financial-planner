from symtable import Class
from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.http import HttpResponse

def Check_whether_category_is_duplicated(value_from_input):
    value_from_input_ = value_from_input
    attributes = User.objects.first().member.attributes.all()
    for x in attributes:
        if value_from_input_ == x.category:
            return False



    #User.objects.first().member.attributes.values_list("category", flat=True).first()
