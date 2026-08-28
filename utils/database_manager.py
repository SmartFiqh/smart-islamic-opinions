# utils/database_manager.py
"""إدارة قاعدة البيانات"""

import sqlite3
import json
import csv
import io
import os
from pathlib import Path
from typing import List, Dict, Optional

DB_PATH = "database/fiqh.db"

class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        # تأكد من وجود المجلد قبل إنشاء قاعدة البيانات
        self._ensure_directory()
        self._init_db()
    
    def _ensure_directory(self):
        """تأكد من وجود مجلد database"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(exist_ok=True)
    
    def _get_connection(self):
        """الحصول على اتصال بقاعدة البيانات"""
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
            
            # جدول المراجع (RAG)
            c.execute('''
                CREATE TABLE IF NOT EXISTS reference_chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_title TEXT,
                    madhab_tag TEXT,
                    chunk_text TEXT,
                    embedding JSON,
                    added_at TEXT,
                    chunk_hash TEXT UNIQUE
                )
            ''')
            
            c.execute('CREATE INDEX IF NOT EXISTS idx_issues_topic ON issues(topic)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_chunks_source ON reference_chunks(source_title)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_chunks_madhab ON reference_chunks(madhab_tag)')
            
            conn.commit()
    
    def load_issues(self, lang: str, topic_filter: str = "all") -> List:
        """تحميل المسائل الفقهية"""
        with self._get_connection() as conn:
            c = conn.cursor()
            
            query = f'''
                SELECT id, topic, title_{lang}, keywords_{lang},
                       ruling_vs_{lang}, ruling_s_{lang}, ruling_f_{lang},
                       rulings_by_madhab_{lang}
                FROM issues
            '''
            params = ()
            if topic_filter != "all":
                query += " WHERE topic = ?"
                params = (topic_filter,)
            
            c.execute(query, params)
            rows = c.fetchall()
            
            issues = []
            for row in rows:
                kw = row[f'keywords_{lang}'].split(',') if row[f'keywords_{lang}'] else []
                issues.append({
                    "id": row['id'],
                    "topic": row['topic'],
                    "title": row[f'title_{lang}'],
                    "keywords": [k.strip() for k in kw if k.strip()],
                    "rulings": {
                        "very_short": row[f'ruling_vs_{lang}'],
                        "short": row[f'ruling_s_{lang}'],
                        "full": row[f'ruling_f_{lang}']
                    },
                    "rulings_by_madhab": json.loads(row[f'rulings_by_madhab_{lang}']) if row[f'rulings_by_madhab_{lang}'] else {}
                })
            return issues
    
    def import_from_csv(self, csv_content: bytes) -> int:
        """استيراد بيانات من CSV"""
        with self._get_connection() as conn:
            c = conn.cursor()
            reader = csv.DictReader(io.StringIO(csv_content.decode('utf-8')))
            count = 0
            
            for row in reader:
                c.execute('''
                    INSERT INTO issues (
                        topic, title_ar, title_en, title_fr, title_fa, title_ms, title_ur,
                        keywords_ar, keywords_en, keywords_fr, keywords_fa, keywords_ms, keywords_ur,
                        ruling_vs_ar, ruling_s_ar, ruling_f_ar,
                        ruling_vs_en, ruling_s_en, ruling_f_en,
                        ruling_vs_fr, ruling_s_fr, ruling_f_fr,
                        ruling_vs_fa, ruling_s_fa, ruling_f_fa,
                        ruling_vs_ms, ruling_s_ms, ruling_f_ms,
                        ruling_vs_ur, ruling_s_ur, ruling_f_ur,
                        rulings_by_madhab_ar, rulings_by_madhab_en, rulings_by_madhab_fr,
                        rulings_by_madhab_fa, rulings_by_madhab_ms, rulings_by_madhab_ur
                    ) VALUES (?,?,?,?,?,?,?, ?,?,?,?,?,?, ?,?,?, ?,?,?, ?,?,?, ?,?,?, ?,?,?, ?,?,?, ?,?,?, ?,?,?)
                ''', (
                    row.get("topic", "other"),
                    row.get("title_ar", ""), row.get("title_en", ""), row.get("title_fr", ""),
                    row.get("title_fa", ""), row.get("title_ms", ""), row.get("title_ur", ""),
                    row.get("keywords_ar", ""), row.get("keywords_en", ""), row.get("keywords_fr", ""),
                    row.get("keywords_fa", ""), row.get("keywords_ms", ""), row.get("keywords_ur", ""),
                    row.get("ruling_vs_ar", ""), row.get("ruling_s_ar", ""), row.get("ruling_f_ar", ""),
                    row.get("ruling_vs_en", ""), row.get("ruling_s_en", ""), row.get("ruling_f_en", ""),
                    row.get("ruling_vs_fr", ""), row.get("ruling_s_fr", ""), row.get("ruling_f_fr", ""),
                    row.get("ruling_vs_fa", ""), row.get("ruling_s_fa", ""), row.get("ruling_f_fa", ""),
                    row.get("ruling_vs_ms", ""), row.get("ruling_s_ms", ""), row.get("ruling_f_ms", ""),
                    row.get("ruling_vs_ur", ""), row.get("ruling_s_ur", ""), row.get("ruling_f_ur", ""),
                    row.get("rulings_by_madhab_ar", "{}"), row.get("rulings_by_madhab_en", "{}"),
                    row.get("rulings_by_madhab_fr", "{}"), row.get("rulings_by_madhab_fa", "{}"),
                    row.get("rulings_by_madhab_ms", "{}"), row.get("rulings_by_madhab_ur", "{}")
                ))
                count += 1
            
            conn.commit()
            return count
    
    def add_reference_chunk(self, title: str, madhab_tag: str, chunk: str, embedding: List[float]) -> bool:
        """إضافة مقطع مرجعي"""
        import hashlib
        import datetime
        
        chunk_hash = hashlib.md5(chunk.encode()).hexdigest()
        now = datetime.datetime.utcnow().isoformat()
        
        with self._get_connection() as conn:
            c = conn.cursor()
            try:
                c.execute(
                    """INSERT INTO reference_chunks 
                       (source_title, madhab_tag, chunk_text, embedding, added_at, chunk_hash) 
                       VALUES (?,?,?,?,?,?)""",
                    (title, madhab_tag or "", chunk, json.dumps(embedding), now, chunk_hash)
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False
    
    def get_reference_chunks(self) -> List[Dict]:
        """الحصول على جميع مقاطع المراجع"""
        with self._get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT id, source_title, madhab_tag, chunk_text, embedding FROM reference_chunks")
            rows = c.fetchall()
            return [dict(row) for row in rows]
    
    def count_reference_chunks(self) -> int:
        """عدد مقاطع المراجع"""
        with self._get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM reference_chunks")
            return c.fetchone()[0]
    
    def list_reference_sources(self) -> List[tuple]:
        """قائمة مصادر المراجع"""
        with self._get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT source_title, COUNT(*) FROM reference_chunks GROUP BY source_title")
            return c.fetchall()
