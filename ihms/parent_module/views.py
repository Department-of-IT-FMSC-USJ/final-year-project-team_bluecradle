from django.shortcuts import get_object_or_404
from infants_module.models import Infant
from clinic_module.models import GrowthRecord, ClinicSession, ScheduledVaccination
from ml_module.models import MLRiskAssessment
from notifications_module.models import NotificationLog
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import date, datetime
from django.utils import timezone

import io
from django.http import FileResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

@login_required
def dashboard_page(request):
    parent = request.user.parent_profile
    infant = get_object_or_404(Infant, phn=parent.phn)
    today = date.today()

    growth_records = GrowthRecord.objects.filter(infant=infant).order_by('-visit_date')
    latest_growth = growth_records.first()
    latest_ml = MLRiskAssessment.objects.filter(infant=infant).order_by('-assessed_at').first()

    next_clinic_session = ClinicSession.objects.filter(
        phm=infant.registered_phm,
        session_date__gte=today,
        status='UPCOMING'
    ).order_by('session_date').first()

    scheduled_vaccinations = ScheduledVaccination.objects.filter(infant=infant).order_by('due_date')

    next_vaccine = scheduled_vaccinations.filter(
        status=ScheduledVaccination.Status.PENDING,
        due_date__gte=today
    ).order_by('due_date').first()

    days_until_next_vaccine = (next_vaccine.due_date - today).days if next_vaccine else None

    unread_count = NotificationLog.objects.filter(
        recipient=request.user, is_read=False
    ).count()

    vac_administered = scheduled_vaccinations.filter(status=ScheduledVaccination.Status.ADMINISTERED).count()
    vac_pending = scheduled_vaccinations.filter(status=ScheduledVaccination.Status.PENDING).count()
    vac_defaulted = scheduled_vaccinations.filter(status=ScheduledVaccination.Status.DEFAULTED).count()
    vac_contraindicated = scheduled_vaccinations.filter(status=ScheduledVaccination.Status.CONTRAINDICATED).count()

    age_days = (today - infant.date_of_birth).days
    if age_days < 30:
        age_display = f"{age_days}d"
    elif age_days < 365:
        months = age_days // 30
        days_rem = age_days % 30
        age_display = f"{months}m {days_rem}d"
    else:
        years = age_days // 365
        months = (age_days % 365) // 30
        age_display = f"{years}y {months}m"

    hour = datetime.now().hour
    if hour < 12:
        greeting = 'Good morning'
    elif hour < 17:
        greeting = 'Good afternoon'
    else:
        greeting = 'Good evening'

    context = {
        'title': f'BlueCradle — {infant.full_name}',
        'infant': infant,
        'parent': parent,
        'age_display': age_display,
        'greeting': greeting,
        'latest_growth': latest_growth,
        'growth_records': growth_records,
        'latest_ml': latest_ml,
        'next_clinic_session': next_clinic_session,
        'next_vaccine': next_vaccine,
        'days_until_next_vaccine': days_until_next_vaccine,
        'unread_count': unread_count,
        'scheduled_vaccinations': scheduled_vaccinations,
        'vac_administered': vac_administered,
        'vac_pending': vac_pending,
        'vac_defaulted': vac_defaulted,
        'vac_contraindicated': vac_contraindicated,
        'vaccines_up_to_date': vac_defaulted == 0,
        'active_nav': 'dashboard',
        'today': today,
    }
    return render(request, 'parent_module/dashboard.html', context)


@login_required
def growth_page(request):
    parent = request.user.parent_profile
    infant = get_object_or_404(Infant, phn=parent.phn)
    today = date.today()

    growth_records = GrowthRecord.objects.filter(infant=infant).order_by('-visit_date')
    latest_growth = growth_records.first()
    latest_ml = MLRiskAssessment.objects.filter(infant=infant).order_by('-assessed_at').first()

    age_days = (today - infant.date_of_birth).days
    if age_days < 30:
        age_display = f"{age_days}d"
    elif age_days < 365:
        age_display = f"{age_days // 30}m"
    else:
        age_display = f"{age_days // 365}y"

    context = {
        'title': 'BlueCradle — Growth Monitoring',
        'infant': infant,
        'parent': parent,
        'age_display': age_display,
        'latest_growth': latest_growth,
        'growth_records': growth_records,
        'latest_ml': latest_ml,
        'active_nav': 'growth',
    }
    return render(request, 'parent_module/growth.html', context)


