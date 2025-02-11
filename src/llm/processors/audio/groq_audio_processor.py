import os
import dotenv
from openai import OpenAI

from src.llm.processors.speech import WhisperTranscriptionProcessor
from src.llm.processors.translation import WhisperTranslationProcessor
from src.llm.processors.symbol.groq_symbol_processor import GroqSymbolProcessor
from src.llm.pipeline import AudioPipelineBuilder

dotenv.load_dotenv()

class GroqAudioProcessor:
    """Groq-based audio processor that supports both transcription and translation using Groq's API services"""
    
    def __init__(self):
        # Initialize OpenAI client
        api_key = os.getenv("GROQ_API_KEY")
        base_url = os.getenv("GROQ_BASE_URL")
        assert api_key, "GROQ_API_KEY environment variable not set"
        
        client = OpenAI(
            api_key=api_key,
            base_url=base_url if base_url else None
        )
        
        # Initialize pipeline with processors
        self.pipeline = (AudioPipelineBuilder()
            .with_transcription(WhisperTranscriptionProcessor(client))
            .with_translation(WhisperTranslationProcessor(client))
            .with_symbol(GroqSymbolProcessor())
            .build())
    
    def process_audio(self, audio_buffer, mode: str = "transcriptions", prompt: str = ""):
        """Process audio using the pipeline"""
        return self.pipeline.process(audio_buffer, mode, prompt)