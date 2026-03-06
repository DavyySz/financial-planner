
from pdb import find_function
from unicodedata import category

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
from .Calculate_monthly_payments import Calculate_monthly_payments
from .Check_whether_category_is_duplicated import Check_whether_category_is_duplicated
from django.contrib.postgres.fields import ArrayField
from decimal import Decimal


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
    #attributes = request.user.member.attributes.all()

    if request.method == "POST":


      if len(request.POST.get("category_name")) <= 25 and request.POST.get("monthly_amount") != "":
        value_from_input = request.POST.get("category_name")
        value_monthly_amount = Decimal(request.POST.get("monthly_amount"))
        value_comment = request.POST.get("comment")
        id_of_user = int(request.POST.get("id_of_user"))

      else:
        return HttpResponse('<script>alert("FEHLER! Der Kategoriename darf maximal 25 Zeichen lang sein und keine Zahlen enthalten. Der Betrag darf keine Buchstaben enthalten. Name und monatliche Einzahlung dürfen nicht leer sein. Der Kommentar ist optional."); window.history.back();</script>')


      if "value_from_input" in locals():
        duplicate_variable = Check_whether_category_is_duplicated(value_from_input)
        if duplicate_variable == False:
          return HttpResponse('<script>alert("Kategorien dürfen nicht doppelt sein"); window.history.back();</script>')
        if value_from_input != "" and value_monthly_amount != "":
          index_of_new_cathegory = request.user.member.attributes.count() + 1
          new_key = "cathegory" + str(index_of_new_cathegory)

          date_today = datetime.date.today()
          request.user.member.attributes.create(key=new_key, category=value_from_input, monthly_amount=[value_monthly_amount], comment=value_comment, creation_date_of_the_category = date_today, index_monthly_amount = 0)
          attributes = request.user.member.attributes.all()

          past_months_since_deposit(attributes.order_by("id"))
          #Calculate_monthly_payments(attributes)
          return redirect("dashboard")


    elif request.method == "GET":

      attributes = request.user.member.attributes.order_by("id")
      Calculate_monthly_payments(attributes.order_by("id"))
      past_months_since_deposit(attributes.order_by("id"))

      return render(request, 'dashboard.html', {"attributes": attributes}) # html on left side / python on right side



@login_required
def change_data(request):

  if request.GET.get("monthly_amount_new"): # if the user is clicking on the linkt of the category
    attributes = request.user.member.attributes.all()
    monthly_amount_new = request.GET.get("monthly_amount_new") # new amount of money the user wants to use in the future
    comment_change =request.GET.get("comment_change") # comment for the change (optional for the user)
    category_string = request.GET.get("category_string")# name of the category
    date_today = datetime.date.today()

    category_picked = request.user.member.attributes.values_list("key", flat=True).get(category=category_string)  # key
    #index_this_moment = request.user.member.attributes.values_list("index_monthly_amount", flat=True).get(category=category_string)

    r = request.user.member.attributes.get(key=category_picked)
    r.monthly_amount.append(monthly_amount_new)
    # r.monthly_amount[index_after_change] = monthly_amount_new
    request.user.member.save()
    r.save()
    index_after_change = len(request.user.member.attributes.values_list("monthly_amount", flat=True).get(key=category_picked)) - 1
    r.index_monthly_amount = index_after_change
    request.user.member.save()
    r.save()
    Calculate_monthly_payments(attributes)

    #Calculate_new_monthly_payments(attributes, monthly_amount_new, comment_change, category_string, date_today, category_picked, index_this_moment, index_after_change)


    template = loader.get_template('change_data.html')

  if request.GET.get("category"): # if the user wants to change the money amount fot a specific category
    category_string = request.GET.get("category")
    attributes = request.user.member.attributes.all()

    category_picked = request.user.member.attributes.values_list("key",flat=True).get(category=category_string)


    template = loader.get_template('change_data.html')


  if "category_string" in locals() and "category_picked" in locals() and "attributes" in locals(): # if the user wants to change the money amount fot a specific category
    return render(request, 'change_data.html', {"category_string": category_string, "category_picked": category_picked, "attributes": attributes})
  elif "monthly_amount_new" in locals(): # if the user is clicking on the linkt of the category
    return render(request, 'change_data.html',{"monthly_amount_new": monthly_amount_new, "comment_change": comment_change, "category_picked": category_picked})