@login_required
def vaccinations_page(request):
    parent = request.user.parent_profile
    infant = get_object_or_404(Infant, phn=parent.phn)

    scheduled_vaccinations = ScheduledVaccination.objects.filter(infant=infant).order_by('due_date')

    context = {
        'title': 'BlueCradle — Vaccinations',
        'infant': infant,
        'parent': parent,
        'scheduled_vaccinations': scheduled_vaccinations,
        'vac_administered': scheduled_vaccinations.filter(status=ScheduledVaccination.Status.ADMINISTERED).count(),
        'vac_pending': scheduled_vaccinations.filter(status=ScheduledVaccination.Status.PENDING).count(),
        'vac_defaulted': scheduled_vaccinations.filter(status=ScheduledVaccination.Status.DEFAULTED).count(),
        'vac_contraindicated': scheduled_vaccinations.filter(status=ScheduledVaccination.Status.CONTRAINDICATED).count(),
        'active_nav': 'vaccinations',
    }
    return render(request, 'parent_module/vaccinations.html', context)


@login_required
def clinic_sessions_page(request):
    parent = request.user.parent_profile
    infant = get_object_or_404(Infant, phn=parent.phn)
    today = date.today()

    context = {
        'title': 'BlueCradle — Clinic Sessions',
        'infant': infant,
        'parent': parent,
        'upcoming_sessions': ClinicSession.objects.filter(
            phm=infant.registered_phm,
            session_date__gte=today,
            status='UPCOMING'
        ).order_by('session_date'),
        'past_sessions': ClinicSession.objects.filter(
            phm=infant.registered_phm,
            session_date__lt=today,
        ).order_by('-session_date')[:10],
        'active_nav': 'sessions',
    }
    return render(request, 'parent_module/clinic_sessions.html', context)


@login_required
def notifications_page(request):
    notifications = NotificationLog.objects.filter(
        recipient=request.user
    ).order_by('-created_at')

    context = {
        'title': 'BlueCradle — Notifications',
        'parent': request.user.parent_profile,
        'notifications': notifications,
        'unread_count': notifications.filter(is_read=False).count(),
        'active_nav': 'notifications',
    }
    return render(request, 'parent_module/notifications.html', context)

@login_required
def chdr_page(request):
    parent = request.user.parent_profile
    infant = get_object_or_404(Infant, phn=parent.phn)
    today = date.today()

    growth_records = GrowthRecord.objects.filter(infant=infant).order_by('visit_date')
    vaccinations = ScheduledVaccination.objects.filter(infant=infant).order_by('due_date')
    latest_ml = MLRiskAssessment.objects.filter(infant=infant).order_by('-assessed_at').first()

    context = {
        'title': 'BlueCradle — Digital CHDR',
        'infant': infant,
        'parent': parent,
        'growth_records': growth_records,
        'vaccinations': vaccinations,
        'latest_ml': latest_ml,
        'today': today,
        'active_nav': 'chdr',
    }
    return render(request, 'parent_module/chdr.html', context)


