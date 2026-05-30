from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
from datetime import date
from dateutil.relativedelta import relativedelta

from accounts_module.models import PHM_User
from infants_module.models import Infant
from clinic_module.models import GrowthRecord, ClinicSession, ScheduledVaccination
from ml_module.models import MLRiskAssessment
from django.db.models import Max


def get_moh_division(request):
    return request.user.moh_profile.moh_division


@login_required
def dashboard(request):
    division = get_moh_division(request)
    today = date.today()
    this_month_start = today.replace(day=1)

    # ── Infant population ────────────────────────────────────
    total_infants = Infant.objects.filter(moh_division=division).count()
    new_this_month = Infant.objects.filter(
        moh_division=division,
        created_at__date__gte=this_month_start
    ).count()
    male_count = Infant.objects.filter(moh_division=division, sex='M').count()
    female_count = Infant.objects.filter(moh_division=division, sex='F').count()

    # ── Latest ML risk counts ────────────────────────────────
    # Get the latest assessment per infant
    latest_ids = MLRiskAssessment.objects.filter(
        infant__moh_division=division
    ).values('infant').annotate(
        latest_id=Max('id')
    ).values_list('latest_id', flat=True)

    latest_assessments = MLRiskAssessment.objects.filter(id__in=latest_ids)
    sam_count = latest_assessments.filter(risk_level='SAM').count()
    mam_count = latest_assessments.filter(risk_level='MAM').count()
    normal_count = latest_assessments.filter(risk_level='NORMAL').count()
    assessed_count = sam_count + mam_count + normal_count

    # ── Vaccination coverage ─────────────────────────────────
    vac_total = ScheduledVaccination.objects.filter(
        infant__moh_division=division
    ).count()
    vac_administered = ScheduledVaccination.objects.filter(
        infant__moh_division=division,
        status='ADMINISTERED'
    ).count()
    vac_defaulted = ScheduledVaccination.objects.filter(
        infant__moh_division=division,
        status='DEFAULTED'
    ).count()

    coverage_rate = round((vac_administered / vac_total * 100), 1) if vac_total > 0 else 0

    # ── PHM activity ─────────────────────────────────────────
    phms = PHM_User.objects.filter(moh_division=division).annotate(
        infant_count=Count('registered_infants'),
        session_count=Count('clinic_sessions'),
    )

    # ── Clinic sessions ──────────────────────────────────────
    upcoming_sessions = ClinicSession.objects.filter(
        moh_division=division,
        session_date__gte=today,
        status='UPCOMING'
    ).order_by('session_date')[:5]

    sessions_this_month = ClinicSession.objects.filter(
        moh_division=division,
        session_date__gte=this_month_start,
        session_date__lte=today,
    ).count()

    # ── Growth monitoring ─────────────────────────────────────
    total_growth_records = GrowthRecord.objects.filter(
        infant__moh_division=division
    ).count()

    oedema_count = GrowthRecord.objects.filter(
        infant__moh_division=division,
        bilateral_pitting_oedema=True
    ).count()

    context = {
        'title': f'BlueCradle — MOH Dashboard · {division}',
        'division': division,
        'today': today,
        'total_infants': total_infants,
        'new_this_month': new_this_month,
        'male_count': male_count,
        'female_count': female_count,
        'sam_count': sam_count,
        'mam_count': mam_count,
        'normal_count': normal_count,
        'assessed_count': assessed_count,
        'vac_total': vac_total,
        'vac_administered': vac_administered,
        'vac_defaulted': vac_defaulted,
        'coverage_rate': coverage_rate,
        'phms': phms,
        'upcoming_sessions': upcoming_sessions,
        'sessions_this_month': sessions_this_month,
        'total_growth_records': total_growth_records,
        'oedema_count': oedema_count,
        'active_nav': 'dashboard',
    }
    return render(request, 'moh_module/dashboard.html', context)

