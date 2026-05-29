from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from accounts_module.permission import IsPHM, IsParent
from infants_module.models import Infant
from clinic_module.models import GrowthRecord
from ml_module.models import MLRiskAssessment
from .models import ChatLog
from .serializers import ChatLogSerializer, ChatRequestSerializer
from .rag import retrieve_chunks
from .gemini import get_chatbot_response


def build_infant_context(phn: str) -> tuple[object | None, str]:
    """
    Fetches infant + latest growth record + ML risk for PHM context.
    Returns (infant_instance, context_string).
    """
    try:
        infant = Infant.objects.get(phn=phn)
    except Infant.DoesNotExist:
        return None, ''

    lines = [
        f"Infant PHN: {infant.phn}",
        f"Name: {infant.full_name}",
        f"Date of Birth: {infant.date_of_birth}",
        f"Sex: {infant.sex}",
    ]

    latest_growth = GrowthRecord.objects.filter(infant=infant).order_by('-visit_date').first()
    if latest_growth:
        lines.append(f"Latest Weight: {latest_growth.weight_kg} kg")
        lines.append(f"Latest Height: {latest_growth.height_cm} cm")
        if latest_growth.muac_mm:
            lines.append(f"MUAC: {latest_growth.muac_mm} mm")
        if latest_growth.whz is not None:
            lines.append(f"WHZ Score: {latest_growth.whz}")

    latest_risk = MLRiskAssessment.objects.filter(infant=infant).order_by('-assessed_at').first()
    if latest_risk:
        lines.append(f"ML Risk Level: {latest_risk.risk_level}")
        lines.append(f"Confidence: {latest_risk.confidence_score:.2f}")

    return infant, '\n'.join(lines)


class PHMChatView(APIView):
    permission_classes = [IsAuthenticated, IsPHM]

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        message = serializer.validated_data['message']
        infant_phn = serializer.validated_data.get('infant_phn', '')

        # RAG retrieval
        rag_result = retrieve_chunks(query=message, role='PHM', language='EN')

        # Infant context if PHN provided
        infant_instance = None
        infant_context = ''
        if infant_phn:
            infant_instance, infant_context = build_infant_context(infant_phn)

        # Gemini call
        bot_response = get_chatbot_response(
            user_message=message,
            role='PHM',
            language='EN',
            context=rag_result['context'],
            infant_context=infant_context
        )

        # Persist to ChatLog
        chat_log = ChatLog.objects.create(
            user=request.user,
            role=ChatLog.Role.PHM,
            infant=infant_instance,
            user_message=message,
            bot_response=bot_response,
            rag_chunks_used=rag_result['chunk_ids'],
            language=ChatLog.Language.EN
        )

        return Response({
            'id': chat_log.id,
            'bot_response': bot_response,
            'rag_chunks_used': rag_result['chunk_ids'],
        }, status=status.HTTP_200_OK)


class ParentChatView(APIView):
    permission_classes = [IsAuthenticated, IsParent]

    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        message = serializer.validated_data['message']
        language = serializer.validated_data.get('language', 'EN')

        # RAG retrieval
        rag_result = retrieve_chunks(query=message, role='PARENT', language=language)

        # Gemini call
        bot_response = get_chatbot_response(
            user_message=message,
            role='PARENT',
            language=language,
            context=rag_result['context']
        )

        # Persist to ChatLog
        chat_log = ChatLog.objects.create(
            user=request.user,
            role=ChatLog.Role.PARENT,
            infant=None,
            user_message=message,
            bot_response=bot_response,
            rag_chunks_used=rag_result['chunk_ids'],
            language=language
        )

        return Response({
            'id': chat_log.id,
            'bot_response': bot_response,
            'rag_chunks_used': rag_result['chunk_ids'],
        }, status=status.HTTP_200_OK)


class ChatHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        logs = ChatLog.objects.filter(user=request.user).order_by('created_at')
        serializer = ChatLogSerializer(logs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)