from abc import ABC, abstractmethod
from typing import Optional
import httpx
from src.llm.core.base import BaseTranscriptionProcessor

class SenseVoiceTranscriptionProcessor(BaseTranscriptionProcessor):
    """SenseVoice-based transcription processor"""
    
    def __init__(self, api_key: str, model: str = "FunAudioLLM/SenseVoiceSmall"):
        self.api_key = api_key
        self.model = model
    
    def transcribe(self, audio_data: bytes, prompt: str = "") -> str:
        """Transcribe audio data to text using SenseVoice model
        
        Args:
            audio_data: Audio data in bytes
            prompt: Optional prompt to guide transcription (not used in SenseVoice)
            
        Returns:
            str: Transcribed text
        """
        transcription_url = "https://api.siliconflow.cn/v1/audio/transcriptions"
        files = {
            'file': ('audio.wav', audio_data),
            'model': (None, self.model)
        }
        headers = {
            'Authorization': f"Bearer {self.api_key}"
        }
        
        with httpx.Client() as client:
            response = client.post(transcription_url, files=files, headers=headers)
            response.raise_for_status()
            return response.json().get('text', 'Failed to get result') 