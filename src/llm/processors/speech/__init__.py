"""Transcription processors for audio processing."""

from .groq_speech_processor import WhisperTranscriptionProcessor
from .siliconflow_speech_processor import SenseVoiceTranscriptionProcessor

__all__ = ['WhisperTranscriptionProcessor', 'SenseVoiceTranscriptionProcessor'] 