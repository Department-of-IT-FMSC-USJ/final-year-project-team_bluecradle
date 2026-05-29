from datetime import timedelta, date
from django.db import transaction


def generate_sessions_from_schedule(schedule):
    """
    Generates ClinicSession records for a full year from a ClinicSchedule.
    Called immediately after a ClinicSchedule is saved.
    Skips dates that already have a session for this PHM.
    Returns the count of sessions created.
    """
    from .models import ClinicSession

    dates_to_create = _resolve_dates(schedule)

    if not dates_to_create:
        return 0

    # Find which dates already have a session for this PHM
    # to avoid duplicates if the function is called twice
    existing_dates = set(
        ClinicSession.objects.filter(
            phm=schedule.phm,
            session_date__in=dates_to_create
        ).values_list('session_date', flat=True)
    )

    sessions = []
    for session_date in dates_to_create:
        if session_date in existing_dates:
            continue
        sessions.append(
            ClinicSession(
                phm=schedule.phm,
                schedule=schedule,
                session_date=session_date,
                session_type=schedule.session_type,
                location=schedule.location,
                moh_division=schedule.phm.moh_division,
                status='UPCOMING',
            )
        )

    with transaction.atomic():
        ClinicSession.objects.bulk_create(sessions)

    return len(sessions)


def _resolve_dates(schedule):
    # Returns a list of date objects based on the schedule mode.
        # RECURRING — generates dates from first_date by frequency_weeks until year end.
        # FIXED_DATES — parses the stored JSON date list.

    from datetime import date
    import datetime

    year_end = date(schedule.year, 12, 31)
    dates = []

    if schedule.schedule_mode == 'RECURRING':
        if not schedule.first_date or not schedule.frequency_weeks:
            return []

        # Ensure first_date is a date object — may be a string if calle immediately after create() before Django refreshes from DB
        first = schedule.first_date
        if isinstance(first, str):
            first = date.fromisoformat(first)

        current = first    
        while current <= year_end:
            if current.year == schedule.year:
                dates.append(current)
            current += timedelta(weeks=schedule.frequency_weeks)

    elif schedule.schedule_mode == 'FIXED_DATES':
        if not schedule.fixed_dates:
            return []

        for date_str in schedule.fixed_dates:
            try:
                parsed = date.fromisoformat(date_str)
                if parsed.year == schedule.year:
                    dates.append(parsed)
            except (ValueError, TypeError):
                continue

    return sorted(dates)