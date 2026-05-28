from rest_framework import request, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from .models import GrowthRecord, ImmunizationEvent, ClinicSession, FHBAtomicEvent
from .serializers import ClinicSessionSerializer, GrowthRecordSerializer, ImmunizationEventSerializer, FHBAtomicEventSerializer
from django.contrib.auth.decorators import login_required
from infants_module.models import Infant
from django.db import models
from datetime import date
from django.utils import timezone
from accounts_module.permission import IsPHM
from .reporting_utils import generate_h523_data
from ml_module.models import MLRiskAssessment

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

        # Check PHN doesn't already exist
        if Infant.objects.filter(phn=data['phn']).exists():
            messages.error(request, f"PHN {data['phn']} is already registered.")
            return redirect('clinic:infant_register')

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
        messages.success(request, f"Infant {data['full_name']} registered successfully.")
        return redirect('clinic:dashboard')

    context = {
        'title': 'BlueCradle - Infant Registration',
        'active_nav': 'infants'
    }
    
    return render(
        request,
        'clinic_module/infant_register.html',
        context,
    )


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

        risk_filter = request.GET.get('filter')
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
        'active_nav': 'growth' if filter_type == 'risk' else 'infants',
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

    context = {
        'title': 'BlueCradle - Infant Detail',
        'infant': infant,
        'age_display': age_display,
        'latest_growth': latest_growth,
        'growth_records': growth_records,
        'latest_ml': latest_ml,
        'immunization_events': immunization_events,
        'active_nav': 'infants',
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

        GrowthRecord.objects.create(
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
        messages.success(request, "Growth record saved successfully.")
        return redirect('clinic:infant_detail', phn=phn)

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
            messages.error(request, f"A record for {data['vaccine']} already exists. Use the update function.")
            return redirect('clinic:immunization', phn=phn)

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
        messages.success(request, "Vaccination record saved.")
        return redirect('clinic:infant_detail', phn=phn)

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
    phm = request.user.phm_profile
    today = date.today()

    if request.method == 'POST':
        data = request.POST
        ClinicSession.objects.create(
            phm=phm,
            session_date=data['session_date'],
            session_type=data['session_type'],
            location=data['location'],
            moh_division=phm.moh_division,
        )
        messages.success(request, "Clinic session created successfully.")
        return redirect('clinic:phm_dashboard')

    # Past sessions
    past_sessions = ClinicSession.objects.filter(
        phm=phm
    ).order_by('-session_date')[:10]

    # Next upcoming session
    next_session = ClinicSession.objects.filter(
        phm=phm,
        session_date__gte=today
    ).order_by('session_date').first()

    # Performance stats for current month
    first_of_month = today.replace(day=1)
    sessions_this_month = ClinicSession.objects.filter(
        phm=phm,
        session_date__gte=first_of_month
    ).count()

    context = {
        'title': 'BlueCradle - Clinic Sessions',
        'past_sessions': past_sessions,
        'next_session': next_session,
        'sessions_this_month': sessions_this_month,
        'today': today,
        'active_nav': 'sessions'
    }
    return render(request, 'clinic_module/session_start.html', context)

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
            
            # Temporarily commented out — requires Redis
            # from ml_module.tasks import run_ml_risk_assessment
            # run_ml_risk_assessment.delay(
            #     infant_phn=phn,
            #     growth_record_id=saved_record.id
            # )

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
            return Response(serializer.data, status=status.HTTP_201_CREATED)
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