from django.urls import reverse
from rest_framework import request, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from .models import GrowthRecord, ImmunizationEvent, ClinicSession, FHBAtomicEvent, ClinicSchedule, ScheduledVaccination
from .serializers import ClinicSessionSerializer, GrowthRecordSerializer, ImmunizationEventSerializer, FHBAtomicEventSerializer, ScheduledVaccinationSerializer, ScheduledVaccinationUpdateSerializer
from django.contrib.auth.decorators import login_required
from infants_module.models import Infant
from django.db import models
from datetime import date
from django.utils import timezone
from accounts_module.permission import IsPHM, IsParent
from .reporting_utils import generate_h523_data
from ml_module.models import MLRiskAssessment

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from clinic_module.models import ScheduledVaccination
from django.urls import reverse

@login_required
def phm_dashboard(request):
    phm = request.user.phm_profile
    today = date.today()
    first_of_month = today.replace(day=1)

    # Stat cards
    all_infants = Infant.objects.filter(registered_phm=phm)
    total_registered = all_infants.count()
    new_this_month = all_infants.filter(created_at__date__gte=first_of_month).count()

    vaccinations_due = ImmunizationEvent.objects.filter(
        infant__registered_phm=phm,
        dose_status='DEFAULTED',
        is_defaulter=False
    ).count()

    overdue_count = ImmunizationEvent.objects.filter(
        infant__registered_phm=phm,
        is_defaulter=True
    ).count()

    at_risk_count = MLRiskAssessment.objects.filter(
        infant__registered_phm=phm,
        risk_level__in=['SAM', 'MAM']
    ).values('infant').distinct().count()

    # Next clinic session
    next_clinic = ClinicSession.objects.filter(
        phm=phm,
        session_date__gte=today
    ).order_by('session_date').first()

    # Recent infants with assembled data
    recent_infants = []
    for infant in all_infants.order_by('-created_at')[:10]:
        latest_growth = GrowthRecord.objects.filter(
            infant=infant
        ).order_by('-visit_date').first()

        latest_ml = MLRiskAssessment.objects.filter(
            infant=infant
        ).order_by('-assessed_at').first()

        next_vaccine = ImmunizationEvent.objects.filter(
            infant=infant,
            dose_status='DEFAULTED',
            is_defaulter=False
        ).order_by('scheduled_date').first()

        # Calculate age display
        age_days = (today - infant.date_of_birth).days
        if age_days < 30:
            age_display = f"{age_days}d"
        elif age_days < 365:
            months = age_days // 30
            days = age_days % 30
            age_display = f"{months}m {days}d"
        else:
            years = age_days // 365
            months = (age_days % 365) // 30
            age_display = f"{years}y {months}m"

        recent_infants.append({
            'infant': infant,
            'age_display': age_display,
            'last_visit': latest_growth.visit_date if latest_growth else None,
            'who_classification': latest_growth.who_classification if latest_growth else 'NORMAL',
            'ml_risk': latest_ml.risk_level if latest_ml else 'NORMAL',
            'next_vaccine': next_vaccine.vaccine if next_vaccine else None,
        })

    # Active alerts
    active_alerts = []
    critical_events = FHBAtomicEvent.objects.filter(
        phm=phm,
        priority__in=['CRITICAL_HIGH', 'CRITICAL'],
        event_timestamp__date=today
    ).order_by('-event_timestamp')[:5]

    for event in critical_events:
        active_alerts.append({
            'priority': event.priority,
            'event_type_display': event.get_event_type_display(),
            'infant_name': event.infant.full_name,
            'phn': event.infant.phn,
        })

    # Unsynced count for sync status indicator
    unsynced_count = FHBAtomicEvent.objects.filter(
        phm=phm,
        is_synced=False
    ).count()

    context = {
        'title': 'BlueCradle - PHM Dashboard',
        'total_registered': total_registered,
        'new_this_month': new_this_month,
        'vaccinations_due': vaccinations_due,
        'overdue_count': overdue_count,
        'at_risk_count': at_risk_count,
        'next_clinic': next_clinic,
        'recent_infants': recent_infants,
        'active_alerts': active_alerts,
        'unsynced_count': unsynced_count,
        'today': timezone.now(),
        'active_nav': 'dashboard',
    }

    return render(
        request, 
        'clinic_module/dashboard.html', 
        context
    )


