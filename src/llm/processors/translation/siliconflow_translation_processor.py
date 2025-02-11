import os
import requests
from dotenv import load_dotenv
from src.llm.core.base import BaseTextTranslationProcessor

load_dotenv()

class TextTranslationProcessor(BaseTextTranslationProcessor):
    """Text-based translation processor using SiliconFlow API"""
    
    def __init__(self):
        self.url = "https://api.siliconflow.cn/v1/chat/completions"
        self.headers = {
            'Authorization': f"Bearer {os.getenv('SILICONFLOW_API_KEY')}",
            "Content-Type": "application/json"
        }
        self.model = os.getenv("SILICONFLOW_TRANSLATE_MODEL", "THUDM/glm-4-9b-chat")
    
    def translate(self, text: str, prompt: str = "") -> str:
        """Translate text to English using SiliconFlow API
        
        Args:
            text: Text to translate
            prompt: Optional prompt to guide translation. If not provided, a default system prompt will be used.
            
        Returns:
            str: Translated text in English
        """
        system_prompt = prompt if prompt else """
        You are a translation assistant.
        Please translate the user's input into English.
        """

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
        }
        
        try:
            response = requests.request("POST", self.url, headers=self.headers, json=payload)
            translated_text = response.json().get('choices', [{}])[0].get('message', {}).get('content', '')
            return translated_text.strip()
        except Exception as e:
            raise Exception(f"Translation failed: {str(e)}")