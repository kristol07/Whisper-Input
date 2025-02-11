from pynput.keyboard import Controller, Key, Listener
import pyperclip
from ..utils.logger import logger
import time
from .inputState import InputState
import os


class KeyboardManager:
    def __init__(self, on_record_start, on_record_stop, on_translate_start, on_translate_stop, on_reset_state):
        self.keyboard = Controller()
        self.option_pressed = False
        self.shift_pressed = False
        self.temp_text_length = 0  # 用于跟踪临时文本的长度
        self.processing_text = None  # 用于跟踪正在处理的文本
        self.error_message = None  # 用于跟踪错误信息
        self.warning_message = None  # 用于跟踪警告信息
        self.option_press_time = None  # 记录 Option 按下的时间戳
        self.PRESS_DURATION_THRESHOLD = 0.5  # 按键持续时间阈值（秒）
        self.is_checking_duration = False  # 用于控制定时器线程
        self.has_triggered = False  # 用于防止重复触发
        self._original_clipboard = None  # 保存原始剪贴板内容
        
        
        # 回调函数
        self.on_record_start = on_record_start
        self.on_record_stop = on_record_stop
        self.on_translate_start = on_translate_start
        self.on_translate_stop = on_translate_stop
        self.on_reset_state = on_reset_state

        
        # 状态管理
        self._state = InputState.IDLE
        self._state_messages = {
            InputState.IDLE: "",
            InputState.RECORDING: "🎤 正在录音...",
            InputState.RECORDING_TRANSLATE: "🎤 正在录音 (翻译模式)",
            InputState.PROCESSING: "🔄 正在转录...",
            InputState.TRANSLATING: "🔄 正在翻译...",
            InputState.ERROR: lambda msg: f"{msg}",  # 错误消息使用函数动态生成
            InputState.WARNING: lambda msg: f"⚠️ {msg}"  # 警告消息使用函数动态生成
        }

        # 获取系统平台
        sysetem_platform = os.getenv("SYSTEM_PLATFORM")
        if sysetem_platform == "win" :
            self.sysetem_platform = Key.ctrl
            logger.info("System platform: Windows")
        else:
            self.sysetem_platform = Key.cmd
            logger.info("System platform: Mac")
        

        # 获取转录和翻译按钮
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
            self.translations_button = Key.shift  # 设置默认值
            
        # Add double click detection variables
        self.last_press_time_trans = 0  # For transcription button
        self.last_press_time_tran = 0   # For translation button
        self.double_click_threshold = 0.3  # 300ms threshold for double click
        self.exit_flag = False
        self.listener = None
        self.is_recording = False
        self.is_translating = False

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
        """获取当前状态"""
        return self._state
    
    @state.setter
    def state(self, new_state):
        """设置新状态并更新UI"""
        if new_state != self._state:
            self._state = new_state
            
            # 获取状态消息
            message = self._state_messages[new_state]
            
            # 根据状态转换类型显示不同消息
            match new_state:
                case InputState.RECORDING :
                    # 录音状态
                    self.temp_text_length = 0
                    self.type_temp_text(message)
                    self.on_record_start()
                    
                
                case InputState.RECORDING_TRANSLATE:
                    # 翻译,录音状态
                    self.temp_text_length = 0
                    self.type_temp_text(message)
                    self.on_translate_start()

                case InputState.PROCESSING:
                    self._delete_previous_text()
                    self.type_temp_text(message)
                    self.processing_text = message
                    self.on_record_stop()

                case InputState.TRANSLATING:
                    # 翻译状态
                    self._delete_previous_text()                 
                    self.type_temp_text(message)
                    self.processing_text = message
                    self.on_translate_stop()
                
                case InputState.WARNING:
                    # 警告状态
                    message = message(self.warning_message)
                    self._delete_previous_text()
                    self.type_temp_text(message)
                    self.warning_message = None
                    self._schedule_message_clear()     
                
                case InputState.ERROR:
                    # 错误状态
                    message = message(self.error_message)
                    self._delete_previous_text()
                    self.type_temp_text(message)
                    self.error_message = None
                    self._schedule_message_clear()  
            
                case InputState.IDLE:
                    # 空闲状态，清除所有临时文本
                    self.processing_text = None
                
                case _:
                    # 其他状态
                    self.type_temp_text(message)
    
    def _schedule_message_clear(self):
        """计划清除消息"""
        def clear_message():
            time.sleep(2)  # 警告消息显示2秒
            self.state = InputState.IDLE
        
        import threading
        threading.Thread(target=clear_message, daemon=True).start()
    
    def show_warning(self, warning_message):
        """显示警告消息"""
        self.warning_message = warning_message
        self.state = InputState.WARNING
    
    def show_error(self, error_message):
        """显示错误消息"""
        self.error_message = error_message
        self.state = InputState.ERROR
    
    def _save_clipboard(self):
        """保存当前剪贴板内容"""
        if self._original_clipboard is None:
            self._original_clipboard = pyperclip.paste()

    def _restore_clipboard(self):
        """恢复原始剪贴板内容"""
        if self._original_clipboard is not None:
            pyperclip.copy(self._original_clipboard)
            self._original_clipboard = None

    def type_text(self, text, error_message=None):
        """将文字输入到当前光标位置
        
        Args:
            text: 要输入的文本或包含文本和错误信息的元组
            error_message: 错误信息
        """
        # 如果text是元组，说明是从process_audio返回的结果
        if isinstance(text, tuple):
            text, error_message = text
            
        if error_message:
            self.show_error(error_message)
            return
            
        if not text:
            # 如果没有文本且不是错误，可能是录音时长不足
            if self.state in (InputState.PROCESSING, InputState.TRANSLATING):
                self.show_warning("Recording too short, please record at least 1 second")
            return
            
        try:
            logger.info("Inputting transcribed text...")
            self._delete_previous_text()
            
            # 先输入文本和完成标记
            self.type_temp_text(text+" ✅")
            
            # 等待一小段时间确保文本已输入
            time.sleep(0.5)
            
            # 删除完成标记（2个字符：空格和✅）
            self.temp_text_length = 2
            self._delete_previous_text()
            
            # 将转录结果复制到剪贴板
            if os.getenv("KEEP_ORIGINAL_CLIPBOARD", "true").lower() != "true":
                pyperclip.copy(text)
            else:
                # 恢复原始剪贴板内容
                self._restore_clipboard()
            
            logger.info("Text input completed")
            
            # 清理处理状态
            self.state = InputState.IDLE
        except Exception as e:
            logger.error(f"Text input failed: {e}")
            self.show_error(f"❌ Text input failed: {e}")
    
    def _delete_previous_text(self):
        """删除之前输入的临时文本"""
        if self.temp_text_length > 0:
            for _ in range(self.temp_text_length):
                self.keyboard.press(Key.backspace)
                self.keyboard.release(Key.backspace)

        self.temp_text_length = 0
    
    def type_temp_text(self, text):
        """输入临时状态文本"""
        if not text:
            return
            
        # 将文本复制到剪贴板
        pyperclip.copy(text)

        # 模拟 Ctrl + V 粘贴文本
        with self.keyboard.pressed(self.sysetem_platform):
            self.keyboard.press('v')
            self.keyboard.release('v')

        # 更新临时文本长度
        self.temp_text_length = len(text)
    
    def start_duration_check(self):
        """开始检查按键持续时间"""
        if self.is_checking_duration:
            return

        def check_duration():
            while self.is_checking_duration and self.option_pressed:
                current_time = time.time()
                if (not self.has_triggered and 
                    self.option_press_time and 
                    (current_time - self.option_press_time) >= self.PRESS_DURATION_THRESHOLD):
                    
                    # 达到阈值时触发相应功能
                    if self.option_pressed and self.shift_pressed and self.state.can_start_recording:
                        self.state = InputState.RECORDING_TRANSLATE
                        # self.on_translate_start()
                        self.has_triggered = True
                    elif self.option_pressed and not self.shift_pressed and self.state.can_start_recording:
                        self.state = InputState.RECORDING
                        # self.on_record_start()
                        self.has_triggered = True
                
                time.sleep(0.01)  # 短暂休眠以降低 CPU 使用率

        self.is_checking_duration = True
        import threading
        threading.Thread(target=check_duration, daemon=True).start()

    def on_press(self, key):
        """按键按下时的回调"""
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
                    if self.is_recording:
                        # If already recording, stop it
                        self.is_recording = False
                        self.state = InputState.PROCESSING
                        self.on_record_stop()
                    else:
                        # If not recording, start it
                        if not self.is_translating:
                            self.is_recording = True
                            if self._original_clipboard is None:
                                self._original_clipboard = pyperclip.paste()
                            self.state = InputState.RECORDING
                            self.on_record_start()
                self.last_press_time_trans = current_time

            elif key == self.translations_button:
                if current_time - self.last_press_time_tran < self.double_click_threshold:
                    # Double click detected
                    if self.is_translating:
                        # If already translating, stop it
                        self.is_translating = False
                        self.state = InputState.TRANSLATING
                        self.on_translate_stop()
                    else:
                        # If not translating, start it
                        if not self.is_recording:
                            self.is_translating = True
                            if self._original_clipboard is None:
                                self._original_clipboard = pyperclip.paste()
                            self.state = InputState.RECORDING_TRANSLATE
                            self.on_translate_start()
                self.last_press_time_tran = current_time

        except AttributeError:
            pass

    def on_release(self, key):
        """按键释放时的回调"""
        try:
            # We don't need most of the old release logic since we're not using hold anymore
            pass
        except AttributeError:
            pass
    
    def start_listening(self):
        """开始监听键盘事件"""
        logger.info("Started listening for keyboard events")
        self.listener = Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.start()
        self.listener.join()

    def reset_state(self):
        """重置所有状态和临时文本"""
        # 清除临时文本
        self._delete_previous_text()
        
        # 恢复剪贴板
        self._restore_clipboard()
        
        # 重置状态标志
        self.is_recording = False
        self.is_translating = False
        self.option_pressed = False
        self.shift_pressed = False
        self.option_press_time = None
        self.is_checking_duration = False
        self.has_triggered = False
        self.processing_text = None
        self.error_message = None
        self.warning_message = None
        
        # 设置为空闲状态
        self.state = InputState.IDLE

def check_accessibility_permissions():
    """检查是否有辅助功能权限并提供指导"""
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