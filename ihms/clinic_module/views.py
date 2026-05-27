from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from .models import GrowthRecord, ImmunizationEvent, ClinicSession, FHBAtomicEvent
from .serializers import ClinicSessionSerializer, GrowthRecordSerializer
from django.contrib.auth.decorators import login_required
from infants_module.models import Infant
from django.db import models
from datetime import date
from django.utils import timezone
from accounts_module.permission import IsPHM

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
        return redirect('clinic:phm_dashboard')

    return render(
        request,
        'clinic/infant_register.html',
        {
            'title': 'BLueCradle - Infant Registration',
        }
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

        infants.append({
            'infant': infant,
            'age_display': age_display,
            'last_visit': latest_growth.visit_date if latest_growth else None,
            'who_classification': latest_growth.who_classification if latest_growth else 'NORMAL',
            'ml_risk': latest_ml.risk_level if latest_ml else 'NORMAL',
        })

    context = {
        'title': 'BlueCradle - Infant Search',
        'infants': infants,
        'total_count': all_infants.count(),
        'query': query,
    }
    return render(request, 'clinic/infant_search.html', context)

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
    }
    return render(request, 'clinic/infant_detail.html', context)

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
    }
    return render(request, 'clinic/growth_record.html', context)

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
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)