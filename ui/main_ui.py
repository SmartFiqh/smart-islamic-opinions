# ui/main_ui.py
"""الواجهة الرئيسية للتطبيق"""

import streamlit as st
from ui.styles import apply_css
from ui.language_bar import render_language_bar
from ui.search_section import render_search_section
from ui.info_sections import render_info_sections
from translations.ui_texts import UI

def render_app(db, ai, search, ref_manager):
    """عرض واجهة التطبيق الرئيسية"""
    
    # تطبيق التنسيقات
    apply_css()
    
    # شريط اللغات
    lang = render_language_bar()
    T = UI[lang]
    
    # RTL support
    is_rtl = lang in ["ar", "fa", "ur"]
    direction = "rtl" if is_rtl else "ltr"
    
    # رأس الصفحة
    st.markdown(f"""
    <div class="app-header">
        <div style="margin-bottom: 4px;">
            <svg width="80" height="80" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
                <circle cx="60" cy="60" r="56" fill="#0f231c" stroke="#d4a854" stroke-width="3"/>
                <circle cx="60" cy="60" r="49" fill="none" stroke="#d4a854" stroke-width="0.75" opacity="0.5"/>
                <path d="M78 20 A15 15 0 1 0 81 47 A11.5 11.5 0 1 1 78 20 Z" fill="#d4a854"/>
                <path d="M60 50 C46 43 32 45 25 52 V90 C32 83 46 81 60 88 C74 81 88 83 95 90 V52 C88 45 74 43 60 50 Z" fill="none" stroke="#f2e6c9" stroke-width="3.5"/>
                <line x1="60" y1="50" x2="60" y2="88" stroke="#f2e6c9" stroke-width="3"/>
                <path d="M32 59 Q46 55 58 59" stroke="#f2e6c9" stroke-width="1.4" fill="none" opacity="0.65"/>
                <path d="M32 67 Q46 63 58 67" stroke="#f2e6c9" stroke-width="1.4" fill="none" opacity="0.65"/>
                <path d="M32 75 Q46 71 58 75" stroke="#f2e6c9" stroke-width="1.4"
