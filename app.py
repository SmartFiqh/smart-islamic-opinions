# app.py
import streamlit as st
from utils.database_manager import DatabaseManager
from utils.ai_service import AIService
from utils.search_service import SearchService
from utils.reference_manager import ReferenceManager
from ui.main_ui import render_app

def main():
    # تهيئة الخدمات
    db = DatabaseManager()
    ai = AIService()
    search = SearchService(db, ai)
    ref_manager = ReferenceManager(db, ai)
    
    # عرض الواجهة
    render_app(db, ai, search, ref_manager)

if __name__ == "__main__":
    main()