@login_required
def nutrition(request):
    division = get_moh_division(request)

    latest_ids = MLRiskAssessment.objects.filter(
        infant__moh_division=division
    ).values('infant').annotate(
        latest_id=Max('id')
    ).values_list('latest_id', flat=True)

    latest_assessments = MLRiskAssessment.objects.filter(
        id__in=latest_ids
    ).select_related('infant')

    sam_count = latest_assessments.filter(risk_level='SAM').count()
    mam_count = latest_assessments.filter(risk_level='MAM').count()
    normal_count = latest_assessments.filter(risk_level='NORMAL').count()
    assessed_count = sam_count + mam_count + normal_count

    # SAM infants list
    sam_infants = latest_assessments.filter(
        risk_level='SAM'
    ).order_by('-assessed_at')

    # MAM infants list
    mam_infants = latest_assessments.filter(
        risk_level='MAM'
    ).order_by('-assessed_at')

    # Oedema cases
    oedema_cases = GrowthRecord.objects.filter(
        infant__moh_division=division,
        bilateral_pitting_oedema=True
    ).select_related('infant').order_by('-visit_date')

    context = {
        'title': f'BlueCradle — Nutritional Status · {division}',
        'division': division,
        'sam_count': sam_count,
        'mam_count': mam_count,
        'normal_count': normal_count,
        'assessed_count': assessed_count,
        'sam_infants': sam_infants,
        'mam_infants': mam_infants,
        'oedema_cases': oedema_cases,
        'active_nav': 'nutrition',
    }
    return render(request, 'moh_module/nutrition.html', context)

@login_required
def vaccination(request):
    division = get_moh_division(request)

    # Overall counts
    vac_qs = ScheduledVaccination.objects.filter(
        infant__moh_division=division
    )
    vac_total = vac_qs.count()
    vac_administered = vac_qs.filter(status='ADMINISTERED').count()
    vac_defaulted = vac_qs.filter(status='DEFAULTED').count()
    vac_pending = vac_qs.filter(status='PENDING').count()
    vac_contraindicated = vac_qs.filter(status='CONTRAINDICATED').count()
    coverage_rate = round((vac_administered / vac_total * 100), 1) if vac_total > 0 else 0

    # Per vaccine breakdown
    from django.db.models import Count
    vaccine_breakdown = vac_qs.values('vaccine_name').annotate(
        total=Count('id'),
        administered=Count('id', filter=Q(status='ADMINISTERED')),
        defaulted=Count('id', filter=Q(status='DEFAULTED')),
        pending=Count('id', filter=Q(status='PENDING')),
    ).order_by('vaccine_name')

    # Defaulted infants
    defaulted_vaccinations = vac_qs.filter(
        status='DEFAULTED'
    ).select_related('infant', 'infant__registered_phm').order_by('due_date')

    context = {
        'title': f'BlueCradle — Vaccination Coverage · {division}',
        'division': division,
        'vac_total': vac_total,
        'vac_administered': vac_administered,
        'vac_defaulted': vac_defaulted,
        'vac_pending': vac_pending,
        'vac_contraindicated': vac_contraindicated,
        'coverage_rate': coverage_rate,
        'vaccine_breakdown': vaccine_breakdown,
        'defaulted_vaccinations': defaulted_vaccinations,
        'active_nav': 'vaccination',
    }
    return render(request, 'moh_module/vaccination.html', context)

@login_required
def phm_activity(request):
    division = get_moh_division(request)

    from django.db.models import Count, Max

    phms = PHM_User.objects.filter(
        moh_division=division
    ).annotate(
        infant_count=Count('registered_infants', distinct=True),
        session_count=Count('clinic_sessions', distinct=True),
        growth_record_count=Count('registered_infants__growth_records', distinct=True),
        last_session_date=Max('clinic_sessions__session_date'),
    ).order_by('-infant_count')

    context = {
        'title': f'BlueCradle — PHM Activity · {division}',
        'division': division,
        'phms': phms,
        'active_nav': 'phm_activity',
    }
    return render(request, 'moh_module/phm_activity.html', context)

