# utils/ai_service.py
"""خدمة الذكاء الاصطناعي Gemini"""

import os
import re
import json
import streamlit as st
from typing import Optional, List, Dict

class AIService:
    def __init__(self):
        self.available = False
        self.model = None
        self._init_gemini()
    
    def _init_gemini(self) -> bool:
        try:
            import google.generativeai as genai
            api_key = self._get_api_key()
            if api_key:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                self.available = True
                return True
        except:
            pass
        return False
    
    def _get_api_key(self) -> Optional[str]:
        try:
            return st.secrets["GEMINI_API_KEY"]
        except:
            pass
        return os.getenv("GEMINI_API_KEY")
    
    def generate(self, prompt: str) -> Optional[str]:
        if not self.available:
            return None
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except:
            return None
    
    def embed_text(self, text: str) -> Optional[List[float]]:
        if not self.available:
            return None
        try:
            import google.generativeai as genai
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_document"
            )
            return result["embedding"]
        except:
            return None
    
    def preprocess_question(self, question: str) -> str:
        """تنظيف السؤال وتحضيره للذكاء الاصطناعي"""
        question = re.sub(r'[،؛؟!\.\,\;\?\!]', ' ', question)
        question = re.sub(r'\s+', ' ', question).strip()
        return question
