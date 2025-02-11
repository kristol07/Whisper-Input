from src.llm.core.base import BaseAudioTranslationProcessor

class WhisperTranslationProcessor(BaseAudioTranslationProcessor):
    """Whisper-based translation processor that directly translates audio to English"""
    
    def __init__(self, client, model="whisper-large-v3"):
        self.client = client
        self.model = model
    
    def translate(self, audio_data: bytes, prompt: str = "") -> str:
        """Translate audio data directly to English using Whisper model
        
        Args:
            audio_data: Audio data in bytes
            prompt: Optional prompt to guide translation
            
        Returns:
            str: Translated text in English
        """
        response = self.client.audio.translations.create(
            model=self.model,
            response_format="text",
            prompt=prompt,
            file=("audio.wav", audio_data)
        )
        return str(response).strip() 