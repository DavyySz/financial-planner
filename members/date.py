import datetime
from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

def past_months_since_deposit(attributes):

    for x in attributes:
        date_this_moment = datetime.date.today()

        x.date_now = date_this_moment
        x.save()

        if (x.date_now.year - x.creation_date_of_the_category.year) == 0: # if it is the same year since the category was created
            past_months_since_deposit = (x.creation_date_of_the_category.month - date_this_moment.month) + 1

        elif (x.date_now.year - x.creation_date_of_the_category.year) == 1: # if it is the next year since the category was created
            months_to_next_year = (12 - x.creation_date_of_the_category.month) + 1
            months_in_the_current_year = date_this_moment.month
            past_months_since_deposit = months_to_next_year + months_in_the_current_year

        elif (x.date_now.year - x.creation_date_of_the_category.year) >= 2: # if at least 2 years have passed since the category was created
            full_months_from_creation_to_the_next_full_year = (12 - x.creation_date_of_the_category.month) + 1

            full_months_since_creation_in_full_years = ((x.date_now.year - x.creation_date_of_the_category.year) - 1) * 12
            full_months_form_last_full_year_to_date_now = x.date_now.month

            past_months_since_deposit = full_months_from_creation_to_the_next_full_year + full_months_since_creation_in_full_years + full_months_form_last_full_year_to_date_now


        x.How_many_months_have_passed_since_the_category_was_created = past_months_since_deposit
        x.save()

    return 0


def calculate_total_amount_of_monthly_payments(attributes):
    for x in attributes:
        pass