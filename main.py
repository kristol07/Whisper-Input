import os
import sys
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from src.audio.recorder import AudioRecorder
from src.keyboard.listener import KeyboardManager, check_accessibility_permissions
from src.llm.processors.audio.groq_audio_processor import GroqAudioProcessor
from src.llm.processors.audio.siliconflow_audio_processor import SiliconFlowAudioProcessor
from src.utils.logger import logger

def check_microphone_permissions():
    """Check microphone permissions and provide guidance"""
    logger.warning("\n=== macOS Microphone Permission Check ===")
    logger.warning("This application requires microphone permissions to record audio.")
    logger.warning("\nPlease follow these steps to grant permission:")
    logger.warning("1. Open System Preferences")
    logger.warning("2. Click on Privacy & Security")
    logger.warning("3. Click on Microphone in the left sidebar")
    logger.warning("4. Click the lock icon in the bottom right and enter your password")
    logger.warning("5. Find Terminal (or your terminal app) in the right list and check it")
    logger.warning("\nAfter granting permission, please restart this program.")
    logger.warning("===============================\n")

class AudioProcessorFactory:
    """Factory for creating audio processors based on service platform"""
    
    @staticmethod
    def create(platform: str = "siliconflow") -> Optional[GroqAudioProcessor | SiliconFlowAudioProcessor]:
        """Create an audio processor instance based on platform
        
        Args:
            platform: Service platform name ('groq' or 'siliconflow')
            
        Returns:
            Audio processor instance
            
        Raises:
            ValueError: If platform is invalid
        """
        platform = platform.lower()
        if platform == "groq":
            return GroqAudioProcessor()
        elif platform == "siliconflow":
            return SiliconFlowAudioProcessor()
        else:
            raise ValueError(f"Invalid service platform: {platform}")

class VoiceAssistant:
    """Voice assistant that handles audio recording and processing"""
    
    def __init__(self, audio_processor):
        self.audio_recorder = AudioRecorder()
        self.audio_processor = audio_processor
        self.keyboard_manager = KeyboardManager(
            on_record_start=self._start_recording,
            on_record_stop=self._stop_recording,
            on_translate_start=self._start_recording,
            on_translate_stop=self._stop_translation_recording,
            on_reset_state=self.reset_state
        )
    
    def _start_recording(self):
        """Start audio recording"""
        self.audio_recorder.start_recording()
    
    def _process_audio(self, audio, mode: str = "transcriptions") -> None:
        """Process recorded audio and handle the result
        
        Args:
            audio: Audio data to process
            mode: Processing mode ('transcriptions' or 'translations')
        """
        if audio == "TOO_SHORT":
            logger.warning("Recording too short, resetting state")
            self.keyboard_manager.reset_state()
            return
            
        if not audio:
            logger.error("No audio data, resetting state")
            self.keyboard_manager.reset_state()
            return
            
        result = self.audio_processor.process_audio(
            audio,
            mode=mode,
            prompt=""
        )
        text, error = result if isinstance(result, tuple) else (result, None)
        self.keyboard_manager.type_text(text, error)
    
    def _stop_recording(self):
        """Stop recording and process audio for transcription"""
        audio = self.audio_recorder.stop_recording()
        self._process_audio(audio, mode="transcriptions")
    
    def _stop_translation_recording(self):
        """Stop recording and process audio for translation"""
        audio = self.audio_recorder.stop_recording()
        self._process_audio(audio, mode="translations")

    def reset_state(self):
        """Reset assistant state"""
        self.keyboard_manager.reset_state()
    
    def run(self):
        """Run the voice assistant"""
        try:
            logger.info("=== Voice Assistant Started ===")
            self.keyboard_manager.start_listening()
        except Exception as e:
            logger.error(f"Error running voice assistant: {e}", exc_info=True)
            raise
        finally:
            if self.keyboard_manager.exit_flag:
                logger.info("=== Voice Assistant Stopped ===")
                self.reset_state()

def main():
    try:
        # Create audio processor using factory
        service_platform = os.getenv("SERVICE_PLATFORM", "siliconflow")
        audio_processor = AudioProcessorFactory.create(service_platform)
        
        # Initialize and run voice assistant
        assistant = VoiceAssistant(audio_processor)
        assistant.run()
        
    except KeyboardInterrupt:
        logger.info("Program interrupted by user")
    except Exception as e:
        error_msg = str(e)
        if "Input event monitoring will not be possible" in error_msg:
            check_accessibility_permissions()
            sys.exit(1)
        elif "Cannot access audio device" in error_msg:
            check_microphone_permissions()
            sys.exit(1)
        else:
            logger.error(f"An error occurred: {error_msg}", exc_info=True)
            sys.exit(1)
    finally:
        sys.exit(0)

if __name__ == "__main__":
    main() 