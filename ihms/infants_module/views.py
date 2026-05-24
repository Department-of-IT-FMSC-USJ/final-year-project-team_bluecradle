from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from accounts_module.permission import IsPHM
from .models import Infant
from .serializers import InfantSerializer

class InfantListCreateView(APIView):
    permission_classes = [IsPHM]

    def get(self, request):
        # Only return infants registered by the currently logged-in PHM.
        infants = Infant.objects.filter(
            registered_phm=request.user.phm_profile
        )
        serializer = InfantSerializer(infants, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = InfantSerializer(data=request.data)
        if serializer.is_valid():
            # registered_phm and moh_division are set automatically —
            # never accepted from the incoming request.
            serializer.save(
                registered_phm=request.user.phm_profile,
                moh_division=request.user.phm_profile.moh_division
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class InfantDetailView(APIView):
    permission_classes = [IsPHM]

    def get_object(self, phn, request):
        # get_object_or_404 ensures we never expose another PHM's infants.
        return get_object_or_404(
            Infant,
            phn=phn,
            registered_phm=request.user.phm_profile
        )

    def get(self, request, phn):
        infant = self.get_object(phn, request)
        serializer = InfantSerializer(infant)
        return Response(serializer.data)

    def put(self, request, phn):
        infant = self.get_object(phn, request)
        serializer = InfantSerializer(infant, data=request.data, partial=True) # 'partial=True' on PUT — allows the PHM to update a single field (e.g. correcting a name typo) without re-submitting the entire infant record. Without this, every field would be required on every update.
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)