@login_required
def infant_register(request):
    if request.method == 'POST':
        phm = request.user.phm_profile
        data = request.POST

        if Infant.objects.filter(phn=data['phn']).exists():
            return redirect(f"{reverse('clinic:infant_register')}?error=duplicate_phn&phn={data['phn']}")

        Infant.objects.create(
            phn=data['phn'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            full_name=data['full_name'],
            date_of_birth=data['date_of_birth'],
            sex=data['sex'],
            birth_order=data['birth_order'],
            birth_weight_kg=data['birth_weight_kg'],
            birth_length_cm=data['birth_length_cm'],
            registered_phm=phm,
            moh_division=phm.moh_division,
        )
        return redirect(f"{reverse('clinic:dashboard')}?success=infant_registered&name={data['full_name']}")

    context = {
        'title': 'BlueCradle - Infant Registration',
        'active_nav': 'infants',
    }
    return render(request, 'clinic_module/infant_register.html', context)


@login_required
def infant_search(request):
    phm = request.user.phm_profile
    today = date.today()
    query = request.GET.get('q', '').strip()

    all_infants = Infant.objects.filter(registered_phm=phm)

    if query:
        all_infants = all_infants.filter(
            models.Q(full_name__icontains=query) |
            models.Q(phn__icontains=query)
        )

    infants = []
    risk_filter = request.GET.get('filter', None)

    for infant in all_infants.order_by('last_name', 'first_name'):
        latest_growth = GrowthRecord.objects.filter(
            infant=infant
        ).order_by('-visit_date').first()

        latest_ml = MLRiskAssessment.objects.filter(
            infant=infant
        ).order_by('-assessed_at').first()

        age_days = (today - infant.date_of_birth).days
        if age_days < 30:
            age_display = f"{age_days}d"
        elif age_days < 365:
            months = age_days // 30
            days = age_days % 30
            age_display = f"{months}m {days}d"
        else:
            years = age_days // 365
            months = (age_days % 365) // 30
            age_display = f"{years}y {months}m"

        if risk_filter == 'risk':
            # Sort SAM/MAM to top
            infants = sorted(infants, key=lambda x: 
                0 if x['who_classification'] == 'SAM' 
                else 1 if x['who_classification'] == 'MAM' 
                else 2
            )

        infants.append({
            'infant': infant,
            'age_display': age_display,
            'last_visit': latest_growth.visit_date if latest_growth else None,
            'who_classification': latest_growth.who_classification if latest_growth else 'NORMAL',
            'ml_risk': latest_ml.risk_level if latest_ml else 'NORMAL',
        })
 
    filter_type = request.GET.get('filter', None)
    context = {
        'title': 'BlueCradle - Infant Search',
        'infants': infants,
        'total_count': all_infants.count(),
        'query': query,
        'filter_type': filter_type,
        'active_nav': 'growth' if filter_type == 'risk' else 'vaccinations' if filter_type == 'defaulters' else 'infants',
    }
    return render(request, 'clinic_module/infant_search.html', context)


@login_required
def infant_detail(request, phn):
    phm = request.user.phm_profile
    today = date.today()

    infant = get_object_or_404(Infant, phn=phn, registered_phm=phm)

    growth_records = GrowthRecord.objects.filter(
        infant=infant
    ).order_by('-visit_date')

    latest_growth = growth_records.first()

    latest_ml = MLRiskAssessment.objects.filter(
        infant=infant
    ).order_by('-assessed_at').first()

    immunization_events = ImmunizationEvent.objects.filter(
        infant=infant
    ).order_by('scheduled_date')

    scheduled_vaccinations = ScheduledVaccination.objects.filter(
        infant=infant
    ).order_by('due_date')

    vac_pending = scheduled_vaccinations.filter(status=ScheduledVaccination.Status.PENDING).count()
    vac_administered = scheduled_vaccinations.filter(status=ScheduledVaccination.Status.ADMINISTERED).count()
    vac_defaulted = scheduled_vaccinations.filter(status=ScheduledVaccination.Status.DEFAULTED).count()
    vac_contraindicated = scheduled_vaccinations.filter(status=ScheduledVaccination.Status.CONTRAINDICATED).count()

    age_days = (today - infant.date_of_birth).days
    if age_days < 30:
        age_display = f"{age_days}d"
    elif age_days < 365:
        months = age_days // 30
        days = age_days % 30
        age_display = f"{months}m {days}d"
    else:
        years = age_days // 365
        months = (age_days % 365) // 30
        age_display = f"{years}y {months}m"

    tab = request.GET.get('tab', 'growth')
    context = {
        'title': 'BlueCradle - Infant Detail',
        'infant': infant,
        'age_display': age_display,
        'latest_growth': latest_growth,
        'growth_records': growth_records,
        'latest_ml': latest_ml,
        'immunization_events': immunization_events,
        'scheduled_vaccinations': scheduled_vaccinations,
        'vac_pending': vac_pending,
        'vac_administered': vac_administered,
        'vac_defaulted': vac_defaulted,
        'vac_contraindicated': vac_contraindicated,
        'active_tab': tab,
        'active_nav': 'vaccinations' if tab == 'vaccinations' else 'growth' if tab == 'growth' else 'infants',
    }
    return render(request, 'clinic_module/infant_detail.html', context)


@login_required
def growth_record(request, phn):
    phm = request.user.phm_profile
    today = date.today()
    infant = get_object_or_404(Infant, phn=phn, registered_phm=phm)

    sessions = ClinicSession.objects.filter(
        phm=phm
    ).order_by('-session_date')[:10]

    growth_records = GrowthRecord.objects.filter(
        infant=infant
    ).order_by('-visit_date')

    if request.method == 'POST':
        data = request.POST
        age_in_days = (date.fromisoformat(data['visit_date']) - infant.date_of_birth).days

        saved_record = GrowthRecord.objects.create(
            infant=infant,
            session_id=data['session'],
            visit_date=data['visit_date'],
            age_in_days=age_in_days,
            weight_kg=data['weight_kg'],
            height_cm=data['height_cm'],
            muac_mm=data.get('muac_mm') or None,
            whz=data.get('whz') or None,
            waz=data.get('waz') or None,
            haz=data.get('haz') or None,
            bilateral_pitting_oedema='bilateral_pitting_oedema' in data,
        )

        from ml_module.tasks import run_ml_risk_assessment
        run_ml_risk_assessment.delay(
            infant_phn=phn,
            growth_record_id=saved_record.id
        )

        return redirect(f"{reverse('clinic:infant_detail', args=[phn])}?success=growth_saved")

    context = {
        'title': 'BlueCradle - Add Growth Record',
        'infant': infant,
        'sessions': sessions,
        'growth_records': growth_records,
        'today': today,
        'active_nav': 'infants',
    }
    return render(request, 'clinic_module/growth_record.html', context)


@login_required
def immunization(request, phn):
    phm = request.user.phm_profile
    infant = get_object_or_404(Infant, phn=phn, registered_phm=phm)

    sessions = ClinicSession.objects.filter(
        phm=phm
    ).order_by('-session_date')[:10]

    immunization_events = ImmunizationEvent.objects.filter(
        infant=infant
    ).order_by('scheduled_date')

    if request.method == 'POST':
        data = request.POST
        dose_status = data['dose_status']

        # Check unique_together constraint
        if ImmunizationEvent.objects.filter(
            infant=infant,
            vaccine=data['vaccine']
        ).exists():
            return redirect(f"{reverse('clinic:immunization', args=[phn])}?error=duplicate_vaccine&vaccine={data['vaccine']}")

        ImmunizationEvent.objects.create(
            infant=infant,
            session_id=data['session'],
            vaccine=data['vaccine'],
            dose_status=dose_status,
            date_administered=data.get('date_administered') or None,
            batch_number=data.get('batch_number') or None,
            adverse_event_noted='adverse_event_noted' in data,
            adverse_event_details=data.get('adverse_event_details') or None,
            scheduled_date=data.get('scheduled_date') or None,
        )
        return redirect(f"{reverse('clinic:infant_detail', args=[phn])}?success=vaccine_saved&tab=vaccinations")

    context = {
        'title': 'BlueCradle - Add Immunization Event',
        'infant': infant,
        'sessions': sessions,
        'immunization_events': immunization_events,
        'vaccine_choices': ImmunizationEvent.VACCINE_CHOICES,
        # add these two:
        'vaccinations_due': ImmunizationEvent.objects.filter(
            infant__registered_phm=phm,
            dose_status='DEFAULTED',
            is_defaulter=False
        ).count(),
        'overdue_count': ImmunizationEvent.objects.filter(
            infant__registered_phm=phm,
            is_defaulter=True
        ).count(),
        'active_nav': 'infants',
    }
    return render(request, 'clinic_module/immunization.html', context)


@login_required
def h523_report(request):
    from datetime import datetime
    from .reporting_utils import generate_h523_data

    date_param = request.GET.get('date', None)
    selected_date = date_param or str(date.today())

    if date_param:
        try:
            target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        except ValueError:
            target_date = date.today()
    else:
        target_date = date.today()

    h523 = generate_h523_data(
        phm=request.user.phm_profile,
        target_date=target_date
    )

    context = {
        'title': 'BlueCradle - H 523 Report',
        'h523': h523,
        'selected_date': selected_date,
        'overdue_count': ImmunizationEvent.objects.filter(
            infant__registered_phm=request.user.phm_profile,
            is_defaulter=True
        ).count(),
        'defaulters': ImmunizationEvent.objects.filter(
            infant__registered_phm=request.user.phm_profile,
            is_defaulter=True
        ).select_related('infant').order_by('-defaulter_days_overdue'),
        'active_nav': 'reports'
    }
    return render(request, 'clinic_module/h523_report.html', context)

@login_required
def session_start(request):
    """
    Main clinic sessions page.
    Shows upcoming, active, and completed sessions in separate tabs.
    Also handles the annual schedule creation form.
    """
    from .models import ClinicSchedule
    from .schedule_utils import generate_sessions_from_schedule
    import json

    phm = request.user.phm_profile
    today = date.today()
    current_year = today.year

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        # ── Schedule form — RECURRING mode ───────────────────────────────────
        if form_type == 'recurring':
            existing = ClinicSchedule.objects.filter(
                phm=phm, year=current_year
            ).first()

            if existing:
                messages.error(request, f"A schedule for {current_year} already exists.")
            else:
                schedule = ClinicSchedule.objects.create(
                    phm=phm,
                    year=current_year,
                    session_type=request.POST.get('session_type', 'CLINIC'),
                    location=request.POST['location'],
                    schedule_mode='RECURRING',
                    first_date=request.POST['first_date'],
                    frequency_weeks=int(request.POST['frequency_weeks']),
                )
                count = generate_sessions_from_schedule(schedule)
                messages.success(
                    request,
                    f"Schedule created. {count} sessions generated for {current_year}."
                )
            return redirect('clinic:session_start')

        # ── Schedule form — FIXED_DATES mode ─────────────────────────────────
        elif form_type == 'fixed_dates':
            existing = ClinicSchedule.objects.filter(
                phm=phm, year=current_year
            ).first()

            if existing:
                messages.error(request, f"A schedule for {current_year} already exists.")
            else:
                raw_dates = request.POST.get('fixed_dates', '')
                # Expect comma-separated ISO dates: "2026-01-15,2026-02-19,..."
                date_list = [d.strip() for d in raw_dates.split(',') if d.strip()]

                schedule = ClinicSchedule.objects.create(
                    phm=phm,
                    year=current_year,
                    session_type=request.POST.get('session_type', 'CLINIC'),
                    location=request.POST['location'],
                    schedule_mode='FIXED_DATES',
                    fixed_dates=date_list,
                )
                count = generate_sessions_from_schedule(schedule)
                messages.success(
                    request,
                    f"Schedule created. {count} sessions generated for {current_year}."
                )
            return redirect('clinic:session_start')

    # ── Queries ───────────────────────────────────────────────────────────────
    upcoming_sessions = ClinicSession.objects.filter(
        phm=phm,
        status='UPCOMING',
        session_date__gte=today
    ).order_by('session_date')

    active_sessions = ClinicSession.objects.filter(
        phm=phm,
        status='ACTIVE'
    ).order_by('session_date')

    completed_sessions = ClinicSession.objects.filter(
        phm=phm,
        status='COMPLETED'
    ).order_by('-session_date')[:20]

    existing_schedule = ClinicSchedule.objects.filter(
        phm=phm,
        year=current_year
    ).first()

    first_of_month = today.replace(day=1)
    sessions_this_month = ClinicSession.objects.filter(
        phm=phm,
        session_date__gte=first_of_month,
        status='COMPLETED'
    ).count()

    context = {
        'title': 'BlueCradle - Clinic Sessions',
        'upcoming_sessions': upcoming_sessions,
        'active_sessions': active_sessions,
        'completed_sessions': completed_sessions,
        'existing_schedule': existing_schedule,
        'sessions_this_month': sessions_this_month,
        'current_year': current_year,
        'today': today,
        'active_nav': 'sessions',
        'unsynced_count': FHBAtomicEvent.objects.filter(
            phm=phm, is_synced=False
        ).count(),
    }
    return render(request, 'clinic_module/session_start.html', context)


@login_required
def session_activate(request, pk):
    """
    POST /clinic/phm/sessions/<pk>/activate/
    PHM starts today's session — flips status from UPCOMING to ACTIVE.
    """
    phm = request.user.phm_profile
    session = get_object_or_404(
        ClinicSession,
        pk=pk,
        phm=phm,
        status='UPCOMING'
    )
    session.status = 'ACTIVE'
    session.save(update_fields=['status'])
    messages.success(request, f"Session started — {session.session_date}.")
    return redirect('clinic:session_start')


@login_required
def session_complete(request, pk):
    """
    POST /clinic/phm/sessions/<pk>/complete/
    PHM closes the session at end of day — flips status from ACTIVE to COMPLETED.
    """
    phm = request.user.phm_profile
    session = get_object_or_404(
        ClinicSession,
        pk=pk,
        phm=phm,
        status='ACTIVE'
    )
    session.status = 'COMPLETED'
    session.save(update_fields=['status'])
    messages.success(request, f"Session completed — {session.session_date}.")
    return redirect('clinic:session_start')


@login_required
def session_manual_create(request):
    """
    POST /clinic/phm/sessions/manual/
    Fallback — allows PHM to manually create a one-off session
    (e.g. an unscheduled domiciliary visit) without a ClinicSchedule.
    """
    phm = request.user.phm_profile

    if request.method == 'POST':
        ClinicSession.objects.create(
            phm=phm,
            session_date=request.POST['session_date'],
            session_type=request.POST['session_type'],
            location=request.POST['location'],
            moh_division=phm.moh_division,
            status='UPCOMING',
        )
        messages.success(request, "Manual session created successfully.")
    return redirect('clinic:session_start')


@login_required
def h523_download_pdf(request):
    from .reporting_utils import generate_h523_data
    from datetime import datetime

    date_param = request.GET.get('date', None)
    if date_param:
        try:
            target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        except ValueError:
            target_date = date.today()
    else:
        target_date = date.today()

    h523 = generate_h523_data(
        phm=request.user.phm_profile,
        target_date=target_date
    )

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph("Form H 523 — Daily Work Return", styles['Title']))
    elements.append(Spacer(1, 12))

    # Header info
    header_data = [
        ['PHM Officer', h523['phm_name']],
        ['MOH Division', h523['moh_division']],
        ['Report Date', h523['report_date']],
    ]
    header_table = Table(header_data, colWidths=[150, 300])
    header_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 20))

    # H 523 Matrix
    data = [
        ['Service Category', 'FHB Code', 'Count'],
        ['New Registrations', 'NEW_REG', h523['new_registrations']],
        ['Growth Monitoring Attendance', 'GM_ATTENDANCE', h523['growth_monitoring_attendance']],
        ['Vaccinations Administered (EPI 3/79)', 'EPI_VACCINATION', h523['vaccinations_administered']],
        ['Defaulters Flagged / Missed Clinic', 'MISSED_CLINIC', h523['defaulters_flagged']],
        ['Postnatal Visits — First 10 Days', 'POSTNATAL_10', h523['postnatal_visits_10_days']],
        ['Postnatal Visits — 42 Days', 'POSTNATAL_42', h523['postnatal_visits_42_days']],
        ['Malnutrition / Low Birth Weight Flags', 'MALNUTRITION_FLAG', h523['malnutrition_flags']],
    ]
    table = Table(data, colWidths=[280, 130, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#002444')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ALIGN', (2,0), (2,-1), 'RIGHT'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f0f4f8')]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#c3c6cf')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 30))

    # Certification
    elements.append(Paragraph(
        f"I certify that the above is a true and correct record of work performed on {h523['report_date']}.",
        styles['Normal']
    ))
    elements.append(Spacer(1, 40))
    elements.append(Paragraph("_________________________", styles['Normal']))
    elements.append(Paragraph(f"Signature of PHM Officer: {h523['phm_name']}", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="H523_{h523["report_date"]}.pdf"'
    return response

@login_required
def alerts(request):
    phm = request.user.phm_profile
    filter_type = request.GET.get('filter', 'all')

    # ML Risk alerts
    ml_alerts = MLRiskAssessment.objects.filter(
        infant__registered_phm=phm,
        risk_level__in=['SAM', 'MAM']
    ).select_related('infant').order_by('-assessed_at')

    # Defaulter alerts
    defaulter_alerts = ImmunizationEvent.objects.filter(
        infant__registered_phm=phm,
        is_defaulter=True
    ).select_related('infant').order_by('-defaulter_days_overdue')

    # Missed visit alerts (no growth record in last 45 days)
    from datetime import timedelta
    cutoff = date.today() - timedelta(days=45)
    all_infants = Infant.objects.filter(registered_phm=phm)
    missed_visits = []
    for infant in all_infants:
        latest = GrowthRecord.objects.filter(infant=infant).order_by('-visit_date').first()
        if latest and latest.visit_date < cutoff:
            missed_visits.append({
                'infant': infant,
                'last_visit': latest.visit_date,
                'days_since': (date.today() - latest.visit_date).days
            })

    context = {
        'title': 'BlueCradle - Alerts',
        'active_nav': 'alerts',
        'ml_alerts': ml_alerts,
        'defaulter_alerts': defaulter_alerts,
        'missed_visits': missed_visits,
        'filter_type': filter_type,
        'total_count': ml_alerts.count() + defaulter_alerts.count() + len(missed_visits),
    }
    return render(request, 'clinic_module/alerts.html', context)


class ClinicSessionListCreateView(APIView):
    permission_classes = [IsPHM]

    def get(self, request):
        # Return all sessions belonging to the logged-in PHM.
        sessions = ClinicSession.objects.filter(
            phm=request.user.phm_profile
        )
        serializer = ClinicSessionSerializer(sessions, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ClinicSessionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                phm=request.user.phm_profile,
                moh_division=request.user.phm_profile.moh_division
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClinicSessionDetailView(APIView):
    permission_classes = [IsPHM]

    def get_object(self, pk, request):
        return get_object_or_404(
            ClinicSession,
            pk=pk,
            phm=request.user.phm_profile
        )

    def get(self, request, pk):
        session = self.get_object(pk, request)
        serializer = ClinicSessionSerializer(session)
        return Response(serializer.data)

    def patch(self, request, pk):
        session = self.get_object(pk, request)
        serializer = ClinicSessionSerializer(session, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GrowthRecordListCreateView(APIView):
    permission_classes = [IsPHM]

    def get(self, request, phn):
        # Return full growth history for one infant — feeds the chart.
        records = GrowthRecord.objects.filter(
            infant__phn=phn,
            infant__registered_phm=request.user.phm_profile
        ).order_by('visit_date')
        serializer = GrowthRecordSerializer(records, many=True)
        return Response(serializer.data)

    def post(self, request, phn):
        serializer = GrowthRecordSerializer(data=request.data)
        if serializer.is_valid():
            saved_record = serializer.save()  
            
            # Rquires Redis
            from ml_module.tasks import run_ml_risk_assessment
            run_ml_risk_assessment.delay(
                infant_phn=phn,
                growth_record_id=saved_record.id
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ImmunizationEventListCreateView(APIView):
    permission_classes = [IsPHM]

    def get(self, request, phn):
        # Return full immunization history for one infant.
        records = ImmunizationEvent.objects.filter(
            infant__phn=phn,
            infant__registered_phm=request.user.phm_profile
        ).order_by('scheduled_date')
        serializer = ImmunizationEventSerializer(records, many=True)
        return Response(serializer.data)

    def post(self, request, phn):
        serializer = ImmunizationEventSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ImmunizationEventDetailView(APIView):
    permission_classes = [IsPHM]

    def get_object(self, pk, request):
        return get_object_or_404(
            ImmunizationEvent,
            pk=pk,
            infant__registered_phm=request.user.phm_profile
        )

    def get(self, request, pk):
        record = self.get_object(pk, request)
        serializer = ImmunizationEventSerializer(record)
        return Response(serializer.data)

    def patch(self, request, pk):
        record = self.get_object(pk, request)
        serializer = ImmunizationEventSerializer(record, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class FHBAtomicEventCreateView(APIView):
    permission_classes = [IsPHM]

    def post(self, request):
        serializer = FHBAtomicEventSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                phm=request.user.phm_profile,
                moh_division=request.user.phm_profile.moh_division
            )
            return Response({'status': 'synced'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class H523ReportView(APIView):
    permission_classes = [IsPHM]

    def get(self, request):
        # Optional date parameter — defaults to today.
        # Allows PHM to regenerate a previous day's return if needed.
        from datetime import datetime
        date_param = request.query_params.get('date', None)

        if date_param:
            try:
                target_date = datetime.strptime(date_param, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {"error": "Invalid date format. Use YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            target_date = None

        h523_data = generate_h523_data(
            phm=request.user.phm_profile,
            target_date=target_date
        )
        return Response(h523_data, status=status.HTTP_200_OK)
    
import csv
from django.http import HttpResponse

class ScheduledVaccinationListView(APIView):
    permission_classes = [IsPHM | IsParent]

    def get(self, request, phn):
        infant = get_object_or_404(Infant, phn=phn)

        # Ownership check
        if hasattr(request.user, 'phm_profile'):
            if infant.registered_phm != request.user.phm_profile:
                return Response(
                    {'detail': 'You do not have access to this infant.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif hasattr(request.user, 'parent_profile'):
            if request.user.parent_profile.phn != phn:
                return Response(
                    {'detail': 'You do not have access to this infant.'},
                    status=status.HTTP_403_FORBIDDEN
                )

        vaccinations = ScheduledVaccination.objects.filter(infant=infant)
        serializer = ScheduledVaccinationSerializer(vaccinations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ScheduledVaccinationUpdateView(APIView):
    permission_classes = [IsPHM]

    def patch(self, request, phn, pk):
        infant = get_object_or_404(Infant, phn=phn)

        # PHM ownership check
        if infant.registered_phm != request.user.phm_profile:
            return Response(
                {'detail': 'You do not have access to this infant.'},
                status=status.HTTP_403_FORBIDDEN
            )

        vaccination = get_object_or_404(
            ScheduledVaccination,
            pk=pk,
            infant=infant
        )

        serializer = ScheduledVaccinationUpdateSerializer(
            vaccination,
            data=request.data,
            partial=True
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if serializer.validated_data.get('status') == ScheduledVaccination.Status.ADMINISTERED:
            serializer.save(administered_by=request.user)
        else:
            serializer.save()

        return Response(
            ScheduledVaccinationSerializer(vaccination).data,
            status=status.HTTP_200_OK
        )