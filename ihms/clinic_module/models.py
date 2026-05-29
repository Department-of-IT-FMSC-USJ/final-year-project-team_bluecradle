from django.db import models
from accounts_module.models import PHM_User
from infants_module.models import Infant

class ClinicSession(models.Model):

    SESSION_TYPE_CHOICES = [
        ('CLINIC', 'Clinic Session'),
        ('DOMICILIARY', 'Domiciliary Visit'),
    ]

    STATUS_CHOICES = [
        ('UPCOMING', 'Upcoming'),
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
    ]

    phm = models.ForeignKey(
        PHM_User,
        on_delete=models.PROTECT,
        related_name='clinic_sessions'
    )

    # FK to the schedule that generated this session.
    # Null for manually created sessions and all existing records.
    schedule = models.ForeignKey(
        'ClinicSchedule',
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        related_name='sessions'
    )

    session_date = models.DateField()
    session_type = models.CharField(max_length=20, choices=SESSION_TYPE_CHOICES, default='CLINIC')
    location = models.CharField(max_length=200)
    moh_division = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UPCOMING')

    # Flipped to True by the Service Worker after all events
    # in this session have been successfully synced to Django.
    is_synced = models.BooleanField(default=False)
    synced_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-session_date']

    def __str__(self):
        return f"{self.phm} — {self.session_type} — {self.session_date} — {self.status}"
    

class ClinicSchedule(models.Model):

    SCHEDULE_MODE_CHOICES = [
        ('RECURRING', 'Recurring — First date + frequency'),
        ('FIXED_DATES', 'Fixed Dates — Exact date list'),
    ]

    phm = models.ForeignKey(
        PHM_User,
        on_delete=models.PROTECT,
        related_name='clinic_schedules'
    )

    year = models.PositiveSmallIntegerField()
    session_type = models.CharField(
        max_length=20,
        choices=ClinicSession.SESSION_TYPE_CHOICES,
        default='CLINIC'
    )
    location = models.CharField(max_length=200)
    schedule_mode = models.CharField(max_length=20, choices=SCHEDULE_MODE_CHOICES)

    # ── RECURRING mode fields ────────────────────────────────────────────────
    # First clinic date of the year — system generates subsequent ones
    # automatically by adding frequency_weeks repeatedly until year end.
    first_date = models.DateField(null=True, blank=True)
    frequency_weeks = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text='How many weeks between each session (e.g. 4 = monthly)'
    )

    # ── FIXED_DATES mode fields ──────────────────────────────────────────────
    # List of exact dates as ISO strings: ["2026-01-15", "2026-02-19", ...]
    fixed_dates = models.JSONField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-year']
        # One active schedule per PHM per year
        unique_together = ['phm', 'year']

    def __str__(self):
        return f"{self.phm} — {self.year} — {self.schedule_mode}"

    
class GrowthRecord(models.Model):

    infant = models.ForeignKey(
        Infant,
        on_delete=models.PROTECT,
        related_name='growth_records'
    )
    session = models.ForeignKey(
        ClinicSession,
        on_delete=models.PROTECT,
        related_name='growth_records'
    )

    visit_date = models.DateField()
    age_in_days = models.PositiveIntegerField()

    # Raw anthropometrics — what the PHM physically measures.
    # Z-scores are calculated FROM these by igrowup, not entered manually.
    weight_kg = models.DecimalField(max_digits=4, decimal_places=2)
    height_cm = models.DecimalField(max_digits=4, decimal_places=1)
    muac_mm = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)

    # Oedema overrides ALL Z-score classifications.
    # If True, infant is SAM regardless of any Z-score value.
    bilateral_pitting_oedema = models.BooleanField(default=False)

    # Z-scores calculated by igrowup on-device, then synced here.
    whz = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    waz = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    haz = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # WHO threshold classification derived from Z-scores.
    # This is deterministic — not ML. Calculated server-side after sync.
    WHO_CLASSIFICATION_CHOICES = [
        ('NORMAL', 'Normal'),
        ('MAM', 'Moderate Acute Malnutrition'),
        ('SAM', 'Severe Acute Malnutrition'),
    ]
    who_classification = models.CharField(
        max_length=10,
        choices=WHO_CLASSIFICATION_CHOICES,
        null=True,
        blank=True
    )

    # Delta fields — calculated at sync time from previous GrowthRecord.
    # These become sequential features in the LSTM.
    days_since_last_visit = models.PositiveIntegerField(null=True, blank=True)
    weight_delta_kg = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    whz_velocity = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['infant', 'visit_date']

    def __str__(self):
        return f"{self.infant} — {self.visit_date} — WHZ: {self.whz}"
    
