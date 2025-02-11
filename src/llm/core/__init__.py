"""Core functionality and base classes for the LLM module."""

from .base import (
    BaseTranscriptionProcessor,
    BaseAudioTranslationProcessor,
    BaseTextTranslationProcessor
)
from src.llm.processors.speech.groq_speech_processor import WhisperTranscriptionProcessor
from src.llm.processors.speech.siliconflow_speech_processor import SenseVoiceTranscriptionProcessor
from src.llm.processors.symbol.groq_symbol_processor import GroqSymbolProcessor
from src.llm.processors.symbol.siliconflow_symbol_processor import SiliconFlowSymbolProcessor
from src.llm.processors.translation.siliconflow_translation_processor import TextTranslationProcessor
from src.llm.processors.translation.groq_translation_processor import WhisperTranslationProcessor

__all__ = [
    'BaseTranscriptionProcessor',
    'BaseAudioTranslationProcessor',
    'BaseTextTranslationProcessor',
    'WhisperTranscriptionProcessor',
    'WhisperTranslationProcessor',
    'SenseVoiceTranscriptionProcessor',
    'GroqSymbolProcessor',
    'SiliconFlowSymbolProcessor',
    'TextTranslationProcessor'
]
