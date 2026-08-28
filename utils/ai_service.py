# utils/ai_service.py
import google.generativeai as genai
import os
import streamlit as st
from typing import Optional, List, Dict

class AIService:
    """خدمة الذكاء الاصطناعي Gemini"""
    
    def __init__(self):
        self.available = self._init_gemini()
    
    def _init_gemini(self) -> bool:
        """تهيئة Gemini"""
        try:
            api_key = self._get_api_key()
            if api_key:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                return True
        except:
            return False
        return False
    
    def _get_api_key(self) -> Optional[str]:
        """الحصول على مفتاح API"""
        # من Streamlit Secrets
        try:
            return st.secrets["GEMINI_API_KEY"]
        except:
            pass
        
        # من متغيرات البيئة
        return os.getenv("GEMINI_API_KEY")
    
    def generate(self, prompt: str) -> Optional[str]:
        """توليد نص"""
        pass
    
    def embed_text(self, text: str) -> Optional[List[float]]:
        """توليد تمثيل رقمي للنص"""
        pass
