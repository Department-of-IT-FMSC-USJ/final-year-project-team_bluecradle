import io
from datetime import date
from django.db.models import Count, Max, Q
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# ── Shared style helpers ─────────────────────────────────────────

BLUE        = colors.HexColor('#0ea5e9')
DARK_BLUE   = colors.HexColor('#1A3A5C')
ERROR       = colors.HexColor('#ef4444')
WARNING     = colors.HexColor('#f59e0b')
SUCCESS     = colors.HexColor('#22c55e')
LIGHT_GRAY  = colors.HexColor('#f8fafc')
BORDER_GRAY = colors.HexColor('#e2e8f0')
TEXT_GRAY   = colors.HexColor('#64748b')


def get_styles():
    styles = getSampleStyleSheet()
    return {
        'title': ParagraphStyle(
            'rpt_title', parent=styles['Title'],
            fontSize=22, textColor=colors.white,
            alignment=TA_CENTER, spaceAfter=4
        ),
        'subtitle': ParagraphStyle(
            'rpt_subtitle', parent=styles['Normal'],
            fontSize=10, textColor=colors.HexColor('#bae6fd'),
            alignment=TA_CENTER, spaceAfter=4
        ),
        'section': ParagraphStyle(
            'rpt_section', parent=styles['Heading2'],
            fontSize=12, spaceBefore=16, spaceAfter=8,
            textColor=BLUE
        ),
        'normal': ParagraphStyle(
            'rpt_normal', parent=styles['Normal'],
            fontSize=9, spaceAfter=4
        ),
        'footer': ParagraphStyle(
            'rpt_footer', parent=styles['Normal'],
            fontSize=7, textColor=TEXT_GRAY,
            alignment=TA_CENTER
        ),
        'stat_label': ParagraphStyle(
            'rpt_stat_label', parent=styles['Normal'],
            fontSize=8, textColor=TEXT_GRAY,
            alignment=TA_CENTER
        ),
        'stat_value': ParagraphStyle(
            'rpt_stat_value', parent=styles['Normal'],
            fontSize=22, fontName='Helvetica-Bold',
            alignment=TA_CENTER
        ),
    }


