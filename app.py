# app.py
# -*- coding: utf-8 -*-
"""
الجامع المختصر لآراء المذاهب
التطبيق الرئيسي
"""

import streamlit as st
import os
import sys
from pathlib import Path

# إضافة المجلدات إلى المسار
sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils.database_manager import DatabaseManager
from utils.ai_service import AIService
from utils.search_service import SearchService
from utils.reference_manager import ReferenceManager
from ui.main_ui import render_app

# ============================================================
# إعدادات الصفحة
# ============================================================

st.set_page_config(
    page_title="الجامع المختصر لآراء المذاهب",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# الدالة الرئيسية
# ============================================================

def main():
    """التطبيق الرئيسي."""
    
    # تهيئة الخدمات
    db = DatabaseManager()
    ai = AIService()
    search = SearchService(db, ai)
    ref_manager = ReferenceManager(db, ai)
    
    # عرض الواجهة
    render_app(db, ai, search, ref_manager)


if __name__ == "__main__":
    main()
