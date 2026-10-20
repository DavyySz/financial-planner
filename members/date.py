import datetime


def months_since(creation, today=None):
    """Seit wie vielen Monaten wird eingezahlt (Erstellungsmonat zaehlt mit)."""
    today = today or datetime.date.today()
    return (today.year - creation.year) * 12 + (today.month - creation.month) + 1