@login_required
def clinics(request):
    division = get_moh_division(request)
    today = date.today()
    this_month_start = today.replace(day=1)

    upcoming_sessions = ClinicSession.objects.filter(
        moh_division=division,
        session_date__gte=today,
        status='UPCOMING'
    ).select_related('phm').order_by('session_date')

    past_sessions = ClinicSession.objects.filter(
        moh_division=division,
        session_date__lt=today,
    ).select_related('phm').order_by('-session_date')[:20]

    sessions_this_month = ClinicSession.objects.filter(
        moh_division=division,
        session_date__gte=this_month_start,
        session_date__lte=today,
    ).count()

    total_sessions = ClinicSession.objects.filter(
        moh_division=division
    ).count()

    completed_sessions = ClinicSession.objects.filter(
        moh_division=division,
        status='COMPLETED'
    ).count()

    context = {
        'title': f'BlueCradle — Clinic Sessions · {division}',
        'division': division,
        'today': today,
        'upcoming_sessions': upcoming_sessions,
        'past_sessions': past_sessions,
        'sessions_this_month': sessions_this_month,
        'total_sessions': total_sessions,
        'completed_sessions': completed_sessions,
        'upcoming_count': upcoming_sessions.count(),
        'active_nav': 'clinics',
    }
    return render(request, 'moh_module/clinics.html', context)

import io
from django.http import FileResponse
from .reports import (
    generate_division_summary,
    generate_nutrition_report,
    generate_vaccination_report,
    generate_phm_activity_report,
)


@login_required
def moh_reports(request):
    division = get_moh_division(request)
    today = date.today()

    # Month options for PHM activity filter
    months = [
        (1, 'January'), (2, 'February'), (3, 'March'),
        (4, 'April'), (5, 'May'), (6, 'June'),
        (7, 'July'), (8, 'August'), (9, 'September'),
        (10, 'October'), (11, 'November'), (12, 'December'),
    ]

    context = {
        'title': f'BlueCradle — Reports · {division}',
        'division': division,
        'today': today,
        'months': months,
        'current_year': today.year,
        'years': range(today.year, today.year - 3, -1),
        'active_nav': 'reports',
    }
    return render(request, 'moh_module/reports.html', context)


@login_required
def download_division_summary(request):
    division = get_moh_division(request)
    today = date.today()
    buffer = generate_division_summary(division, today)
    filename = f"BlueCradle_DivisionSummary_{division}_{today.strftime('%Y%m%d')}.pdf"
    return FileResponse(buffer, as_attachment=True, filename=filename, content_type='application/pdf')


@login_required
def download_nutrition_report(request):
    division = get_moh_division(request)
    today = date.today()
    buffer = generate_nutrition_report(division, today)
    filename = f"BlueCradle_NutritionalStatus_{division}_{today.strftime('%Y%m%d')}.pdf"
    return FileResponse(buffer, as_attachment=True, filename=filename, content_type='application/pdf')


@login_required
def download_vaccination_report(request):
    division = get_moh_division(request)
    today = date.today()
    buffer = generate_vaccination_report(division, today)
    filename = f"BlueCradle_VaccinationCoverage_{division}_{today.strftime('%Y%m%d')}.pdf"
    return FileResponse(buffer, as_attachment=True, filename=filename, content_type='application/pdf')


@login_required
def download_phm_activity_report(request):
    division = get_moh_division(request)
    today = date.today()
    month = request.GET.get('month')
    year = request.GET.get('year')
    buffer = generate_phm_activity_report(division, today, month, year)
    filename = f"BlueCradle_PHMActivity_{division}_{today.strftime('%Y%m%d')}.pdf"
    return FileResponse(buffer, as_attachment=True, filename=filename, content_type='application/pdf')