from django.db.models import Count
from .models import FHBAtomicEvent
from datetime import date


def generate_h523_data(phm, target_date=None):
    """
    Aggregates FHBAtomicEvents for a given PHM on a given date
    and maps them to the H 523 matrix columns.
    """
    if target_date is None:
        target_date = date.today()

    events = FHBAtomicEvent.objects.filter(
        phm=phm,
        event_timestamp__date=target_date
    ).values('fhb_service_code').annotate(count=Count('id'))

    # Map service codes to H 523 column names
    H523_COLUMN_MAP = {
        'NEW_REG':          'new_registrations',
        'GM_ATTENDANCE':    'growth_monitoring_attendance',
        'EPI_VACCINATION':  'vaccinations_administered',
        'MISSED_CLINIC':    'defaulters_flagged',
        'POSTNATAL_10':     'postnatal_visits_10_days',
        'POSTNATAL_42':     'postnatal_visits_42_days',
        'MALNUTRITION_FLAG':'malnutrition_flags',
    }

    # Initialize all columns to zero.
    h523: dict = {col: 0 for col in H523_COLUMN_MAP.values()}

    # Fill in counts from the query.
    for event in events:
        column = H523_COLUMN_MAP.get(event['fhb_service_code'])
        if column:
            h523[column] = event['count']

    h523['phm_name'] = phm.full_name
    h523['moh_division'] = phm.moh_division
    h523['report_date'] = str(target_date)

    return h523