def build_header(story, styles, title, subtitle, division, today):
    """Shared header block for all reports."""
    # Header table with dark blue background
    header_data = [[
        Paragraph(f'<font color="white"><b>BlueCradle</b></font>', ParagraphStyle(
            'h1', fontSize=20, alignment=TA_CENTER,
            textColor=colors.white, fontName='Helvetica-Bold'
        )),
    ], [
        Paragraph(title, ParagraphStyle(
            'h2', fontSize=14, alignment=TA_CENTER,
            textColor=colors.HexColor('#bae6fd'), fontName='Helvetica-Bold'
        )),
    ], [
        Paragraph(
            f'{division} · Generated on {today.strftime("%d %B %Y")}',
            ParagraphStyle(
                'h3', fontSize=9, alignment=TA_CENTER,
                textColor=colors.HexColor('#7dd3fc')
            )
        ),
    ]]
    header_table = Table(header_data, colWidths=[170 * mm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND',  (0, 0), (-1, -1), DARK_BLUE),
        ('PADDING',     (0, 0), (-1, -1), 10),
        ('ALIGN',       (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING',  (0, 0), (-1, 0), 20),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 20),
        ('ROUNDEDCORNERS', [8, 8, 8, 8]),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 16))


def build_footer(story, styles):
    story.append(Spacer(1, 16))
    story.append(HRFlowable(
        width="100%", thickness=0.5, color=BORDER_GRAY
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "This report is generated from the BlueCradle Infant Health Monitoring System. "
        "For official use by MOH Officers only.",
        styles['footer']
    ))


def base_table_style():
    return TableStyle([
        ('FONTSIZE',       (0, 0), (-1, -1), 8),
        ('FONTNAME',       (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND',     (0, 0), (-1, 0), BLUE),
        ('TEXTCOLOR',      (0, 0), (-1, 0), colors.white),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ('GRID',           (0, 0), (-1, -1), 0.5, BORDER_GRAY),
        ('PADDING',        (0, 0), (-1, -1), 6),
        ('ALIGN',          (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN',          (0, 1), (0, -1), 'LEFT'),
    ])


def build_doc(buffer):
    return SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )


# ── Report 1: Division Summary ───────────────────────────────────

def generate_division_summary(division, today):
    from infants_module.models import Infant
    from clinic_module.models import ClinicSession, ScheduledVaccination
    from ml_module.models import MLRiskAssessment
    from accounts_module.models import PHM_User

    buffer = io.BytesIO()
    doc = build_doc(buffer)
    styles = get_styles()
    story = []

    build_header(story, styles, 'Division Summary Report', '', division, today)

    # ── Infant Population ────────────────────────────────────
    story.append(Paragraph("Infant Population", styles['section']))
    this_month_start = today.replace(day=1)

    total_infants  = Infant.objects.filter(moh_division=division).count()
    new_this_month = Infant.objects.filter(moh_division=division, created_at__date__gte=this_month_start).count()
    male_count     = Infant.objects.filter(moh_division=division, sex='M').count()
    female_count   = Infant.objects.filter(moh_division=division, sex='F').count()
    total_phms     = PHM_User.objects.filter(moh_division=division).count()

    pop_data = [
        ['Metric', 'Count'],
        ['Total Registered Infants', str(total_infants)],
        ['New Registrations This Month', str(new_this_month)],
        ['Male', str(male_count)],
        ['Female', str(female_count)],
        ['PHMs in Division', str(total_phms)],
    ]
    pop_table = Table(pop_data, colWidths=[120 * mm, 50 * mm])
    pop_table.setStyle(base_table_style())
    story.append(pop_table)
    story.append(Spacer(1, 8))

    # ── Nutritional Status ───────────────────────────────────
    story.append(Paragraph("Nutritional Status (Latest ML Assessments)", styles['section']))

    latest_ids = MLRiskAssessment.objects.filter(
        infant__moh_division=division
    ).values('infant').annotate(latest_id=Max('id')).values_list('latest_id', flat=True)

    latest = MLRiskAssessment.objects.filter(id__in=latest_ids)
    sam_count    = latest.filter(risk_level='SAM').count()
    mam_count    = latest.filter(risk_level='MAM').count()
    normal_count = latest.filter(risk_level='NORMAL').count()
    assessed     = sam_count + mam_count + normal_count

    nut_data = [
        ['Risk Level', 'Count', '% of Assessed'],
        ['SAM (Severe Acute Malnutrition)', str(sam_count),
         f"{round(sam_count/assessed*100,1)}%" if assessed else '—'],
        ['MAM (Moderate Acute Malnutrition)', str(mam_count),
         f"{round(mam_count/assessed*100,1)}%" if assessed else '—'],
        ['Normal', str(normal_count),
         f"{round(normal_count/assessed*100,1)}%" if assessed else '—'],
        ['Total Assessed', str(assessed), '100%'],
    ]
    nut_table = Table(nut_data, colWidths=[100 * mm, 35 * mm, 35 * mm])
    nut_table.setStyle(base_table_style())
    story.append(nut_table)
    story.append(Spacer(1, 8))

    # ── Vaccination Coverage ─────────────────────────────────
    story.append(Paragraph("Vaccination Coverage", styles['section']))

    vac_total        = ScheduledVaccination.objects.filter(infant__moh_division=division).count()
    vac_administered = ScheduledVaccination.objects.filter(infant__moh_division=division, status='ADMINISTERED').count()
    vac_defaulted    = ScheduledVaccination.objects.filter(infant__moh_division=division, status='DEFAULTED').count()
    vac_pending      = ScheduledVaccination.objects.filter(infant__moh_division=division, status='PENDING').count()
    coverage_rate    = round(vac_administered / vac_total * 100, 1) if vac_total > 0 else 0

    vac_data = [
        ['Metric', 'Count'],
        ['Total Scheduled Vaccines', str(vac_total)],
        ['Administered', str(vac_administered)],
        ['Defaulted', str(vac_defaulted)],
        ['Pending', str(vac_pending)],
        ['Coverage Rate', f"{coverage_rate}%"],
    ]
    vac_table = Table(vac_data, colWidths=[120 * mm, 50 * mm])
    vac_table.setStyle(base_table_style())
    story.append(vac_table)
    story.append(Spacer(1, 8))

    # ── Clinic Sessions ──────────────────────────────────────
    story.append(Paragraph("Clinic Sessions", styles['section']))

    total_sessions     = ClinicSession.objects.filter(moh_division=division).count()
    completed_sessions = ClinicSession.objects.filter(moh_division=division, status='COMPLETED').count()
    upcoming_sessions  = ClinicSession.objects.filter(moh_division=division, status='UPCOMING').count()
    this_month         = ClinicSession.objects.filter(
        moh_division=division,
        session_date__gte=this_month_start,
        session_date__lte=today,
    ).count()

    ses_data = [
        ['Metric', 'Count'],
        ['Total Sessions', str(total_sessions)],
        ['Completed', str(completed_sessions)],
        ['Upcoming', str(upcoming_sessions)],
        ['Held This Month', str(this_month)],
    ]
    ses_table = Table(ses_data, colWidths=[120 * mm, 50 * mm])
    ses_table.setStyle(base_table_style())
    story.append(ses_table)

    build_footer(story, styles)
    doc.build(story)
    buffer.seek(0)
    return buffer


# ── Report 2: Nutritional Status ────────────────────────────────

def generate_nutrition_report(division, today):
    from ml_module.models import MLRiskAssessment
    from clinic_module.models import GrowthRecord

    buffer = io.BytesIO()
    doc = build_doc(buffer)
    styles = get_styles()
    story = []

    build_header(story, styles, 'Nutritional Status Report', '', division, today)

    latest_ids = MLRiskAssessment.objects.filter(
        infant__moh_division=division
    ).values('infant').annotate(latest_id=Max('id')).values_list('latest_id', flat=True)
    latest = MLRiskAssessment.objects.filter(id__in=latest_ids).select_related('infant', 'infant__registered_phm')

    sam_count    = latest.filter(risk_level='SAM').count()
    mam_count    = latest.filter(risk_level='MAM').count()
    normal_count = latest.filter(risk_level='NORMAL').count()
    assessed     = sam_count + mam_count + normal_count

    # Summary
    story.append(Paragraph("Summary", styles['section']))
    sum_data = [
        ['SAM', 'MAM', 'Normal', 'Total Assessed'],
        [str(sam_count), str(mam_count), str(normal_count), str(assessed)],
    ]
    sum_table = Table(sum_data, colWidths=[42*mm, 42*mm, 42*mm, 44*mm])
    sum_table.setStyle(base_table_style())
    story.append(sum_table)
    story.append(Spacer(1, 8))

    # SAM Infants
    story.append(Paragraph("SAM Risk Infants", styles['section']))
    sam_header = [['Infant Name', 'PHN', 'Confidence', 'Assessed On', 'PHM']]
    sam_rows = [
        [
            a.infant.full_name,
            a.infant.phn,
            f"{float(a.confidence_score)*100:.1f}%",
            a.assessed_at.strftime('%d %b %Y'),
            a.infant.registered_phm.full_name,
        ]
        for a in latest.filter(risk_level='SAM').order_by('-assessed_at')
    ]
    if sam_rows:
        sam_table = Table(sam_header + sam_rows, colWidths=[45*mm, 30*mm, 25*mm, 30*mm, 40*mm])
        sam_table.setStyle(base_table_style())
        story.append(sam_table)
    else:
        story.append(Paragraph("No SAM risk infants.", styles['normal']))

    story.append(Spacer(1, 8))

    # MAM Infants
    story.append(Paragraph("MAM Risk Infants", styles['section']))
    mam_header = [['Infant Name', 'PHN', 'Confidence', 'Assessed On', 'PHM']]
    mam_rows = [
        [
            a.infant.full_name,
            a.infant.phn,
            f"{float(a.confidence_score)*100:.1f}%",
            a.assessed_at.strftime('%d %b %Y'),
            a.infant.registered_phm.full_name,
        ]
        for a in latest.filter(risk_level='MAM').order_by('-assessed_at')
    ]
    if mam_rows:
        mam_table = Table(mam_header + mam_rows, colWidths=[45*mm, 30*mm, 25*mm, 30*mm, 40*mm])
        mam_table.setStyle(base_table_style())
        story.append(mam_table)
    else:
        story.append(Paragraph("No MAM risk infants.", styles['normal']))

    story.append(Spacer(1, 8))

    # Oedema Cases
    story.append(Paragraph("Bilateral Pitting Oedema Cases", styles['section']))
    oedema_qs = GrowthRecord.objects.filter(
        infant__moh_division=division,
        bilateral_pitting_oedema=True
    ).select_related('infant', 'infant__registered_phm').order_by('-visit_date')

    oedema_header = [['Infant Name', 'PHN', 'Recorded On', 'PHM']]
    oedema_rows = [
        [
            r.infant.full_name,
            r.infant.phn,
            r.visit_date.strftime('%d %b %Y'),
            r.infant.registered_phm.full_name,
        ]
        for r in oedema_qs
    ]
    if oedema_rows:
        oedema_table = Table(oedema_header + oedema_rows, colWidths=[50*mm, 35*mm, 35*mm, 50*mm])
        oedema_table.setStyle(base_table_style())
        story.append(oedema_table)
    else:
        story.append(Paragraph("No oedema cases recorded.", styles['normal']))

    build_footer(story, styles)
    doc.build(story)
    buffer.seek(0)
    return buffer


# ── Report 3: Vaccination Coverage ──────────────────────────────

def generate_vaccination_report(division, today):
    from clinic_module.models import ScheduledVaccination

    buffer = io.BytesIO()
    doc = build_doc(buffer)
    styles = get_styles()
    story = []

    build_header(story, styles, 'Vaccination Coverage Report', '', division, today)

    vac_qs           = ScheduledVaccination.objects.filter(infant__moh_division=division)
    vac_total        = vac_qs.count()
    vac_administered = vac_qs.filter(status='ADMINISTERED').count()
    vac_defaulted    = vac_qs.filter(status='DEFAULTED').count()
    vac_pending      = vac_qs.filter(status='PENDING').count()
    vac_contra       = vac_qs.filter(status='CONTRAINDICATED').count()
    coverage_rate    = round(vac_administered / vac_total * 100, 1) if vac_total > 0 else 0

    # Summary
    story.append(Paragraph("Coverage Summary", styles['section']))
    sum_data = [
        ['Total', 'Administered', 'Defaulted', 'Pending', 'Contraindicated', 'Coverage Rate'],
        [str(vac_total), str(vac_administered), str(vac_defaulted),
         str(vac_pending), str(vac_contra), f"{coverage_rate}%"],
    ]
    sum_table = Table(sum_data, colWidths=[28*mm, 32*mm, 28*mm, 28*mm, 34*mm, 30*mm])
    sum_table.setStyle(base_table_style())
    story.append(sum_table)
    story.append(Spacer(1, 8))

    # Per vaccine breakdown
    story.append(Paragraph("Per Vaccine Breakdown", styles['section']))
    breakdown = vac_qs.values('vaccine_name').annotate(
        total=Count('id'),
        administered=Count('id', filter=Q(status='ADMINISTERED')),
        defaulted=Count('id', filter=Q(status='DEFAULTED')),
        pending=Count('id', filter=Q(status='PENDING')),
    ).order_by('vaccine_name')

    bk_header = [['Vaccine', 'Total', 'Administered', 'Defaulted', 'Pending', 'Coverage']]
    bk_rows = [
        [
            v['vaccine_name'],
            str(v['total']),
            str(v['administered']),
            str(v['defaulted']),
            str(v['pending']),
            f"{round(v['administered']/v['total']*100,1)}%" if v['total'] > 0 else '—',
        ]
        for v in breakdown
    ]
    if bk_rows:
        bk_table = Table(bk_header + bk_rows, colWidths=[45*mm, 20*mm, 30*mm, 25*mm, 25*mm, 25*mm])
        bk_table.setStyle(base_table_style())
        story.append(bk_table)

    story.append(PageBreak())

    # Defaulted vaccinations
    story.append(Paragraph("Defaulted Vaccinations", styles['section']))
    def_qs = vac_qs.filter(status='DEFAULTED').select_related(
        'infant', 'infant__registered_phm'
    ).order_by('due_date')

    def_header = [['Infant Name', 'PHN', 'Vaccine', 'Due Date', 'PHM']]
    def_rows = [
        [
            v.infant.full_name,
            v.infant.phn,
            v.vaccine_name,
            v.due_date.strftime('%d %b %Y'),
            v.infant.registered_phm.full_name,
        ]
        for v in def_qs
    ]
    if def_rows:
        def_table = Table(def_header + def_rows, colWidths=[45*mm, 28*mm, 30*mm, 28*mm, 39*mm])
        def_table.setStyle(base_table_style())
        story.append(def_table)
    else:
        story.append(Paragraph("No defaulted vaccinations.", styles['normal']))

    build_footer(story, styles)
    doc.build(story)
    buffer.seek(0)
    return buffer


# ── Report 4: PHM Activity ───────────────────────────────────────

def generate_phm_activity_report(division, today, month=None, year=None):
    from accounts_module.models import PHM_User
    from clinic_module.models import ClinicSession, GrowthRecord
    from infants_module.models import Infant

    buffer = io.BytesIO()
    doc = build_doc(buffer)
    styles = get_styles()
    story = []

    # Month filter
    if month and year:
        from datetime import date as dt
        period_start = dt(int(year), int(month), 1)
        import calendar
        last_day = calendar.monthrange(int(year), int(month))[1]
        period_end = dt(int(year), int(month), last_day)
        period_label = period_start.strftime('%B %Y')
    else:
        period_start = None
        period_end = None
        period_label = 'All Time'

    build_header(
        story, styles,
        'PHM Activity Report',
        '',
        division,
        today
    )

    story.append(Paragraph(f"Period: {period_label}", styles['normal']))
    story.append(Spacer(1, 8))

    phms = PHM_User.objects.filter(moh_division=division)

    phm_header = [['PHM Name', 'Reg. No', 'Infants', 'Sessions', 'Growth Records', 'Last Session']]
    phm_rows = []

    for phm in phms:
        infant_count = Infant.objects.filter(registered_phm=phm).count()

        session_qs = ClinicSession.objects.filter(phm=phm)
        if period_start and period_end:
            session_qs = session_qs.filter(
                session_date__gte=period_start,
                session_date__lte=period_end
            )
        session_count = session_qs.count()

        gr_qs = GrowthRecord.objects.filter(infant__registered_phm=phm)
        if period_start and period_end:
            gr_qs = gr_qs.filter(
                visit_date__gte=period_start,
                visit_date__lte=period_end
            )
        gr_count = gr_qs.count()

        last_session = ClinicSession.objects.filter(
            phm=phm
        ).order_by('-session_date').first()

        phm_rows.append([
            phm.full_name,
            phm.registration_number,
            str(infant_count),
            str(session_count),
            str(gr_count),
            last_session.session_date.strftime('%d %b %Y') if last_session else '—',
        ])

    if phm_rows:
        phm_table = Table(
            phm_header + phm_rows,
            colWidths=[45*mm, 28*mm, 20*mm, 22*mm, 30*mm, 25*mm]
        )
        phm_table.setStyle(base_table_style())
        story.append(phm_table)
    else:
        story.append(Paragraph("No PHMs found in this division.", styles['normal']))

    build_footer(story, styles)
    doc.build(story)
    buffer.seek(0)
    return buffer