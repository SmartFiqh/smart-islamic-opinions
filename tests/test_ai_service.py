# tests/test_ai_service.py
import pytest
from utils.ai_service import AIService

def test_ai_service_initialization():
    """اختبار تهيئة خدمة الذكاء الاصطناعي"""
    ai = AIService()
    assert ai is not None

def test_generate_response():
    """اختبار توليد الردود"""
    ai = AIService()
    if ai.available:
        response = ai.generate("ما هو حكم الصلاة؟")
        assert response is not None
        assert len(response) > 0
