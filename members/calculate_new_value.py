from symtable import Class

from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField




if request.POST.get("category_name_new") != "":
    a = request.POST.get("category_name_new")
    print(a)