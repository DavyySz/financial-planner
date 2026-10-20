"""Berechnung der eingezahlten Monatsraten einer Kategorie."""
import datetime
from decimal import Decimal


def months_between(start_year, start_month, end_year, end_month):
    """Anzahl Monate von (start_year, start_month) bis (end_year, end_month)."""
    return (end_year - start_year) * 12 + (end_month - start_month)


def total_amount_of_monthly_payments(history, today=None):
    """Summe aller bisher eingezahlten Monatsraten.

    history ist eine Liste von (betrag, jahr, monat), aelteste zuerst. Jeder
    Eintrag wird ab seinem Monat jeden Monat eingezahlt, bis der naechste
    Eintrag beginnt; der letzte Eintrag laeuft bis heute (inklusive des
    aktuellen Monats).
    """
    today = today or datetime.date.today()
    total = Decimal("0")
    for i, (amount, year, month) in enumerate(history):
        if i + 1 < len(history):
            _, next_year, next_month = history[i + 1]
            months = months_between(year, month, next_year, next_month)
        else:
            months = months_between(year, month, today.year, today.month) + 1
        total += max(months, 0) * Decimal(str(amount))
    return total
