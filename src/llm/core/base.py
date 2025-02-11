from abc import ABC, abstractmethod
from typing import Optional, Union, Tuple
import os
from opencc import OpenCC
from src.utils.logger import logger

class BaseTranscriptionProcessor(ABC):
    """Base class for transcription processors"""
    
    @abstractmethod
    def transcribe(self, audio_data: bytes, prompt: str = "") -> str:
        """Transcribe audio data to text
        
        Args:
            audio_data: Audio data in bytes
            prompt: Optional prompt to guide transcription
            
        Returns:
            str: Transcribed text
        """
        pass

class BaseAudioTranslationProcessor(ABC):
    """Base class for audio translation processors"""
    
    @abstractmethod
    def translate(self, audio_data: bytes, prompt: str = "") -> str:
        """Translate audio data directly to target language
        
        Args:
            audio_data: Audio data in bytes
            prompt: Optional prompt to guide translation
            
        Returns:
            str: Translated text
        """
        pass

class BaseTextTranslationProcessor(ABC):
    """Base class for text translation processors"""
    
    @abstractmethod
    def translate(self, text: str, prompt: str = "") -> str:
        """Translate text to target language
        
        Args:
            text: Text to translate
            prompt: Optional prompt to guide translation
            
        Returns:
            str: Translated text
        """
        pass

class BaseSymbolProcessor(ABC):
    """Base class for symbol processors that handle text post-processing"""
    
    def __init__(self):
        self.convert_to_simplified = os.getenv("CONVERT_TO_SIMPLIFIED", "false").lower() == "true"
        self.cc = OpenCC('t2s') if self.convert_to_simplified else None
        self.add_symbol_enabled = os.getenv("ADD_SYMBOL", "false").lower() == "true"
        self.optimize_enabled = os.getenv("OPTIMIZE_RESULT", "false").lower() == "true"
    
    def process(self, text: str) -> str:
        """Process text through all enabled post-processing steps
        
        Args:
            text (str): The input text to process
            
        Returns:
            str: The processed text
        """
        if not text:
            return text
            
        # Convert traditional to simplified Chinese if enabled
        if self.convert_to_simplified and self.cc:
            text = self.cc.convert(text)
            
        # Add punctuation if enabled
        if self.add_symbol_enabled:
            result = self.add_symbol(text)
            if isinstance(result, tuple):
                text, error = result
                logger.error(f"Error adding symbols: {error}")
            else:
                text = result
                logger.info(f"Added punctuation: {text}")
            
        # Optimize result if enabled
        if self.optimize_enabled:
            result = self.optimize_result(text)
            if isinstance(result, tuple):
                text, error = result
                logger.error(f"Error optimizing result: {error}")
            else:
                text = result
                logger.info(f"Optimized result: {text}")
            
        return text
    
    @abstractmethod
    def add_symbol(self, text: str) -> Union[str, Tuple[str, Exception]]:
        """Add appropriate punctuation to the input text
        
        Args:
            text (str): The input text to add punctuation to
            
        Returns:
            Union[str, Tuple[str, Exception]]: The text with added punctuation, or original text and error if failed
        """
        pass
        
    @abstractmethod
    def optimize_result(self, text: str) -> Union[str, Tuple[str, Exception]]:
        """Optimize recognition results
        
        Args:
            text (str): The input text to optimize
            
        Returns:
            Union[str, Tuple[str, Exception]]: The optimized text, or original text and error if failed
        """
        pass 