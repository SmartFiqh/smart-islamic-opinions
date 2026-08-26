# app_merged.py
# -*- coding: utf-8 -*-
"""
التطبيق المدمج - يجمع أفضل ميزات كلا البرنامجين
"""

import streamlit as st
import re
import sqlite3
import json
import os
import csv
import io
import datetime
import hashlib
import logging
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import numpy as np

# ============================================================
# إعدادات التسجيل
# ============================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
# إعدادات الصفحة
# ============================================================

st.set_page_config(
    page_title="الجامع المختصر لآراء المذاهب",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# إعدادات البيئة
# ============================================================

DB_PATH = "fiqh.db"
DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# ============================================================
# الاتصال بـ Gemini (اختياري)
# ============================================================

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    GENAI_AVAILABLE = False

def get_gemini_api_key() -> Optional[str]:
    try:
        return st.secrets["GEMINI_API_KEY"]
    except (KeyError, AttributeError):
        pass
    return os.getenv("GEMINI_API_KEY")

GEMINI_API_KEY = get_gemini_api_key()
USE_GEMINI = GEMINI_API_KEY is not None and GENAI_AVAILABLE

if USE_GEMINI:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        logger.info("Gemini AI initialized successfully")
    except Exception as e:
        USE_GEMINI = False
        logger.error(f"Failed to initialize Gemini: {e}")

EMBED_MODEL = "models/text-embedding-004"

# ============================================================
# تطبيع النص العربي (من app -all-school.txt)
# ============================================================

_AR_DIACRITICS = re.compile(r'[\u0617-\u061A\u064B-\u0652\u0670\u06D6-\u06ED\u0640]')
_AR_PUNCT = re.compile(r'[\u060C\u061B\u061F\u066A-\u066D،؛؟!.,:;"\'()\[\]{}؟]')

def normalize_arabic(text: str) -> str:
    """تطبيع النص العربي للتطابق الأفضل."""
    if not text:
        return ""
    t = text.strip()
    t = _AR_DIACRITICS.sub('', t)
    t = re.sub(r'[إأآٱ]', 'ا', t)
    t = t.replace('ى', 'ي')
    t = t.replace('ة', 'ه')
    t = t.replace('ؤ', 'و')
    t = t.replace('ئ', 'ي')
    t = _AR_PUNCT.sub(' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t.lower()

# ============================================================
# فئات البيانات
# ============================================================

@dataclass
class Issue:
    """مسألة فقهية مع محتوى متعدد اللغات."""
    id: int
    topic: str
    title: str
    keywords: List[str]
    rulings: Dict[str, str]
    rulings_by_madhab: Dict[str, Dict[str, str]]

@dataclass
class SearchResult:
    """نتيجة البحث مع بطاقات المذاهب."""
    title: str
    topic: str
    cards: List[Dict[str, str]]

# ============================================================
# اللغات والمذاهب
# ============================================================

LANGS = {
    "العربية": "ar",
    "English": "en",
    "Français": "fr",
    "فارسی": "fa",
    "Bahasa Melayu": "ms",
    "اردو": "ur"
}

LANG_FLAGS = {"ar": "🇸🇦", "en": "🇬🇧", "fr": "🇫🇷", "fa": "🇮🇷", "ms": "🇲🇾", "ur": "🇵🇰"}

MADHHAB_NAMES = {
    "maliki": {"ar": "مالكي", "en": "Maliki", "fr": "Malikite", "fa": "مالکی", "ms": "Maliki", "ur": "مالکی"},
    "shafii": {"ar": "شافعي", "en": "Shafi'i", "fr": "Chaféite", "fa": "شافعی", "ms": "Syafie", "ur": "شافعی"},
    "hanafi": {"ar": "حنفي", "en": "Hanafi", "fr": "Hanafite", "fa": "حنفی", "ms": "Hanafi", "ur": "حنفی"},
    "hanbali": {"ar": "حنبلي", "en": "Hanbali", "fr": "Hanbalite", "fa": "حنبلی", "ms": "Hanbali", "ur": "حنبلی"},
    "zahiri": {"ar": "ظاهري", "en": "Zahiri", "fr": "Zahirite", "fa": "ظاهری", "ms": "Zahiri", "ur": "ظاہری"},
    "jafari": {"ar": "جعفري", "en": "Ja'fari", "fr": "Jaafarite", "fa": "جعفری", "ms": "Jaafari", "ur": "جعفری"},
    "zaidi": {"ar": "زيدي", "en": "Zaidi", "fr": "Zaydite", "fa": "زیدی", "ms": "Zaidi", "ur": "زیدی"},
    "ibadi": {"ar": "إباضي", "en": "Ibadi", "fr": "Ibadite", "fa": "اباضی", "ms": "Ibadi", "ur": "اباضی"},
}

GROUPS = {
    "sunni": {
        "ar": "مذاهب السنة",
        "en": "Sunni Schools",
        "fr": "Écoles sunnites",
        "fa": "مذاهب اهل سنت",
        "ms": "Mazhab Sunni",
        "ur": "اہل سنت کے مذاہب",
        "members": ["maliki", "shafii", "hanafi", "hanbali", "zahiri"]
    },
    "shia": {
        "ar": "مذاهب الشيعة",
        "en": "Shia Schools",
        "fr": "Écoles chiites",
        "fa": "مذاهب شیعه",
        "ms": "Mazhab Syiah",
        "ur": "شیعہ مذاہب",
        "members": ["jafari", "zaidi"]
    },
    "ibadi": {
        "ar": "المذهب الإباضي",
        "en": "Ibadi School",
        "fr": "École ibadite",
        "fa": "مذهب اباضی",
        "ms": "Mazhab Ibadi",
        "ur": "اباضی مذہب",
        "members": ["ibadi"]
    },
}

TOPICS = {
    "ibadat": {"ar": "العبادات", "en": "Acts of Worship", "fr": "Actes d'adoration", "fa": "عبادات", "ms": "Ibadat", "ur": "عبادات"},
    "muamalat": {"ar": "المعاملات", "en": "Transactions", "fr": "Transactions", "fa": "معاملات", "ms": "Muamalat", "ur": "معاملات"},
    "family": {"ar": "الأسرة", "en": "Family", "fr": "Famille", "fa": "خانواده", "ms": "Keluarga", "ur": "خاندان"},
    "other": {"ar": "مواضيع أخرى", "en": "Other Topics", "fr": "Autres sujets", "fa": "موضوعات دیگر", "ms": "Topik Lain", "ur": "دیگر موضوعات"},
}

LEVELS = {
    "very_short": {"ar": "مختصرة (كلمة)", "en": "Very short (one word)", "fr": "Très bref (un mot)", "fa": "بسیار مختصر (یک واژه)", "ms": "Sangat ringkas (satu perkataan)", "ur": "بہت مختصر (ایک لفظ)"},
    "short": {"ar": "مبسطة (سطر)", "en": "Short (one line)", "fr": "Bref (une ligne)", "fa": "ساده (یک خط)", "ms": "Ringkas (satu baris)", "ur": "آسان (ایک سطر)"},
    "full": {"ar": "مفصل (أكثر من سطر)", "en": "Detailed (full)", "fr": "Détaillé (complet)", "fa": "مفصل (چند خط)", "ms": "Terperinci (penuh)", "ur": "تفصیلی (مکمل)"},
}

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# ============================================================
# قائمة UI المدمجة (نفس القائمة من app -all-school.txt مع إضافات)
# ============================================================

UI = {
    "ar": {
        "app_title": "الجامع المختصر لآراء المذاهب",
        "app_subtitle": "منصة لعرض ومقارنة آراء المذاهب الفقهية — للفهم والتبصر، وليست موقع إفتاء.",
        "lang_label": "اللغة",
        "s1_title": "١ — اختر المذهب",
        "group_q": "مذاهب السنة، أم مذاهب الشيعة، أم المذهب الإباضي؟",
        "multi_hint": "💡 يمكنك اختيار أكثر من مذهب لعرض إجاباتها جنباً إلى جنب للمقارنة.",
        "sub_select": "اختر مذهباً واحداً أو أكثر:",
        "s2_title": "٢ — اختر الموضوع",
        "topic_q": "اختر الموضوع الفقهي",
        "s3_title": "٣ — طريقة عرض الإجابة",
        "level_q": "اختر مستوى التفصيل",
        "s4_title": "٤ — اكتب سؤالك",
        "question_placeholder": "مثال: ما حكم صلاة الجماعة؟",
        "search_btn": "🔍 ابحث عن الإجابة",
        "s5_title": "٥ — الإجابة",
        "answer_placeholder": "ستظهر الإجابة هنا بعد كتابة السؤال والضغط على زر البحث.",
        "no_question_warning": "الرجاء كتابة سؤالك أولاً في الفقرة الرابعة.",
        "no_madhab_warning": "الرجاء اختيار مذهب واحد على الأقل.",
        "no_results_warning": "🔍 لم نجد مسألة بهذا الوصف ضمن الموضوع المختار. جرّب كلمات أو صياغة أخرى.",
        "signature": "هذا والله أعلم",
        "note_general": "رأي عام موحّد — لم يُفصّل بعد لكل مذهب",
        "note_madhab": "رأي المذهب {}",
        "ai_badge": "🤖 إجابة الذكاء الاصطناعي",
        "ai_disclaimer": "⚠️ هذه إجابة ولّدها الذكاء الاصطناعي تلقائياً. إنها ليست فتوى ولم تُراجع من عالم شرعي.",
        "ai_generating": "🤖 جاري توليد إجابة بالذكاء الاصطناعي...",
        "ai_unavailable": "ميزة الإجابة التلقائية بالذكاء الاصطناعي غير مفعّلة حالياً.",
        "rag_badge": "📖 مبني على المراجع المرفوعة ({})",
        "rag_expander": "📁 إدارة المراجع (RAG) — للمشرفين",
        "rag_intro": "ارفع نصوص مراجع فقهية؛ سيُقسّمها النظام إلى مقاطع ويبحث فيها دلالياً.",
        "rag_title_label": "عنوان المصدر",
        "rag_madhab_label": "المذهب (اختياري)",
        "rag_text_label": "الصق النص هنا، أو ارفع ملف .txt",
        "rag_file_label": "أو ارفع ملف نصي (.txt)",
        "rag_submit": "إضافة المرجع وفهرسته",
        "rag_processing": "جاري تقسيم النص وحساب التمثيل الرقمي للمقاطع...",
        "rag_success": "✅ أُضيف {} مقطعاً من «{}» إلى فهرس المراجع.",
        "rag_empty_warning": "⚠️ الرجاء لصق نص أو رفع ملف قبل الإضافة.",
        "rag_failed": "❌ تعذّر فهرسة المرجع (تحقق من مفتاح Gemini API).",
        "rag_current_sources": "المصادر المفهرسة حالياً:",
        "rag_no_sources": "لا توجد مراجع مفهرسة بعد.",
        "expander_imams": "📜 الأئمة المؤسسون للمذاهب",
        "expander_countries": "🗺️ الدول الإسلامية والمذهب الرسمي السائد",
        "expander_glossary": "📚 مصطلحات فقهية رئيسية",
        "rules_title": "📘 القواعد والأصول الفقهية الرئيسية",
        "rules_definition": "التعريف",
        "rules_example": "مثال",
        "expander_comments": "💬 أضف تعليقك أو ملاحظتك",
        "rating_label": "قيّم فائدة الإجابة:",
        "comment_placeholder": "اكتب ملاحظتك هنا...",
        "comment_submit": "إرسال التعليق",
        "comment_success": "✅ تم إرسال تعليقك، شكراً لك.",
        "comment_warning": "⚠️ الرجاء كتابة تعليق قبل الإرسال.",
        "comments_title": "تعليقات هذه الجلسة:",
        "comments_note": "ملاحظة: هذه التعليقات محفوظة لجلستك الحالية فقط.",
        "birthplace": "مكان الميلاد",
        "founding_place": "مكان تأسيس المذهب",
        "scholars": "أشهر فقهاء المذهب",
        "official_madhab": "المذهب الرسمي",
        "population": "عدد السكان (تقريبي)",
        "badge_madhabs": "مذاهب",
        "badge_langs": "لغات",
        "badge_countries": "دولة",
        "admin_password": "كلمة مرور المشرف",
        "access_denied": "لا تملك الصلاحية.",
        "source_title": "عنوان المصدر",
        "source_text": "نص المرجع",
        "madhab": "المذهب",
        "add_reference": "إضافة المرجع",
        "reference_added": "تمت إضافة {} مقاطع.",
        "legal_sources": "مصادر التشريع",
        "usul": "أصول الاستدلال",
        "combined_sources": "📜 مصادر التشريع وأصول الاستدلال الفقهي",
    },
    "en": {
        "app_title": "The Concise Compendium of Madhhab Opinions",
        "app_subtitle": "A platform for presenting and comparing juristic (fiqh) opinions — for understanding, not for issuing formal rulings (fatwas).",
        "lang_label": "Language",
        "s1_title": "1 — Choose the Madhhab",
        "group_q": "Sunni schools, Shia schools, or the Ibadi school?",
        "multi_hint": "💡 You can select more than one school to compare their answers side by side.",
        "sub_select": "Choose one or more schools:",
        "s2_title": "2 — Choose the Topic",
        "topic_q": "Choose a fiqh topic",
        "s3_title": "3 — Answer Detail Level",
        "level_q": "Choose the level of detail",
        "s4_title": "4 — Type Your Question",
        "question_placeholder": "Example: What is the ruling on congregational prayer?",
        "search_btn": "🔍 Search for the Ruling",
        "s5_title": "5 — The Answer",
        "answer_placeholder": "The answer will appear here after you type a question and press search.",
        "no_question_warning": "Please type your question first in section 4.",
        "no_madhab_warning": "Please select at least one school.",
        "no_results_warning": "🔍 No matching issue was found. Try different keywords or wording.",
        "signature": "And God knows best",
        "note_general": "A general, unified opinion — not yet detailed per school",
        "note_madhab": "Opinion of the {} school",
        "ai_badge": "🤖 AI-generated answer",
        "ai_disclaimer": "⚠️ This answer was generated automatically by AI. It is not a fatwa and hasn't been reviewed by a scholar.",
        "ai_generating": "🤖 Generating an AI answer...",
        "ai_unavailable": "Automatic AI answering is currently disabled.",
        "rag_badge": "📖 Based on uploaded references ({})",
        "rag_expander": "📁 Manage References (RAG) — Admins",
        "rag_intro": "Upload fiqh reference texts; the system will chunk them and search semantically.",
        "rag_title_label": "Source title",
        "rag_madhab_label": "Madhhab (optional)",
        "rag_text_label": "Paste the text here, or upload a .txt file",
        "rag_file_label": "Or upload a text file (.txt)",
        "rag_submit": "Add and Index Reference",
        "rag_processing": "Chunking text and computing embeddings...",
        "rag_success": "✅ Added {} chunks from \"{}\" to the reference index.",
        "rag_empty_warning": "⚠️ Please paste text or upload a file before adding.",
        "rag_failed": "❌ Failed to index the reference (check your Gemini API key).",
        "rag_current_sources": "Currently indexed sources:",
        "rag_no_sources": "No references indexed yet.",
        "expander_imams": "📜 The Founding Imams of the Schools",
        "expander_countries": "🗺️ Muslim-Majority Countries & Their Prevailing Official School",
        "expander_glossary": "📚 Key Juristic Terms",
        "rules_title": "📘 Key Jurisprudential Rules and Principles",
        "rules_definition": "Definition",
        "rules_example": "Example",
        "expander_comments": "💬 Add Your Comment or Note",
        "rating_label": "Rate how helpful this answer was:",
        "comment_placeholder": "Write your note here...",
        "comment_submit": "Submit Comment",
        "comment_success": "✅ Your comment has been submitted, thank you.",
        "comment_warning": "⚠️ Please write a comment before submitting.",
        "comments_title": "Comments in this session:",
        "comments_note": "Note: these comments are saved for your current session only.",
        "birthplace": "Birthplace",
        "founding_place": "Where the school was founded",
        "scholars": "Prominent scholars of the school",
        "official_madhab": "Official school",
        "population": "Population (approx.)",
        "badge_madhabs": "Schools",
        "badge_langs": "Languages",
        "badge_countries": "Countries",
        "admin_password": "Admin password",
        "access_denied": "Access denied.",
        "source_title": "Source title",
        "source_text": "Reference text",
        "madhab": "Madhhab",
        "add_reference": "Add reference",
        "reference_added": "{} chunks were added.",
        "legal_sources": "Legal sources",
        "usul": "Principles of legal reasoning",
        "combined_sources": "📜 Legal sources and principles of reasoning",
    },
    # ... (continue for fr, fa, ms, ur - same pattern)
}

# ============================================================
# قاعدة البيانات المدمجة
# ============================================================

class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()
        self._ensure_reference_table()
        self._seed_initial_issues()
    
    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self) -> None:
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
    
    def _ensure_reference_table(self) -> None:
        with self._get_connection() as conn:
            c = conn.cursor()
            c.execute("PRAGMA table_info(reference_chunks)")
            columns = [col[1] for col in c.fetchall()]
            for col in ['source_title', 'madhab_tag', 'added_at', 'chunk_hash']:
                if col not in columns:
                    c.execute(f"ALTER TABLE reference_chunks ADD COLUMN {col} TEXT")
            conn.commit()
    
    def _seed_initial_issues(self) -> None:
        """بذر البيانات الأولية (نفس البيانات من app -all-school.txt)"""
        with self._get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM issues")
            if c.fetchone()[0] > 0:
                return
            # ... (إدراج البيانات الأولية - نفس الكود من app -all-school.txt)
            conn.commit()
    
    def load_issues(self, lang: str, topic_filter: str = "all") -> List[Issue]:
        # ... (نفس الكود من app -all-school.txt)
        pass
    
    def import_from_csv(self, csv_content: bytes) -> int:
        # ... (نفس الكود من app -all-school.txt)
        pass
    
    def add_reference_chunk(self, title: str, madhab_tag: str, chunk: str, embedding: List[float]) -> bool:
        # ... (نفس الكود من app -all-school.txt)
        pass
    
    def get_reference_chunks(self) -> List[Dict]:
        # ... (نفس الكود من app -all-school.txt)
        pass
    
    def count_reference_chunks(self) -> int:
        # ... (نفس الكود من app -all-school.txt)
        pass
    
    def list_reference_sources(self) -> List[Tuple[str, int]]:
        # ... (نفس الكود من app -all-school.txt)
        pass

# ============================================================
# خدمة الذكاء الاصطناعي (من app -siqh school-plex.txt)
# ============================================================

class AIService:
    def __init__(self):
        self.available = USE_GEMINI
        if not self.available:
            logger.warning("AI service not available")
    
    def embed_text(self, text: str, task_type: str = "retrieval_document") -> Optional[List[float]]:
        # ... (نفس الكود من app -all-school.txt)
        pass
    
    def embed_texts(self, texts: List[str], task_type: str = "retrieval_document") -> Optional[List[List[float]]]:
        # ... (نفس الكود من app -all-school.txt)
        pass
    
    def generate(self, prompt: str) -> Optional[str]:
        # ... (نفس الكود من app -all-school.txt)
        pass
    
    def preprocess_question(self, question: str) -> str:
        # ... (نفس الكود من app -all-school.txt)
        pass
    
    def semantic_search(self, query: str, issues: List[Issue], lang: str) -> Optional[List[int]]:
        # ... (نفس الكود من app -all-school.txt)
        pass
    
    def rag_generate_answer(self, question: str, lang: str, madhab_codes: List[str], 
                           level: str, T: Dict, chunks: List[Dict]) -> Optional[List[Dict]]:
        # ... (نفس الكود من app -all-school.txt)
        pass
    
    def ai_generate_answer(self, question: str, lang: str, madhab_codes: List[str], 
                          level: str, T: Dict) -> Optional[List[Dict]]:
        # ... (نفس الكود من app -all-school.txt)
        pass

# ============================================================
# خدمة البحث المدمجة
# ============================================================

class SearchService:
    def __init__(self, db: DatabaseManager, ai: AIService):
        self.db = db
        self.ai = ai
        self._cache = {}
    
    def search(self, query: str, topic_filter: str, madhabs: List[str], 
               level: str, lang: str, T: Dict) -> List[SearchResult]:
        # دمج بحث app -all-school.txt (مع تطبيع متقدم) + البحث الدلالي من app -siqh school-plex.txt
        # ... (الكود المدمج)
        pass

# ============================================================
# إدارة المراجع (من app -siqh school-plex.txt)
# ============================================================

class ReferenceManager:
    def __init__(self, db: DatabaseManager, ai: AIService):
        self.db = db
        self.ai = ai
    
    def chunk_text(self, text: str, max_chars: int = 700, overlap: int = 100) -> List[str]:
        # ... (نفس الكود من app -all-school.txt)
        pass
    
    def add_document(self, title: str, madhab_tag: str, raw_text: str) -> int:
        # ... (نفس الكود من app -all-school.txt)
        pass
    
    def retrieve_relevant_chunks(self, query: str, top_k: int = 5, 
                                 min_similarity: float = 0.55) -> List[Dict]:
        # ... (نفس الكود من app -all-school.txt)
        pass

# ============================================================
# البيانات التعليمية (من كلا التطبيقين)
# ============================================================

# الأئمة (من app -all-school.txt مع توسعة)
IMAMS = [
    {
        "name": {"ar": "الإمام مالك بن أنس الأصبحي", "en": "Imam Malik ibn Anas al-Asbahi"},
        "school": MADHHAB_NAMES["maliki"],
        "lifespan": "93 - 179 AH",
        "birthplace": {"ar": "المدينة المنورة", "en": "Medina"},
        "founding_place": {"ar": "المدينة المنورة", "en": "Medina"},
        "scholars": {"ar": "ابن القاسم، سحنون، ابن رشد، القرافي، خليل بن إسحاق", "en": "Ibn al-Qasim, Sahnun, Ibn Rushd, al-Qarafi, Khalil ibn Ishaq"}
    },
    # ... (باقي الأئمة)
]

# الدول (28+ دولة من app -all-school.txt)
COUNTRIES = [
    {"flag": "🇸🇦", "name": {"ar": "السعودية", "en": "Saudi Arabia"}, "madhab": "hanbali", "population": "36.4M"},
    # ... (باقي الدول)
]

# المصطلحات (من app -all-school.txt مع إضافات)
GLOSSARY = [
    {
        "term": {"ar": "الحلال", "en": "Halal (Lawful)"},
        "definition": {"ar": "ما أذن الشارع بفعله أو استعماله", "en": "What the Lawgiver has permitted"},
        "example": {"ar": "البيع المباح، الطعام الحلال", "en": "A permissible sale; lawful food"}
    },
    # ... (باقي المصطلحات)
]

# القواعد الفقهية (من app -all-school.txt مع إضافات)
RULES = [
    {
        "name": {"ar": "اليقين لا يزول بالشك", "en": "Certainty cannot be overridden by doubt"},
        "definition": {"ar": "إذا ثبت أمر بيقين فلا يزول إلا بيقين مثله", "en": "Certainty cannot be overridden by doubt"},
        "example": {"ar": "من تيقن الطهارة وشك في الحدث، يبقى على الطهارة", "en": "If someone is certain of purity and doubts impurity, they remain in a state of purity"}
    },
    # ... (باقي القواعد)
]

# مصادر التشريع وأصول الاستدلال (من app -siqh school-plex.txt)
LEGAL_SOURCES = [
    {"name": {"ar": "القرآن الكريم", "en": "The Qur'an"}, "description": {"ar": "المصدر الأعلى والأول للتشريع الإسلامي.", "en": "The primary and highest source of Islamic law."}},
    # ...
]

USUL = [
    {"name": {"ar": "الأمر والنهي", "en": "Commands and prohibitions"}, "definition": {"ar": "بحث دلالات صيغ الأمر والنهي", "en": "Analysis of commands and prohibitions"}},
    # ...
]

# ============================================================
# دالة عرض القواعد (من app -all-school.txt)
# ============================================================

def display_fiqh_rules(lang: str, T: Dict) -> None:
    # ... (نفس الكود من app -all-school.txt مع إضافة القواعد الجديدة)
    pass

# ============================================================
# الدالة الرئيسية
# ============================================================

def main():
    # تهيئة الخدمات
    db = DatabaseManager()
    ai = AIService()
    search_service = SearchService(db, ai)
    ref_manager = ReferenceManager(db, ai)
    
    # تهيئة حالة الجلسة
    if "lang" not in st.session_state:
        st.session_state.lang = "ar"
    if "session_comments" not in st.session_state:
        st.session_state.session_comments = []
    
    lang = st.session_state.lang
    T = UI[lang]
    
    # شريط اللغات المحسن (من app -siqh school-plex.txt)
    with st.container(border=True):
        lb1, lb2 = st.columns([1, 3])
        with lb1:
            st.markdown(f"**🌐 {T['lang_label']}**")
        with lb2:
            lang_choice = st.radio(
                T["lang_label"],
                list(LANGS.keys()),
                index=list(LANGS.values()).index(st.session_state.lang),
                horizontal=True,
                label_visibility="collapsed",
                format_func=lambda name: f"{LANG_FLAGS.get(LANGS[name], '')} {name}",
                key="lang_radio",
            )
    if LANGS[lang_choice] != st.session_state.lang:
        st.session_state.lang = LANGS[lang_choice]
        st.rerun()
    
    # رأس الصفحة المحسن (دمج من كلا التطبيقين)
    st.markdown(f"""
    <div class="app-header">
        <div class="app-header-accent"></div>
        <div class="app-logo">
            <svg width="84" height="84" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
                <circle cx="60" cy="60" r="56" fill="#0f231c" stroke="#d4a854" stroke-width="3"/>
                <circle cx="60" cy="60" r="49" fill="none" stroke="#d4a854" stroke-width="0.75" opacity="0.5"/>
                <path d="M78 20 A15 15 0 1 0 81 47 A11.5 11.5 0 1 1 78 20 Z" fill="#d4a854"/>
                <path d="M60 50 C46 43 32 45 25 52 V90 C32 83 46 81 60 88 C74 81 88 83 95 90 V52 C88 45 74 43 60 50 Z" fill="none" stroke="#f2e6c9" stroke-width="3.5" stroke-linejoin="round" stroke-linecap="round"/>
                <line x1="60" y1="50" x2="60" y2="88" stroke="#f2e6c9" stroke-width="3"/>
                <path d="M32 59 Q46 55 58 59" stroke="#f2e6c9" stroke-width="1.4" fill="none" opacity="0.65"/>
                <path d="M32 67 Q46 63 58 67" stroke="#f2e6c9" stroke-width="1.4" fill="none" opacity="0.65"/>
                <path d="M32 75 Q46 71 58 75" stroke="#f2e6c9" stroke-width="1.4" fill="none" opacity="0.65"/>
                <path d="M62 59 Q74 55 88 59" stroke="#f2e6c9" stroke-width="1.4" fill="none" opacity="0.65"/>
                <path d="M62 67 Q74 63 88 67" stroke="#f2e6c9" stroke-width="1.4" fill="none" opacity="0.65"/>
                <path d="M62 75 Q74 71 88 75" stroke="#f2e6c9" stroke-width="1.4" fill="none" opacity="0.65"/>
            </svg>
        </div>
        <h1>📖 {T['app_title']}</h1>
        <p class="app-subtitle">{T['app_subtitle']}</p>
        <div class="app-badges">
            <span class="app-badge">📖 8 {T['badge_madhabs']}</span>
            <span class="app-badge">🌐 6 {T['badge_langs']}</span>
            <span class="app-badge">🗺️ {len(COUNTRIES)} {T['badge_countries']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # شريط جانبي (من app -siqh school-plex.txt)
    with st.sidebar:
        # ... (واجهة اختيار المذاهب والموضوعات ومستوى التفاصيل)
        st.markdown(f"### {T['s1_title']}")
        # ... (رمز اختيار المذاهب)
    
    # منطقة البحث الرئيسية (دمج من كلا التطبيقين)
    # ... (الواجهة الرئيسية)
    
    # أقسام المعلومات (دمج من كلا التطبيقين)
    with st.expander(T["expander_imams"]):
        # ... (عرض الأئمة)
    
    with st.expander(T["expander_countries"]):
        # ... (عرض الدول)
    
    with st.expander(T["expander_glossary"]):
        # ... (عرض المصطلحات)
    
    with st.expander(T["combined_sources"]):
        # ... (عرض مصادر التشريع وأصول الاستدلال - جديد)
    
    display_fiqh_rules(lang, T)  # عرض القواعد
    
    # قسم التعليقات (من app -all-school.txt)
    with st.expander(T["expander_comments"]):
        # ... (واجهة التعليقات والتقييم)
    
    # إدارة المراجع (من app -siqh school-plex.txt مع حماية)
    # ... (واجهة إدارة المراجع مع كلمة مرور)

if __name__ == "__main__":
    main()
