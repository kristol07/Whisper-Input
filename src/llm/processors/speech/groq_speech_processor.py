from src.llm.core.base import BaseTranscriptionProcessor

class WhisperTranscriptionProcessor(BaseTranscriptionProcessor):
    """Whisper-based transcription processor"""
    
    def __init__(self, client, model="whisper-large-v3-turbo"):
        self.client = client
        self.model = model
    
    def transcribe(self, audio_data: bytes, prompt: str = "") -> str:
        """Transcribe audio data to text using Whisper model
        
        Args:
            audio_data: Audio data in bytes
            prompt: Optional prompt to guide transcription
            
        Returns:
            str: Transcribed text
        """
        response = self.client.audio.transcriptions.create(
            model=self.model,
            response_format="text",
            prompt=prompt,
            file=("audio.wav", audio_data)
        )
        return str(response).strip()