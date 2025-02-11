from typing import Optional, List
from abc import ABC, abstractmethod
import time
from functools import wraps
import threading
from opencc import OpenCC
import os

from src.llm.core.base import (
    BaseTranscriptionProcessor, 
    BaseAudioTranslationProcessor, 
    BaseTextTranslationProcessor,
    BaseSymbolProcessor
)
from src.utils.logger import logger

def timeout_decorator(seconds):
    """Decorator to add timeout to a function"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = [None]
            error = [None]
            completed = threading.Event()

            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    error[0] = e
                finally:
                    completed.set()

            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()

            if completed.wait(seconds):
                if error[0] is not None:
                    raise error[0]
                return result[0]
            raise TimeoutError(f"Operation timeout ({seconds} seconds)")

        return wrapper
    return decorator

class AudioPipeline:
    """Pipeline for processing audio through multiple stages"""
    DEFAULT_TIMEOUT = 20

    def __init__(self):
        self.transcription_processor: Optional[BaseTranscriptionProcessor] = None
        self.translation_processor: Optional[BaseAudioTranslationProcessor | BaseTextTranslationProcessor] = None
        self.symbol_processor: Optional[BaseSymbolProcessor] = None
        self.timeout_seconds = self.DEFAULT_TIMEOUT

    def set_transcription_processor(self, processor: BaseTranscriptionProcessor) -> 'AudioPipeline':
        """Set the transcription processor"""
        self.transcription_processor = processor
        return self

    def set_translation_processor(self, processor: BaseTextTranslationProcessor | BaseAudioTranslationProcessor) -> 'AudioPipeline':
        """Set the translation processor"""
        self.translation_processor = processor
        return self
        
    def set_symbol_processor(self, processor: BaseSymbolProcessor) -> 'AudioPipeline':
        """Set the symbol processor"""
        self.symbol_processor = processor
        return self

    @timeout_decorator(10)
    def _call_api(self, audio_data: bytes, mode: str = "transcriptions", prompt: str = "") -> str:
        """Process audio using appropriate processor"""
        if mode == "translations":
            if not self.translation_processor:
                raise ValueError("Translation processor not configured")
            return self.translation_processor.translate(audio_data, prompt)
        else:
            if not self.transcription_processor:
                raise ValueError("Transcription processor not configured")
            return self.transcription_processor.transcribe(audio_data, prompt)

    def process(self, audio_buffer, mode: str = "transcriptions", prompt: str = "") -> tuple[Optional[str], Optional[str]]:
        """Process audio through the pipeline"""
        try:
            start_time = time.time()
            
            logger.info(f"Processing audio... (mode: {mode})")
            result = self._call_api(audio_buffer, mode, prompt)
            
            # Apply post-processing if symbol processor is configured
            if self.symbol_processor:
                result = self.symbol_processor.process(result)

            logger.info(f"Processing successful ({mode}), time taken: {time.time() - start_time:.1f}s")
            logger.info(f"Result: {result}")
            
            return result, None

        except TimeoutError:
            error_msg = f"❌ Processing timeout ({self.timeout_seconds}s)"
            logger.error(error_msg)
            return None, error_msg
        except Exception as e:
            error_msg = f"❌ {str(e)}"
            logger.error(f"Processing error: {str(e)}", exc_info=True)
            return None, error_msg
        finally:
            audio_buffer.close()

class AudioPipelineBuilder:
    """Builder for creating audio processing pipelines"""
    def __init__(self):
        self.pipeline = AudioPipeline()
    
    def with_transcription(self, processor: BaseTranscriptionProcessor) -> 'AudioPipelineBuilder':
        """Add transcription processor to pipeline"""
        self.pipeline.set_transcription_processor(processor)
        return self
    
    def with_translation(self, processor: BaseTextTranslationProcessor | BaseAudioTranslationProcessor) -> 'AudioPipelineBuilder':
        """Add translation processor to pipeline"""
        self.pipeline.set_translation_processor(processor)
        return self
        
    def with_symbol(self, processor: BaseSymbolProcessor) -> 'AudioPipelineBuilder':
        """Add symbol processor to pipeline"""
        self.pipeline.set_symbol_processor(processor)
        return self
    
    def build(self) -> AudioPipeline:
        """Build and return the configured pipeline"""
        return self.pipeline 