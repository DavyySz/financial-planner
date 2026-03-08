import time
from symtable import Class
import datetime
from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.http import HttpResponse
from django.template import loader
from django.shortcuts import render
from django.contrib import messages



def Calculate_monthly_payments(attributes):
    for x in attributes:
        x.monthly_amount_value = float(x.monthly_amount[-1][0])
        time.sleep(0.01)
        x.save()
        continue

def total_amount_of_monthly_payments(attributes):
    for x in attributes:
        if len(x.monthly_amount) == 1:
            all = total_paid_in = float(x.monthly_amount[0][0])
            x.total_monthly_payments = all
            x.save()
            continue

        date_today = datetime.date.today()
        actual_month = date_today.month
        actual_year = date_today.year
        money_amount_now = float(x.monthly_amount[-1][0])
        all = 0
        last_iteration = 1
        length = len(x.monthly_amount)-1
        while length > 1:
            last_date_year = x.monthly_amount[length][1]
            last_date_month = x.monthly_amount[length][2]
            date_before_year = x.monthly_amount[length-1][1]
            date_before_month = x.monthly_amount[length - 1][2]
            money_before_month = x.monthly_amount[length - 1][0]
            length = length - 1

            if last_iteration == 1:
                if (actual_year - last_date_year) > 1:
                    amount = actual_month + (((actual_year - last_date_year) - 1) * 12) +  (12 - last_date_month + 1)
                    all = all + (float(amount) * money_amount_now)
                elif (actual_year - last_date_year) == 0:
                    amount = actual_month - last_date_month + 1
                    all = all + (float(amount) * money_amount_now)
                elif (actual_year - last_date_year) == 1:
                    amount = actual_month + (12 - last_date_month + 1)
                    all = all + (float(amount) * money_amount_now)

                length = length + 1
                last_iteration = 0


            elif last_iteration == 0:
                if (last_date_year - date_before_year) > 1:
                    amount = (last_date_month - 1) + (((last_date_year - date_before_year) - 1) * 12) +  (12 - date_before_month + 1)
                    all = all + (float(amount) * money_amount_now)
                elif (last_date_year - date_before_year) == 0:
                    amount = last_date_month - date_before_month
                    all = all + (float(amount) * money_amount_now)
                elif (last_date_year - date_before_year) == 1:
                    amount = (last_date_month - 1) + (12 - date_before_month + 1)
                    all = all + (float(amount) * money_amount_now)
                if length == 1:
                    start_date_year = x.monthly_amount[0][1]
                    start_date_month = x.monthly_amount[0][2]
                    start_date_before_year = x.monthly_amount[1][1]
                    start_date_before_month = x.monthly_amount[1][2]
                    start_money_before_month = x.monthly_amount[length - 1][0]

                    if (start_date_before_year - start_date_year) == 1:
                        amount = (12 - start_date_month + 1) + (start_date_before_month - 1)
                        all = all + (float(amount) * money_amount_now)
                    elif (start_date_before_year - start_date_year) > 1:
                        amount = (12 - start_date_month + 1) + (((start_date_before_year - start_date_year) - 1) * 12) + (start_date_before_month - 1)
                        all = all + (float(amount) * money_amount_now)
                    elif (start_date_year - start_date_before_year) == 0:
                        amount = start_date_before_month - start_date_month
                        all = all + (float(amount) * money_amount_now)

        x.total_monthly_payments = all
        x.save()



def calculate_full_money_amount(attributes, category_name, new_amount):
    if category_name == False and new_amount == False:
        for x in attributes:
            x.new_amount = float(x.total_monthly_payments)
    else:
        category_name_ = category_name
        new_amount_ = new_amount
        is_There = False
        for x in attributes:
            if category_name_ == x.category:
                x.new_amount = float(new_amount_) + float(x.total_monthly_payments)
                x.save()
                is_there = True
            else:
                x.new_amount = float(x.total_monthly_payments)

    if is_there == False:
        return False
    elif is_there == True:
        return True













