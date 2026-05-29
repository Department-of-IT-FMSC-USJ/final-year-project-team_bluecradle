from google import genai
from google.genai import types
from django.conf import settings

_client = None


def get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


PHM_SYSTEM_PROMPT = """You are BlueCradle Assistant, a clinical protocol guide for Public Health \
Midwives in Sri Lanka. Answer only using the provided context from FHB guidelines and WHO standards. \
Use precise clinical language. If the answer is not in the context, say so clearly. Never guess."""

PARENT_SYSTEM_PROMPT = """You are BlueCradle, a friendly health assistant for parents in Sri Lanka. \
Answer only using the provided context. Use simple, clear language a parent can understand. \
Never use clinical jargon. Respond in {language}."""

LANGUAGE_NAMES = {
    'EN': 'English',
    'SI': 'Sinhala',
    'TA': 'Tamil',
}


def build_phm_prompt(user_message: str, context: str, infant_context: str = '') -> str:
    parts = []
    if infant_context:
        parts.append(f"Infant Context:\n{infant_context}")
    if context:
        parts.append(f"Guideline Context:\n{context}")
    else:
        parts.append("Guideline Context:\nNo relevant guidelines found for this query.")
    parts.append(f"PHM Question:\n{user_message}")
    return '\n\n'.join(parts)


def build_parent_prompt(user_message: str, context: str, language: str) -> str:
    parts = []
    if context:
        parts.append(f"Health Information:\n{context}")
    else:
        parts.append("Health Information:\nNo relevant information found for this query.")
    parts.append(f"Parent Question:\n{user_message}")
    return '\n\n'.join(parts)


def get_system_prompt(role: str, language: str) -> str:
    if role == 'PHM':
        return PHM_SYSTEM_PROMPT
    language_name = LANGUAGE_NAMES.get(language, 'English')
    return PARENT_SYSTEM_PROMPT.format(language=language_name)


def call_gemini(system_prompt: str, user_prompt: str) -> str:
    try:
        client = get_client()
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=1000,
                temperature=0.2,
            )
        )
        return response.text
    except Exception as e:
        return f"I'm sorry, I was unable to process your request at this time. Error: {str(e)}"


def get_chatbot_response(
    user_message: str,
    role: str,
    language: str,
    context: str,
    infant_context: str = ''
) -> str:
    system_prompt = get_system_prompt(role, language)
    if role == 'PHM':
        user_prompt = build_phm_prompt(user_message, context, infant_context)
    else:
        user_prompt = build_parent_prompt(user_message, context, language)
    return call_gemini(system_prompt, user_prompt)