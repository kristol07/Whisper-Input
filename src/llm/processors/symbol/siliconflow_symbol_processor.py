import os
import requests
from typing import Union, Tuple
from dotenv import load_dotenv
from src.utils.logger import logger
from src.llm.core.base import BaseSymbolProcessor

load_dotenv()

class SiliconFlowSymbolProcessor(BaseSymbolProcessor):
    def __init__(self):
        super().__init__()  # Call parent's __init__
        self.url = "https://api.siliconflow.cn/v1/chat/completions"
        self.headers = {
            'Authorization': f"Bearer {os.getenv('SILICONFLOW_API_KEY')}",
            "Content-Type": "application/json"
        }
        self.model = os.getenv("SILICONFLOW_SYMBOL_MODEL", "THUDM/glm-4-9b-chat")

    def add_symbol(self, text: str) -> Union[str, Tuple[str, Exception]]:
        """Add appropriate punctuation to the input text"""
        system_prompt = """
        Please add appropriate punctuation to the user's input and return it. Apart from this, do not add or modify anything else. Do not translate the user's input. Do not add any explanation. Do not answer the user's question and so on. Just output the user's input with punctuation!
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
            logger.info("Adding punctuation marks...")
            response = requests.request("POST", self.url, headers=self.headers, json=payload)
            result = response.json().get('choices', [{}])[0].get('message', {}).get('content', '')
            return result
        except Exception as e:
            return text, e

    def optimize_result(self, text):
        """Optimize recognition results"""
        system_prompt = """
        You are a speech recognition content input optimizer.
        Please optimize the user's input based on your knowledge.
        And add appropriate punctuation to the user's input.
        Do not change the user's language.
        Do not add any explanation.
        Do not add answer to the user's question,just output the optimized content.
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
            logger.info("Optimizing recognition results...")
            response = requests.request("POST", self.url, headers=self.headers, json=payload)
            result = response.json().get('choices', [{}])[0].get('message', {}).get('content', '')
            return result
        except Exception as e:
            return text, e 