"""
Translation Service.
Handles dynamic translation of safety advice and plans into Tamil and Hindi.
Per spec: 'Translate safety meaning accurately. Preserve severity. Preserve numbers, times, measurements.'
"""

from typing import Optional
from src.infrastructure.llm.gemini_client import gemini_client
from src.infrastructure.llm.prompt_templates import SYSTEM_SAFETY_POLICY
from src.observability.logger import get_logger

logger = get_logger(__name__)


class TranslationService:
    """Uses LLM to perform safety-aware translations of dynamic text."""

    async def translate_text(self, text: str, target_lang: str) -> str:
        """
        Translate safety content to target language (en, ta, hi).
        Rely on Gemini for high-context safety translation.
        Fails back to source text if translation fails.
        """
        if target_lang.lower() == "en" or not text:
            return text

        lang_names = {
            "ta": "Tamil (தமிழ்)",
            "hi": "Hindi (हिन्दी)",
        }

        target_name = lang_names.get(target_lang.lower())
        if not target_name:
            # Unsupported language fallback
            return text

        llm_ready = gemini_client._get_client() is not None
        if not llm_ready:
            return text

        prompt = (
            f"Translate the following emergency safety text into {target_name}.\n\n"
            f"TEXT TO TRANSLATE:\n{text}\n\n"
            f"CRITICAL TRANSLATION RULES:\n"
            f"1. Keep severity and urgency exactly identical to the original.\n"
            f"2. Fully preserve all numbers, hours, percentages, and measurements (e.g. 50mm, 6 hours).\n"
            f"3. Do not make the translation sound less urgent than the English source.\n"
            f"4. If official warnings are mentioned, use the standard recognized target term."
        )

        try:
            translated = await gemini_client.generate_text(
                prompt=prompt,
                system_instruction=SYSTEM_SAFETY_POLICY,
            )
            return translated.strip()
        except Exception as e:
            logger.error("translation_failed_falling_back_to_original", lang=target_lang, error=str(e))
            return text


# Singleton
translation_service = TranslationService()
