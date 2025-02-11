from pynput.keyboard import Controller, Key, Listener
import pyperclip
from ..utils.logger import logger
import time
from .inputState import InputState
import os


class KeyboardManager:
    def __init__(self, on_record_start, on_record_stop, on_translate_start, on_translate_stop, on_reset_state):
        self.keyboard = Controller()
        self.temp_text_length = 0  # Track length of temporary text
        self.processing_text = None  # Track text being processed
        self.error_message = None  # Track error messages
        self.warning_message = None  # Track warning messages
        self._original_clipboard = None  # Save original clipboard content
        
        # Callback functions
        self.on_record_start = on_record_start
        self.on_record_stop = on_record_stop
        self.on_translate_start = on_translate_start
        self.on_translate_stop = on_translate_stop
        self.on_reset_state = on_reset_state

        # State management
        self._state = InputState.IDLE
        self._state_messages = {
            InputState.IDLE: "",
            InputState.RECORDING: "🎤 Recording...",
            InputState.RECORDING_TRANSLATE: "🎤 Recording (Translation Mode)",
            InputState.PROCESSING: "🔄 Processing...",
            InputState.TRANSLATING: "🔄 Translating...",
            InputState.ERROR: lambda msg: f"{msg}",  # Error messages generated dynamically
            InputState.WARNING: lambda msg: f"⚠️ {msg}"  # Warning messages generated dynamically
        }

        # Get system platform
        sysetem_platform = os.getenv("SYSTEM_PLATFORM")
        if sysetem_platform == "win" :
            self.sysetem_platform = Key.ctrl
            logger.info("System platform: Windows")
        else:
            self.sysetem_platform = Key.cmd
            logger.info("System platform: Mac")
        

        # Get transcription and translation buttons
        transcriptions_button = os.getenv("TRANSCRIPTIONS_BUTTON")
        try:
            # Handle special key mappings
            if transcriptions_button.lower() == 'alt':
                self.transcriptions_button = Key.alt
            elif transcriptions_button.lower() == 'shift':
                self.transcriptions_button = Key.shift
            elif transcriptions_button.lower() == 'ctrl':
                self.transcriptions_button = Key.ctrl
            else:
                self.transcriptions_button = Key[transcriptions_button]
            logger.info(f"Transcription button configured: {transcriptions_button}")
            logger.debug(f"Transcription button Key object: {self.transcriptions_button}")
        except (KeyError, AttributeError):
            logger.error(f"Invalid transcription button configuration: {transcriptions_button}")

        translations_button = os.getenv("TRANSLATIONS_BUTTON")
        try:
            # Handle special key mappings
            if translations_button.lower() == 'alt':
                self.translations_button = Key.alt
            elif translations_button.lower() == 'shift':
                self.translations_button = Key.shift
            elif translations_button.lower() == 'ctrl':
                self.translations_button = Key.ctrl
            else:
                self.translations_button = Key[translations_button]
            logger.info(f"Translation button configured: {translations_button}")
            logger.debug(f"Translation button Key object: {self.translations_button}")
        except (KeyError, AttributeError):
            logger.error(f"Invalid translation button configuration: {translations_button}")
            logger.info("Falling back to default translation button: shift")
            self.translations_button = Key.shift  # Set default value
            
        # Add double click detection variables
        self.last_press_time_trans = 0  # For transcription button
        self.last_press_time_tran = 0   # For translation button
        self.double_click_threshold = 0.3  # 300ms threshold for double click
        self.exit_flag = False
        self.listener = None

        # Get exit key from env or use default
        exit_button = os.getenv("EXIT_BUTTON", "f6")
        try:
            self.exit_button = Key[exit_button]
            logger.info(f"Exit button configured: {exit_button}")
        except KeyError:
            logger.error(f"Invalid exit button configuration: {exit_button}")
            self.exit_button = Key.f6

        # Log the keyboard controls
        logger.info("=== Keyboard Controls ===")
        logger.info(f"Double click {transcriptions_button}: Start/Stop recording (Transcription mode)")
        logger.info(f"Double click {translations_button}: Start/Stop recording (Translation mode)")
        logger.info(f"Press {exit_button}: Exit program")
        logger.info("=====================")
    
    @property
    def state(self):
        """Get current state"""
        return self._state
    
    @state.setter
    def state(self, new_state):
        """Set new state and update UI"""
        if new_state != self._state:
            self._state = new_state
            
            # Get state message
            message = self._state_messages[new_state]
            
            # Display different messages based on state transition type
            match new_state:
                case InputState.RECORDING :
                    # Recording state
                    self.temp_text_length = 0
                    self.type_temp_text(message)
                    self.on_record_start()
                    
                
                case InputState.RECORDING_TRANSLATE:
                    # Translation, recording state
                    self.temp_text_length = 0
                    self.type_temp_text(message)
                    self.on_translate_start()

                case InputState.PROCESSING:
                    self._delete_previous_text()
                    self.type_temp_text(message)
                    self.processing_text = message
                    self.on_record_stop()

                case InputState.TRANSLATING:
                    # Translation state
                    self._delete_previous_text()                 
                    self.type_temp_text(message)
                    self.processing_text = message
                    self.on_translate_stop()
                
                case InputState.WARNING:
                    # Warning state
                    message = message(self.warning_message)
                    self._delete_previous_text()
                    self.type_temp_text(message)
                    self.warning_message = None
                    self._schedule_message_clear()     
                
                case InputState.ERROR:
                    # Error state
                    message = message(self.error_message)
                    self._delete_previous_text()
                    self.type_temp_text(message)
                    self.error_message = None
                    self._schedule_message_clear()  
            
                case InputState.IDLE:
                    # Idle state, clear all temporary text
                    self.processing_text = None
                
                case _:
                    # Other state
                    self.type_temp_text(message)
    
    def _schedule_message_clear(self):
        """Schedule message clearing"""
        def clear_message():
            time.sleep(2)  # Warning message displays for 2 seconds
            self.state = InputState.IDLE
        
        import threading
        threading.Thread(target=clear_message, daemon=True).start()
    
    def show_warning(self, warning_message):
        """Display warning message"""
        self.warning_message = warning_message
        self.state = InputState.WARNING
    
    def show_error(self, error_message):
        """Display error message"""
        self.error_message = error_message
        self.state = InputState.ERROR
    
    def _save_clipboard(self):
        """Save current clipboard content"""
        if self._original_clipboard is None:
            self._original_clipboard = pyperclip.paste()

    def _restore_clipboard(self):
        """Restore original clipboard content"""
        if self._original_clipboard is not None:
            pyperclip.copy(self._original_clipboard)
            self._original_clipboard = None

    def type_text(self, text, error_message=None):
        """Input text at current cursor position
        
        Args:
            text: Text to input or tuple containing text and error information
            error_message: Error information
        """
        # If text is a tuple, it means it's from process_audio return result
        if isinstance(text, tuple):
            text, error_message = text
            
        if error_message:
            self.show_error(error_message)
            return
            
        if not text:
            # If there's no text and it's not an error, it might be because the recording was too short
            if self.state in (InputState.PROCESSING, InputState.TRANSLATING):
                self.show_warning("Recording too short, please record at least 1 second")
            return
            
        try:
            logger.info("Inputting transcribed text...")
            self._delete_previous_text()
            
            # First input text and completion marker
            completion_marker = " ✅"
            self.type_temp_text(text+completion_marker)
            
            # Wait a short time to ensure text is input
            time.sleep(0.5)
            
            # Delete completion marker (2 characters: space and ✅)
            self.temp_text_length = 2
            self._delete_previous_text()
            
            # Copy transcription result to clipboard
            if os.getenv("KEEP_ORIGINAL_CLIPBOARD", "true").lower() != "true":
                pyperclip.copy(text)
            else:
                # Restore original clipboard content
                self._restore_clipboard()
            
            logger.info("Text input completed")
            
            # Clear processing state
            self.state = InputState.IDLE
        except Exception as e:
            logger.error(f"Text input failed: {e}")
            self.show_error(f"❌ Text input failed: {e}")
    
    def _delete_previous_text(self):
        """Delete previous input temporary text"""
        if self.temp_text_length > 0:
            for _ in range(self.temp_text_length):
                self.keyboard.press(Key.backspace)
                self.keyboard.release(Key.backspace)

        self.temp_text_length = 0
    
    def type_temp_text(self, text):
        """Input temporary state text"""
        if not text:
            return
            
        # Copy text to clipboard
        pyperclip.copy('')  # Clear clipboard first
        time.sleep(0.1)
        pyperclip.copy(text)

        # Simulate Ctrl + V to paste text
        with self.keyboard.pressed(self.sysetem_platform):
            self.keyboard.press('v')
            self.keyboard.release('v')

        # Update temporary text length
        self.temp_text_length = len(text)
    
    def on_press(self, key):
        """Callback for key press events"""
        try:
            logger.info(f"Key pressed: {key}")
            current_time = time.time()

            if key == self.exit_button:
                logger.info("Exit button triggered")
                self.exit_flag = True
                if self.listener:
                    self.listener.stop()
                return False

            elif key == self.transcriptions_button:
                if current_time - self.last_press_time_trans < self.double_click_threshold:
                    # Double click detected
                    if self._state.is_recording:
                        # If recording, stop it
                        self.state = InputState.PROCESSING
                    else:
                        # If not recording and can start, begin recording
                        if self._state.can_start_recording:
                            if self._original_clipboard is None:
                                self._original_clipboard = pyperclip.paste()
                            self.state = InputState.RECORDING
                self.last_press_time_trans = current_time

            elif key == self.translations_button:
                if current_time - self.last_press_time_tran < self.double_click_threshold:
                    # Double click detected
                    if self._state == InputState.RECORDING_TRANSLATE:
                        # If in translation recording, stop it
                        self.state = InputState.TRANSLATING
                    else:
                        # If not recording and can start, begin translation recording
                        if self._state.can_start_recording:
                            if self._original_clipboard is None:
                                self._original_clipboard = pyperclip.paste()
                            self.state = InputState.RECORDING_TRANSLATE
                self.last_press_time_tran = current_time

        except AttributeError:
            pass

    
    def start_listening(self):
        """Start listening for keyboard events"""
        logger.info("Started listening for keyboard events")
        self.listener = Listener(on_press=self.on_press)
        self.listener.start()
        self.listener.join()

    def reset_state(self):
        """Reset all states and temporary text"""
        # Clear temporary text
        self._delete_previous_text()
        
        # Restore clipboard
        self._restore_clipboard()
        
        # Reset state flags
        self.processing_text = None
        self.error_message = None
        self.warning_message = None
        
        # Set to idle state
        self.state = InputState.IDLE

def check_accessibility_permissions():
    """Check for accessibility permissions and provide guidance"""
    logger.warning("\n=== macOS Accessibility Permissions Check ===")
    logger.warning("This application requires accessibility permissions to listen for keyboard events.")
    logger.warning("\nPlease follow these steps to grant permissions:")
    logger.warning("1. Open System Preferences")
    logger.warning("2. Click Privacy & Security")
    logger.warning("3. Click Accessibility in the left sidebar")
    logger.warning("4. Click the lock icon in the bottom right and enter your password")
    logger.warning("5. Find Terminal (or your terminal app) in the right list and check it")
    logger.warning("\nAfter granting permissions, please restart this program.")
    logger.warning("===============================\n") 