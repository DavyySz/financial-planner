from pdb import find_function

from django.http import HttpResponse
from django.template import loader
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Member
from members.models import MemberAttribute
from django.contrib import messages
from django.shortcuts import render, redirect
import datetime
from .date import past_months_since_deposit
from django.contrib.postgres.fields import ArrayField


def members(request):
  mymembers = Member.objects.all().values()
  template = loader.get_template('all_members.html')
  context = {'mymembers': mymembers,}
  return HttpResponse(template.render(context, request))
  
def details(request, id):
  mymember = Member.objects.get(id=id)
  template = loader.get_template('details.html')
  context = {'mymember': mymember,}
  return HttpResponse(template.render(context, request))

def main(request):
  template = loader.get_template('main.html')
  return HttpResponse(template.render())

def testing(request):
  template = loader.get_template('template.html')
  context = {
    'fruits': ['Apple', 'Banana', 'Cherry'],   
  }
  return HttpResponse(template.render(context, request))

def double_bracket(request):
  mymembers = Member.objects.all().values()
  template = loader.get_template('template.html')
  context = {'mymembers': mymembers,}
  return HttpResponse(template.render(context, request))

@login_required
def dashboard(request):

    attributes = request.user.member.attributes.all()
    past_months_since_deposit(attributes)

    if request.method == "POST":
      if len(request.POST.get("category_name")) <= 25:
        value_from_input = request.POST.get("category_name")
      else:
        attributes = "category_string_to_long"
      value_monthly_amount = request.POST.get("monthly_amount")
      value_comment = request.POST.get("comment")
      if "value_from_input" in locals():
        if value_from_input != "" and value_monthly_amount != "":
          index_of_new_cathegory = request.user.member.attributes.count() + 1
          new_key = "cathegory" + str(index_of_new_cathegory)

          date_today = datetime.date.today()
          request.user.member.attributes.create(key=new_key, category=value_from_input,monthly_amount=value_monthly_amount, comment=value_comment, creation_date_of_the_category = date_today)
          attributes = request.user.member.attributes.all()
          creation_date =request.user.member.attributes.filter(key=new_key).values_list("creation_date_of_the_category", flat=True).first()


          past_months_since_deposit(attributes)
        else:
          attributes = request.user.member.attributes.all()
          past_months_since_deposit(attributes)
          attributes = "false"
      return redirect('dashboard')


    elif request.method == "GET":
      attributes = request.user.member.attributes.all()
      #past_months_since_deposit(attributes)
      return render(request, 'dashboard.html', {"attributes": attributes}) # html on left side / python on right side




