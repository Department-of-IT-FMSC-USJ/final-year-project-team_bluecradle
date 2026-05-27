import math
from datetime import date

def classify_who(whz, muac_mm=None, oedema=False):
    """
    Apply WHO thresholds to return SAM / MAM / NORMAL.
    Oedema overrides everything.
    """
    if oedema:
        return 'SAM'
    if muac_mm is not None:
        if muac_mm < 115:
            return 'SAM'
        if 115 <= muac_mm < 125:
            return 'MAM'
    if whz is not None:
        if whz < -3:
            return 'SAM'
        if -3 <= whz < -2:
            return 'MAM'
    return 'NORMAL'

def get_grace_period_days(date_of_birth, scheduled_date):
    """
    Returns the correct grace period in days based on
    the infant's age at the scheduled vaccination date.
    Under 12 months — 14 days.
    12 months and over — 30 days.
    """
    age_in_days = (scheduled_date - date_of_birth).days
    age_in_months = age_in_days / 30.44

    if age_in_months < 12:
        return 14
    return 30


def is_defaulter(date_of_birth, scheduled_date, today=None):
    """
    Returns True if the vaccine is overdue beyond the grace period.
    """
    if today is None:
        today = date.today()

    grace_period = get_grace_period_days(date_of_birth, scheduled_date)
    days_overdue = (today - scheduled_date).days

    return days_overdue > grace_period