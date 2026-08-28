# utils/database_manager.py
"""إدارة قاعدة البيانات"""

import sqlite3
import json
import csv
import io
from typing import List, Dict, Optional
from pathlib import Path

DB_PATH = "database/fiqh.db"

class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()
    
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        """تهيئة قاعدة البيانات"""
        with self._get_connection() as conn:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS issues (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT,
                    title_ar TEXT, title_en TEXT, title_fr TEXT, 
                    title_fa TEXT, title_ms TEXT, title_ur TEXT,
                    keywords_ar TEXT, keywords_en TEXT, keywords_fr TEXT, 
                    keywords_fa TEXT, keywords_ms TEXT, keywords_ur TEXT,
                    ruling_vs_ar TEXT, ruling_s_ar TEXT, ruling_f_ar TEXT,
                    ruling_vs_en TEXT, ruling_s_en TEXT, ruling_f_en TEXT,
                    ruling_vs_fr TEXT, ruling_s_fr TEXT, ruling_f_fr TEXT,
                    ruling_vs_fa TEXT, ruling_s_fa TEXT, ruling_f_fa TEXT,
                    ruling_vs_ms TEXT, ruling_s_ms TEXT, ruling_f_ms TEXT,
                    ruling_vs_ur TEXT, ruling_s_ur TEXT, ruling_f_ur TEXT,
                    rulings_by_madhab_ar JSON, rulings_by_madhab_en JSON, 
                    rulings_by_madhab_fr JSON, rulings_by_madhab_fa JSON, 
                    rulings_by_madhab_ms JSON, rulings_by_madhab_ur JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            c.execute('CREATE INDEX IF NOT EXISTS idx_issues_topic ON issues(topic)')
            conn.commit()
    
    def load_issues(self, lang: str, topic_filter: str = "all") -> List:
        """تحميل المسائل الفقهية"""
        # سيتم تنفيذها لاحقاً
        return []
