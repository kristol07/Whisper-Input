"""Translation processors for both audio and text translation."""

from .groq_translation_processor import WhisperTranslationProcessor
from .siliconflow_translation_processor import TextTranslationProcessor

__all__ = [
    'WhisperTranslationProcessor',  # For direct audio-to-English translation
    'TextTranslationProcessor'      # For text-to-text translation
] 