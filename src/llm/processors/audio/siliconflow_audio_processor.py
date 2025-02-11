import os
import dotenv

from src.llm.processors.speech import SenseVoiceTranscriptionProcessor
from src.llm.processors.translation import TextTranslationProcessor
from src.llm.processors.symbol.siliconflow_symbol_processor import SiliconFlowSymbolProcessor
from src.llm.pipeline import AudioPipelineBuilder

dotenv.load_dotenv()

class SiliconFlowAudioProcessor:
    """SiliconFlow-based audio processor that supports transcription with external translation using SiliconFlow's API services"""
    
    def __init__(self):
        # Initialize API key
        api_key = os.getenv("SILICONFLOW_API_KEY")
        assert api_key, "SILICONFLOW_API_KEY environment variable not set"
        
        # Initialize pipeline with processors
        self.pipeline = (AudioPipelineBuilder()
            .with_transcription(SenseVoiceTranscriptionProcessor(api_key))
            .with_translation(TextTranslationProcessor())
            .with_symbol(SiliconFlowSymbolProcessor())
            .build())
    
    def process_audio(self, audio_buffer, mode: str = "transcriptions", prompt: str = ""):
        """Process audio using the pipeline"""
        return self.pipeline.process(audio_buffer, mode, prompt)
