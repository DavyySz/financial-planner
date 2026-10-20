from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/change_data/', views.change_data, name='change_data'),
    path('dashboard/delete/', views.delete_category, name='delete_category'),
    path('dashboard/transaction/', views.add_transaction, name='add_transaction'),
    path('dashboard/transaction/delete/', views.delete_transaction, name='delete_transaction'),
    path('dashboard/salary/', views.set_salary, name='set_salary'),
    path('passwort-vergessen/', views.password_request, name='password_request'),
    path('adminboard/', views.adminboard, name='adminboard'),
]
