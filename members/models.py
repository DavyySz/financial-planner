from django.db import models
from django.contrib.auth.models import User

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
    value = models.CharField(max_length=255)