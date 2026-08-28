# ui/main_ui.py
import streamlit as st
from ui.language_bar import render_language_bar
from ui.search_section import render_search_section
from ui.info_sections import render_info_sections
from translations.ui_texts import UI

def render_app(db, ai, search, ref_manager):
    """عرض واجهة التطبيق الرئيسية"""
    
    # شريط اللغات
    lang = render_language_bar()
    T = UI[lang]
    
    # رأس الصفحة
    render_header(T)
    
    # تخطيط العمودين
    col_left, col_right = st.columns([5, 7])
    
    with col_left:
        # قسم البحث
        render_search_section(T, db, ai, search)
    
    with col_right:
        # الأقسام التعليمية
        render_info_sections(T)
    
    # التعليقات
    render_comments(T)
