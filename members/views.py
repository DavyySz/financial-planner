from django.http import HttpResponse
from django.template import loader
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Member

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
    value_for_cathegory=""
    if request.method == "POST":
      value_from_input = request.POST.get("fname")
      index_of_new_cathegory = request.user.member.attributes.count() + 1
      new_key = "cathegory" + str(index_of_new_cathegory)
      request.user.member.attributes.create(key=new_key, value=value_from_input)
      if request.user.member.attributes.filter(key__contains="cathegory").exists():
        print("es gibt schon Kathegorien")
      else:
        print("es gibt noch keine Kathegorien")
      value_for_cathegory = request.user.member.attributes.get(key=new_key).value
    return render(request, 'dashboard.html', {"value_from_input": value_for_cathegory}) #html on left side / python on right side 