@login_required
def chdr_download(request):
    parent = request.user.parent_profile
    infant = get_object_or_404(Infant, phn=parent.phn)
    today = timezone.now().date()

    growth_records = GrowthRecord.objects.filter(infant=infant).order_by('visit_date')
    vaccinations = ScheduledVaccination.objects.filter(infant=infant).order_by('due_date')
    latest_ml = MLRiskAssessment.objects.filter(infant=infant).order_by('-assessed_at').first()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        'title', parent=styles['Title'],
        fontSize=20, spaceAfter=4, alignment=TA_CENTER
    )
    subtitle_style = ParagraphStyle(
        'subtitle', parent=styles['Normal'],
        fontSize=10, textColor=colors.grey, alignment=TA_CENTER, spaceAfter=16
    )
    section_style = ParagraphStyle(
        'section', parent=styles['Heading2'],
        fontSize=12, spaceBefore=16, spaceAfter=8,
        textColor=colors.HexColor('#0ea5e9')
    )
    normal_style = ParagraphStyle(
        'normal_custom', parent=styles['Normal'],
        fontSize=9, spaceAfter=4
    )
    footer_style = ParagraphStyle(
        'footer', parent=styles['Normal'],
        fontSize=7, textColor=colors.grey, alignment=TA_CENTER
    )

    # ── Header ───────────────────────────────────────────────
    story.append(Paragraph("BlueCradle", title_style))
    story.append(Paragraph("Child Health Development Record (Digital)", subtitle_style))
    story.append(Paragraph(f"Generated on {today.strftime('%d %B %Y')}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#0ea5e9')))
    story.append(Spacer(1, 12))

    # ── Section 1: Infant Profile ────────────────────────────
    story.append(Paragraph("Infant Profile", section_style))
    profile_data = [
        ['Full Name',     infant.full_name],
        ['PHN',           infant.phn],
        ['Date of Birth', infant.date_of_birth.strftime('%d %B %Y')],
        ['Sex',           infant.get_sex_display()],
        ['Birth Weight',  f"{infant.birth_weight_kg} kg"],
        ['Birth Length',  f"{infant.birth_length_cm} cm"],
        ['Birth Order',   str(infant.birth_order)],
        ['MOH Division',  infant.moh_division],
        ['Assigned PHM',  infant.registered_phm.full_name],
    ]
    profile_table = Table(profile_data, colWidths=[60 * mm, 110 * mm])
    profile_table.setStyle(TableStyle([
        ('FONTSIZE',       (0, 0), (-1, -1), 9),
        ('FONTNAME',       (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME',       (1, 0), (1, -1), 'Helvetica'),
        ('TEXTCOLOR',      (0, 0), (0, -1), colors.HexColor('#64748b')),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('GRID',           (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('PADDING',        (0, 0), (-1, -1), 6),
    ]))
    story.append(profile_table)
    story.append(Spacer(1, 8))

    # ── Section 2: ML Risk ───────────────────────────────────
    story.append(Paragraph("ML Risk Stratification", section_style))
    if latest_ml:
        risk_data = [
            ['Risk Level',   latest_ml.risk_level],
            ['Confidence',   f"{float(latest_ml.confidence_score) * 100:.1f}%"],
            ['Assessed On',  latest_ml.assessed_at.strftime('%d %B %Y')],
        ]
    else:
        risk_data = [['Status', 'No assessment yet — requires 2+ visits']]

    risk_table = Table(risk_data, colWidths=[60 * mm, 110 * mm])
    risk_table.setStyle(TableStyle([
        ('FONTSIZE',       (0, 0), (-1, -1), 9),
        ('FONTNAME',       (0, 0), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR',      (0, 0), (0, -1), colors.HexColor('#64748b')),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('GRID',           (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('PADDING',        (0, 0), (-1, -1), 6),
    ]))
    story.append(risk_table)
    story.append(Spacer(1, 8))

    # ── Section 3: Growth Records ────────────────────────────
    story.append(Paragraph("Growth Record History", section_style))
    if growth_records.exists():
        growth_header = [['Date', 'Age (days)', 'Weight (kg)', 'Height (cm)', 'WHZ', 'Classification']]
        growth_rows = [
            [
                gr.visit_date.strftime('%d %b %Y'),
                str(gr.age_in_days),
                str(gr.weight_kg),
                str(gr.height_cm),
                str(gr.whz) if gr.whz is not None else '—',
                gr.who_classification or '—',
            ]
            for gr in growth_records
        ]
        growth_table = Table(growth_header + growth_rows, colWidths=[28*mm, 22*mm, 28*mm, 28*mm, 20*mm, 34*mm])
        growth_table.setStyle(TableStyle([
            ('FONTSIZE',       (0, 0), (-1, -1), 8),
            ('FONTNAME',       (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND',     (0, 0), (-1, 0), colors.HexColor('#0ea5e9')),
            ('TEXTCOLOR',      (0, 0), (-1, 0), colors.white),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ('GRID',           (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING',        (0, 0), (-1, -1), 5),
            ('ALIGN',          (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(growth_table)
    else:
        story.append(Paragraph("No growth records yet.", normal_style))

    story.append(Spacer(1, 8))

    # ── Section 4: Vaccination Schedule ─────────────────────
    story.append(Paragraph("Vaccination Schedule", section_style))
    if vaccinations.exists():
        vac_header = [['Vaccine', 'Due Date', 'Date Given', 'Status']]
        vac_rows = [
            [
                vac.vaccine_name,
                vac.due_date.strftime('%d %b %Y'),
                vac.date_given.strftime('%d %b %Y') if vac.date_given else '—',
                vac.status,
            ]
            for vac in vaccinations
        ]
        vac_table = Table(vac_header + vac_rows, colWidths=[50*mm, 35*mm, 35*mm, 40*mm])
        vac_table.setStyle(TableStyle([
            ('FONTSIZE',       (0, 0), (-1, -1), 8),
            ('FONTNAME',       (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND',     (0, 0), (-1, 0), colors.HexColor('#0ea5e9')),
            ('TEXTCOLOR',      (0, 0), (-1, 0), colors.white),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ('GRID',           (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING',        (0, 0), (-1, -1), 5),
            ('ALIGN',          (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(vac_table)
    else:
        story.append(Paragraph("No vaccination records yet.", normal_style))

    # ── Footer ───────────────────────────────────────────────
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0')))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "This document is a digital export from the BlueCradle Infant Health Monitoring System. "
        "For clinical decisions, always consult a qualified health professional.",
        footer_style
    ))

    doc.build(story)
    buffer.seek(0)

    filename = f"CHDR_{infant.phn}_{today.strftime('%Y%m%d')}.pdf"
    return FileResponse(
        buffer,
        as_attachment=True,
        filename=filename,
        content_type='application/pdf'
    )