class ImmunizationEvent(models.Model):

    VACCINE_CHOICES = [
        ('BCG', 'BCG'),
        ('OPV_0', 'OPV Birth Dose'),
        ('HEP_B', 'Hepatitis B Birth Dose'),
        ('PENTA_1', 'Pentavalent 1'),
        ('PENTA_2', 'Pentavalent 2'),
        ('PENTA_3', 'Pentavalent 3'),
        ('OPV_1', 'OPV 1'),
        ('OPV_2', 'OPV 2'),
        ('OPV_3', 'OPV 3'),
        ('PCV_1', 'PCV 1'),
        ('PCV_2', 'PCV 2'),
        ('PCV_3', 'PCV 3'),
        ('ROTA_1', 'Rotavirus 1'),
        ('ROTA_2', 'Rotavirus 2'),
        ('MR_1', 'MR 1'),
        ('JE', 'Live JE'),
        ('DTP_BOOSTER', 'DTP Booster'),
        ('OPV_BOOSTER', 'OPV Booster'),
        ('MR_2', 'MR 2'),
    ]

    DOSE_STATUS_CHOICES = [
        ('ADMINISTERED', 'Administered'),
        ('DEFAULTED', 'Defaulted'),
        ('CONTRAINDICATED', 'Contraindicated'),
    ]

    infant = models.ForeignKey(
        Infant,
        on_delete=models.PROTECT,
        related_name='immunization_events'
    )
    session = models.ForeignKey(
        ClinicSession,
        on_delete=models.PROTECT,
        related_name='immunization_events'
    )

    vaccine = models.CharField(max_length=20, choices=VACCINE_CHOICES)
    dose_status = models.CharField(max_length=20, choices=DOSE_STATUS_CHOICES)

    # Only populated when dose_status = ADMINISTERED
    date_administered = models.DateField(null=True, blank=True)
    batch_number = models.CharField(max_length=50, null=True, blank=True)
    adverse_event_noted = models.BooleanField(default=False)
    adverse_event_detail = models.TextField(null=True, blank=True)

    # Defaulter fields — only populated when dose_status = DEFAULTED
    scheduled_date = models.DateField(null=True, blank=True)
    is_defaulter = models.BooleanField(default=False)
    defaulter_days_overdue = models.PositiveIntegerField(null=True, blank=True)

    # Grace period applied — stored for audit clarity.
    # 14 days if infant was under 12 months at scheduled_date.
    # 30 days if infant was 12 months or older at scheduled_date.
    grace_period_days = models.PositiveSmallIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['infant', 'scheduled_date']
        # One record per vaccine per infant — no duplicate entries.
        unique_together = ['infant', 'vaccine']

    def __str__(self):
        return f"{self.infant} — {self.vaccine} — {self.dose_status}"
    
class FHBAtomicEvent(models.Model):

    EVENT_TYPE_CHOICES = [
        ('NEW_REGISTRATION', 'New Infant Registration'),
        ('GROWTH_RECORD', 'Anthropometric Measurement'),
        ('VACCINATION', 'Vaccination Administered'),
        ('DEFAULTER', 'Vaccination Defaulter'),
        ('POSTNATAL_VISIT', 'Domiciliary Postnatal Visit'),
        ('CONTRAINDICATION', 'Vaccine Contraindicated'),
    ]

    FHB_SERVICE_CODE_CHOICES = [
        ('NEW_REG', 'New Registration'),
        ('GM_ATTENDANCE', 'Growth Monitoring Attendance'),
        ('EPI_VACCINATION', 'EPI 3/79 Register Entry'),
        ('MISSED_CLINIC', 'Missed Clinic / Domiciliary Follow-up'),
        ('POSTNATAL_10', 'Postpartum Visit — First 10 Days'),
        ('POSTNATAL_42', 'Postpartum Visit — 42 Days'),
        ('MALNUTRITION_FLAG', 'Low Birth Weight / Malnutrition Flag'),
    ]

    PRIORITY_CHOICES = [
        ('CRITICAL_HIGH', 'Critical High — SAM/MAM Alerts'),
        ('CRITICAL', 'Critical — Vaccinations / Defaulters'),
        ('STANDARD', 'Standard — Growth Records / Admin'),
    ]

    infant = models.ForeignKey(
        Infant,
        on_delete=models.PROTECT,
        related_name='atomic_events'
    )
    session = models.ForeignKey(
        ClinicSession,
        on_delete=models.PROTECT,
        related_name='atomic_events'
    )
    phm = models.ForeignKey(
        PHM_User,
        on_delete=models.PROTECT,
        related_name='atomic_events'
    )

    # moh_division denormalized here — same reason as on Infant.
    # Future MOH dashboard just adds .filter(moh_division='Deraniyagala').
    moh_division = models.CharField(max_length=100)

    event_type = models.CharField(max_length=25, choices=EVENT_TYPE_CHOICES)
    fhb_service_code = models.CharField(max_length=25, choices=FHB_SERVICE_CODE_CHOICES)
    priority = models.CharField(max_length=15, choices=PRIORITY_CHOICES, default='STANDARD')

    # JSON snapshot of the clinical data at the time of this event.
    # This is what gets packaged into the encrypted sync payload.
    payload_json = models.JSONField()

    event_timestamp = models.DateTimeField()

    # Sync state — Service Worker watches this flag.
    is_synced = models.BooleanField(default=False)
    synced_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['priority', 'event_timestamp']

    def __str__(self):
        return f"{self.phm} — {self.event_type} — {self.event_timestamp}"