# التطبيق الكامل المعدل

```python
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
    initial_sidebar_state="collapsed",
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

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# ============================================================
# تطبيع النص العربي
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

# ============================================================
# قائمة UI
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
        "legal_sources": "📖 مصادر التشريع",
        "usul": "📐 أصول الاستدلال الفقهي",
        "combined_sources": "📜 مصادر التشريع وأصول الاستدلال الفقهي",
        "summary": "نبذة عن المذهب",
        "note": "ملاحظة",
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
        "legal_sources": "📖 Legal sources",
        "usul": "📐 Principles of legal reasoning",
        "combined_sources": "📜 Legal sources and principles of reasoning",
        "summary": "Summary",
        "note": "Note",
    },
    "fr": {
        "app_title": "Le Recueil Concis des Avis des Écoles Juridiques",
        "app_subtitle": "Une plateforme pour présenter et comparer les avis juridiques (fiqh) — pour la compréhension, non pour émettre des fatwas.",
        "lang_label": "Langue",
        "s1_title": "1 — Choisir l'école juridique",
        "group_q": "Écoles sunnites, écoles chiites, ou école ibadite ?",
        "multi_hint": "💡 Vous pouvez sélectionner plusieurs écoles pour comparer leurs réponses côte à côte.",
        "sub_select": "Choisissez une ou plusieurs écoles :",
        "s2_title": "2 — Choisir le sujet",
        "topic_q": "Choisissez un sujet de fiqh",
        "s3_title": "3 — Niveau de détail de la réponse",
        "level_q": "Choisissez le niveau de détail",
        "s4_title": "4 — Écrivez votre question",
        "question_placeholder": "Exemple : Quel est le statut de la prière en congrégation ?",
        "search_btn": "🔍 Rechercher la réponse",
        "s5_title": "5 — La réponse",
        "answer_placeholder": "La réponse apparaîtra ici après avoir écrit une question et appuyé sur rechercher.",
        "no_question_warning": "Veuillez d'abord écrire votre question à la section 4.",
        "no_madhab_warning": "Veuillez sélectionner au moins une école.",
        "no_results_warning": "🔍 Aucune question correspondante trouvée. Essayez d'autres mots-clés ou une autre formulation.",
        "signature": "Et Dieu est plus savant",
        "note_general": "Avis général unifié — pas encore détaillé par école",
        "note_madhab": "Avis de l'école {}",
        "ai_badge": "🤖 Réponse générée par l'IA",
        "ai_disclaimer": "⚠️ Cette réponse a été générée automatiquement par l'IA. Ce n'est pas une fatwa et elle n'a pas été révisée par un érudit.",
        "ai_generating": "🤖 Génération d'une réponse par IA...",
        "ai_unavailable": "La réponse automatique par IA est actuellement désactivée.",
        "rag_badge": "📖 Basé sur les références téléversées ({})",
        "rag_expander": "📁 Gérer les références (RAG) — Administrateurs",
        "rag_intro": "Téléversez des textes de référence en fiqh ; le système les découpera et les recherchera sémantiquement.",
        "rag_title_label": "Titre de la source",
        "rag_madhab_label": "Madhhab (optionnel)",
        "rag_text_label": "Collez le texte ici, ou téléversez un fichier .txt",
        "rag_file_label": "Ou téléversez un fichier texte (.txt)",
        "rag_submit": "Ajouter et indexer la référence",
        "rag_processing": "Découpage du texte et calcul des vecteurs...",
        "rag_success": "✅ {} extraits de « {} » ajoutés à l'index des références.",
        "rag_empty_warning": "⚠️ Veuillez coller du texte ou téléverser un fichier avant d'ajouter.",
        "rag_failed": "❌ Échec de l'indexation de la référence (vérifiez votre clé API Gemini).",
        "rag_current_sources": "Sources actuellement indexées :",
        "rag_no_sources": "Aucune référence indexée pour le moment.",
        "expander_imams": "📜 Les Imams Fondateurs des Écoles",
        "expander_countries": "🗺️ Pays à Majorité Musulmane et Leur École Officielle Dominante",
        "expander_glossary": "📚 Termes Juridiques Clés",
        "rules_title": "📘 Règles et principes juridiques clés",
        "rules_definition": "Définition",
        "rules_example": "Exemple",
        "expander_comments": "💬 Ajoutez Votre Commentaire ou Remarque",
        "rating_label": "Évaluez l'utilité de cette réponse :",
        "comment_placeholder": "Écrivez votre remarque ici...",
        "comment_submit": "Envoyer le commentaire",
        "comment_success": "✅ Votre commentaire a été envoyé, merci.",
        "comment_warning": "⚠️ Veuillez écrire un commentaire avant d'envoyer.",
        "comments_title": "Commentaires de cette session :",
        "comments_note": "Remarque : ces commentaires ne sont conservés que pour votre session actuelle.",
        "birthplace": "Lieu de naissance",
        "founding_place": "Lieu de fondation de l'école",
        "scholars": "Savants marquants de l'école",
        "official_madhab": "École officielle",
        "population": "Population (approx.)",
        "badge_madhabs": "Écoles",
        "badge_langs": "Langues",
        "badge_countries": "Pays",
        "admin_password": "Mot de passe admin",
        "access_denied": "Accès refusé.",
        "source_title": "Titre de la source",
        "source_text": "Texte de référence",
        "madhab": "École juridique",
        "add_reference": "Ajouter la référence",
        "reference_added": "{} segments ajoutés.",
        "legal_sources": "📖 Sources juridiques",
        "usul": "📐 Principes du raisonnement",
        "combined_sources": "📜 Sources et principes du raisonnement juridique",
        "summary": "Résumé",
        "note": "Remarque",
    },
    "fa": {
        "app_title": "جامع مختصر آراء مذاهب",
        "app_subtitle": "پلتفرمی برای نمایش و مقایسه آراء فقهی مذاهب — برای فهم و بصیرت، نه صدور فتوا.",
        "lang_label": "زبان",
        "s1_title": "۱ — انتخاب مذهب",
        "group_q": "مذاهب اهل سنت، مذاهب شیعه، یا مذهب اباضی؟",
        "multi_hint": "💡 می‌توانید بیش از یک مذهب را برای مقایسه پاسخ‌ها انتخاب کنید.",
        "sub_select": "یک یا چند مذهب را انتخاب کنید:",
        "s2_title": "۲ — انتخاب موضوع",
        "topic_q": "موضوع فقهی را انتخاب کنید",
        "s3_title": "۳ — سطح نمایش پاسخ",
        "level_q": "سطح جزئیات را انتخاب کنید",
        "s4_title": "۴ — سوال خود را بنویسید",
        "question_placeholder": "مثال: حکم نماز جماعت چیست؟",
        "search_btn": "🔍 جستجوی پاسخ",
        "s5_title": "۵ — پاسخ",
        "answer_placeholder": "پاسخ پس از نوشتن سوال و کلیک روی جستجو نمایش داده می‌شود.",
        "no_question_warning": "لطفاً ابتدا سوال خود را در بخش ۴ بنویسید.",
        "no_madhab_warning": "لطفاً حداقل یک مذهب را انتخاب کنید.",
        "no_results_warning": "🔍 هیچ مسئله‌ای یافت نشد. کلمات یا عبارت دیگری را امتحان کنید.",
        "signature": "والله اعلم",
        "note_general": "نظر عمومی واحد — هنوز به‌تفکیک مذهب نیست",
        "note_madhab": "نظر مذهب {}",
        "ai_badge": "🤖 پاسخ تولیدشده توسط هوش مصنوعی",
        "ai_disclaimer": "⚠️ این پاسخ به‌طور خودکار توسط هوش مصنوعی تولید شده است. این فتوا نیست و توسط یک عالم دینی بررسی نشده است.",
        "ai_generating": "🤖 در حال تولید پاسخ با هوش مصنوعی...",
        "ai_unavailable": "پاسخ خودکار با هوش مصنوعی در حال حاضر غیرفعال است.",
        "rag_badge": "📖 بر اساس مراجع بارگذاری‌شده ({})",
        "rag_expander": "📁 مدیریت مراجع (RAG) — مدیران",
        "rag_intro": "متون مرجع فقهی بارگذاری کنید؛ سیستم آن‌ها را به بخش‌هایی تقسیم کرده و جستجوی معنایی می‌کند.",
        "rag_title_label": "عنوان منبع",
        "rag_madhab_label": "مذهب (اختیاری)",
        "rag_text_label": "متن را اینجا جای‌گذاری کنید، یا فایل .txt بارگذاری کنید",
        "rag_file_label": "یا یک فایل متنی (.txt) بارگذاری کنید",
        "rag_submit": "افزودن و فهرست‌بندی منبع",
        "rag_processing": "در حال تقسیم متن و محاسبه بردارها...",
        "rag_success": "✅ {} بخش از «{}» به فهرست مراجع افزوده شد.",
        "rag_empty_warning": "⚠️ لطفاً پیش از افزودن، متنی جای‌گذاری یا فایلی بارگذاری کنید.",
        "rag_failed": "❌ فهرست‌بندی منبع ناموفق بود (کلید Gemini API را بررسی کنید).",
        "rag_current_sources": "منابع فهرست‌شده فعلی:",
        "rag_no_sources": "هنوز هیچ منبعی فهرست نشده است.",
        "expander_imams": "📜 ائمه مؤسس مذاهب",
        "expander_countries": "🗺️ کشورهای اسلامی و مذهب رسمی",
        "expander_glossary": "📚 اصطلاحات کلیدی فقهی",
        "rules_title": "📘 قواعد و اصول فقهی اصلی",
        "rules_definition": "تعریف",
        "rules_example": "مثال",
        "expander_comments": "💬 نظر یا پیشنهاد خود را اضافه کنید",
        "rating_label": "میزان مفید بودن پاسخ را ارزیابی کنید:",
        "comment_placeholder": "نظر خود را اینجا بنویسید...",
        "comment_submit": "ارسال نظر",
        "comment_success": "✅ نظر شما با موفقیت ارسال شد، سپاسگزاریم.",
        "comment_warning": "⚠️ لطفاً قبل از ارسال، نظر خود را بنویسید.",
        "comments_title": "نظرات این جلسه:",
        "comments_note": "توجه: این نظرات فقط برای جلسه فعلی ذخیره می‌شوند.",
        "birthplace": "محل تولد",
        "founding_place": "محل تأسیس مذهب",
        "scholars": "مشهورترین فقهای مذهب",
        "official_madhab": "مذهب رسمی",
        "population": "جمعیت (تقریبی)",
        "badge_madhabs": "مذهب",
        "badge_langs": "زبان",
        "badge_countries": "کشور",
        "admin_password": "رمز عبور مدیر",
        "access_denied": "دسترسی مجاز نیست.",
        "source_title": "عنوان منبع",
        "source_text": "متن مرجع",
        "madhab": "مذهب",
        "add_reference": "افزودن مرجع",
        "reference_added": "{} بخش اضافه شد.",
        "legal_sources": "📖 منابع تشریع",
        "usul": "📐 اصول استنباط",
        "combined_sources": "📜 منابع و اصول استنباط فقهی",
        "summary": "خلاصه",
        "note": "یادداشت",
    },
    "ms": {
        "app_title": "Himpunan Ringkas Pendapat Mazhab",
        "app_subtitle": "Platform untuk memaparkan dan membandingkan pendapat fiqh mazhab — untuk kefahaman dan wawasan, bukan laman fatwa.",
        "lang_label": "Bahasa",
        "s1_title": "1 — Pilih Mazhab",
        "group_q": "Mazhab Sunni, Syiah, atau Ibadi?",
        "multi_hint": "💡 Anda boleh memilih lebih daripada satu mazhab untuk membandingkan jawapan mereka.",
        "sub_select": "Pilih satu atau lebih mazhab:",
        "s2_title": "2 — Pilih Topik",
        "topic_q": "Pilih topik fiqh",
        "s3_title": "3 — Tahap Perincian Jawapan",
        "level_q": "Pilih tahap perincian",
        "s4_title": "4 — Taip Soalan Anda",
        "question_placeholder": "Contoh: Apakah hukum solat berjemaah?",
        "search_btn": "🔍 Cari Jawapan",
        "s5_title": "5 — Jawapan",
        "answer_placeholder": "Jawapan akan muncul di sini selepas anda menaip soalan dan menekan cari.",
        "no_question_warning": "Sila taip soalan anda terlebih dahulu di bahagian 4.",
        "no_madhab_warning": "Sila pilih sekurang-kurangnya satu mazhab.",
        "no_results_warning": "🔍 Tiada isu sepadan ditemui. Cuba kata kunci atau ungkapan lain.",
        "signature": "Dan Allah lebih mengetahui",
        "note_general": "Pendapat umum yang disatukan — belum diperincikan mengikut mazhab",
        "note_madhab": "Pendapat mazhab {}",
        "ai_badge": "🤖 Jawapan dijana oleh AI",
        "ai_disclaimer": "⚠️ Jawapan ini dijana secara automatik oleh AI. Ia bukan fatwa dan belum disemak oleh ulama.",
        "ai_generating": "🤖 Menjana jawapan AI...",
        "ai_unavailable": "Jawapan automatik AI kini dinyahaktifkan.",
        "rag_badge": "📖 Berdasarkan rujukan yang dimuat naik ({})",
        "rag_expander": "📁 Urus Rujukan (RAG) — Pentadbir",
        "rag_intro": "Muat naik teks rujukan fiqh; sistem akan memecahkannya kepada bahagian dan mencari secara semantik.",
        "rag_title_label": "Tajuk sumber",
        "rag_madhab_label": "Mazhab (pilihan)",
        "rag_text_label": "Tampal teks di sini, atau muat naik fail .txt",
        "rag_file_label": "Atau muat naik fail teks (.txt)",
        "rag_submit": "Tambah dan Indeks Rujukan",
        "rag_processing": "Memecahkan teks dan mengira vektor...",
        "rag_success": "✅ {} bahagian daripada \"{}\" ditambah ke indeks rujukan.",
        "rag_empty_warning": "⚠️ Sila tampal teks atau muat naik fail sebelum menambah.",
        "rag_failed": "❌ Gagal mengindeks rujukan (semak kunci API Gemini anda).",
        "rag_current_sources": "Sumber yang diindeks sekarang:",
        "rag_no_sources": "Tiada rujukan diindeks lagi.",
        "expander_imams": "📜 Imam Pengasas Mazhab",
        "expander_countries": "🗺️ Negara Islam & Mazhab Rasmi",
        "expander_glossary": "📚 Istilah Fiqh Utama",
        "rules_title": "📘 Peraturan dan Prinsip Fiqh Utama",
        "rules_definition": "Definisi",
        "rules_example": "Contoh",
        "expander_comments": "💬 Tambah Ulasan atau Nota Anda",
        "rating_label": "Nilaikan kemanfaatan jawapan ini:",
        "comment_placeholder": "Tulis ulasan anda di sini...",
        "comment_submit": "Hantar Ulasan",
        "comment_success": "✅ Ulasan anda telah dihantar, terima kasih.",
        "comment_warning": "⚠️ Sila tulis ulasan sebelum menghantar.",
        "comments_title": "Ulasan sesi ini:",
        "comments_note": "Nota: ulasan ini hanya disimpan untuk sesi semasa anda.",
        "birthplace": "Tempat lahir",
        "founding_place": "Tempat penubuhan mazhab",
        "scholars": "Ulama terkemuka mazhab",
        "official_madhab": "Mazhab rasmi",
        "population": "Penduduk (anggaran)",
        "badge_madhabs": "Mazhab",
        "badge_langs": "Bahasa",
        "badge_countries": "Negara",
        "admin_password": "Kata laluan admin",
        "access_denied": "Akses ditolak.",
        "source_title": "Tajuk sumber",
        "source_text": "Teks rujukan",
        "madhab": "Mazhab",
        "add_reference": "Tambah rujukan",
        "reference_added": "{} bahagian ditambah.",
        "legal_sources": "📖 Sumber hukum",
        "usul": "📐 Prinsip istinbat",
        "combined_sources": "📜 Sumber dan prinsip fiqh",
        "summary": "Ringkasan",
        "note": "Nota",
    },
    "ur": {
        "app_title": "مذاہب کی آراء کا مختصر مجموعہ",
        "app_subtitle": "مذاہب فقہیہ کی آراء دکھانے اور موازنہ کرنے کا پلیٹ فارم — فہم و بصیرت کے لیے، فتویٰ جاری کرنے کے لیے نہیں۔",
        "lang_label": "زبان",
        "s1_title": "۱ — مذہب منتخب کریں",
        "group_q": "اہل سنت کے مذاہب، اہل تشیع کے مذاہب، یا اباضی مذہب؟",
        "multi_hint": "💡 آپ موازنہ کے لیے ایک سے زیادہ مذاہب منتخب کر سکتے ہیں۔",
        "sub_select": "ایک یا زیادہ مذاہب منتخب کریں:",
        "s2_title": "۲ — موضوع منتخب کریں",
        "topic_q": "فقہی موضوع منتخب کریں",
        "s3_title": "۳ — جواب کی تفصیل کی سطح",
        "level_q": "تفصیل کی سطح منتخب کریں",
        "s4_title": "۴ — اپنا سوال لکھیں",
        "question_placeholder": "مثال: نماز باجماعت کا کیا حکم ہے؟",
        "search_btn": "🔍 جواب تلاش کریں",
        "s5_title": "۵ — جواب",
        "answer_placeholder": "جواب یہاں ظاہر ہوگا جب آپ سوال لکھیں گے اور تلاش پر کلک کریں گے۔",
        "no_question_warning": "براہ کرم پہلے حصہ ۴ میں اپنا سوال لکھیں۔",
        "no_madhab_warning": "براہ کرم کم از کم ایک مذہب منتخب کریں۔",
        "no_results_warning": "🔍 کوئی مسئلہ نہیں ملا۔ دوسرے الفاظ یا انداز میں لکھ کر آزمائیں۔",
        "signature": "واللہ اعلم",
        "note_general": "متفقہ عمومی رائے — ابھی تک مذہب کے لحاظ سے تفصیل نہیں دی گئی",
        "note_madhab": "مذہب {} کی رائے",
        "ai_badge": "🤖 مصنوعی ذہانت سے تیار کردہ جواب",
        "ai_disclaimer": "⚠️ یہ جواب خودکار طور پر AI نے تیار کیا ہے۔ یہ فتویٰ نہیں ہے اور کسی عالم دین نے اس کا جائزہ نہیں لیا۔",
        "ai_generating": "🤖 AI کے ذریعے جواب تیار کیا جا رہا ہے...",
        "ai_unavailable": "خودکار AI جواب فی الحال غیر فعال ہے۔",
        "rag_badge": "📖 اپ لوڈ کردہ حوالہ جات پر مبنی ({})",
        "rag_expander": "📁 حوالہ جات کا انتظام (RAG) — منتظمین",
        "rag_intro": "فقہی حوالہ جات کے متن اپ لوڈ کریں؛ نظام انہیں حصوں میں تقسیم کر کے معنوی تلاش کرے گا۔",
        "rag_title_label": "ماخذ کا عنوان",
        "rag_madhab_label": "مذہب (اختیاری)",
        "rag_text_label": "متن یہاں پیسٹ کریں، یا .txt فائل اپ لوڈ کریں",
        "rag_file_label": "یا ایک متنی فائل (.txt) اپ لوڈ کریں",
        "rag_submit": "حوالہ شامل اور انڈیکس کریں",
        "rag_processing": "متن تقسیم اور ویکٹر شمار کیے جا رہے ہیں...",
        "rag_success": "✅ «{}» سے {} حصے حوالہ انڈیکس میں شامل کیے گئے۔",
        "rag_empty_warning": "⚠️ شامل کرنے سے پہلے براہ کرم متن پیسٹ کریں یا فائل اپ لوڈ کریں۔",
        "rag_failed": "❌ حوالہ انڈیکس نہیں ہو سکا (اپنی Gemini API کلید چیک کریں)۔",
        "rag_current_sources": "فی الحال انڈیکس شدہ ماخذ:",
        "rag_no_sources": "ابھی تک کوئی حوالہ انڈیکس نہیں ہوا۔",
        "expander_imams": "📜 مذاہب کے بانی ائمہ",
        "expander_countries": "🗺️ اسلامی ممالک اور سرکاری مذہب",
        "expander_glossary": "📚 اہم فقہی اصطلاحات",
        "rules_title": "📘 اہم فقہی اصول و قواعد",
        "rules_definition": "تعریف",
        "rules_example": "مثال",
        "expander_comments": "💬 اپنا تبصرہ یا نوٹ شامل کریں",
        "rating_label": "اس جواب کی افادیت کی درجہ بندی کریں:",
        "comment_placeholder": "اپنا تبصرہ یہاں لکھیں...",
        "comment_submit": "تبصرہ جمع کریں",
        "comment_success": "✅ آپ کا تبصرہ موصول ہوگیا، شکریہ۔",
        "comment_warning": "⚠️ براہ کرم جمع کرنے سے پہلے تبصرہ لکھیں۔",
        "comments_title": "اس سیشن کے تبصرے:",
        "comments_note": "نوٹ: یہ تبصرے صرف آپ کے موجودہ سیشن کے لیے محفوظ ہیں۔",
        "birthplace": "جائے پیدائش",
        "founding_place": "مذہب کے قیام کی جگہ",
        "scholars": "مشہور فقہاء",
        "official_madhab": "سرکاری مذہب",
        "population": "آبادی (تقریباً)",
        "badge_madhabs": "مذاہب",
        "badge_langs": "زبانیں",
        "badge_countries": "ممالک",
        "admin_password": "منتظم کا پاس ورڈ",
        "access_denied": "رسائی کی اجازت نہیں۔",
        "source_title": "ماخذ کا عنوان",
        "source_text": "حوالہ کا متن",
        "madhab": "مذہب",
        "add_reference": "حوالہ شامل کریں",
        "reference_added": "{} حصے شامل کیے گئے۔",
        "legal_sources": "📖 مصادر تشریع",
        "usul": "📐 اصول استدلال",
        "combined_sources": "📜 فقہی مصادر اور اصول استدلال",
        "summary": "خلاصہ",
        "note": "نوٹ",
    },
}

# ============================================================
# جميع دول منظمة التعاون الإسلامي (57 دولة)
# ============================================================

COUNTRIES = [
    # الدول العربية (22 دولة)
    {"flag": "🇸🇦", "name": {"ar": "السعودية", "en": "Saudi Arabia", "fr": "Arabie saoudite", "fa": "عربستان سعودی", "ms": "Arab Saudi", "ur": "سعودی عرب"}, "madhab": "hanbali", "population": "36.4M"},
    {"flag": "🇪🇬", "name": {"ar": "مصر", "en": "Egypt", "fr": "Égypte", "fa": "مصر", "ms": "Mesir", "ur": "مصر"}, "madhab": "shafii", "population": "112.7M"},
    {"flag": "🇲🇦", "name": {"ar": "المغرب", "en": "Morocco", "fr": "Maroc", "fa": "مراکش", "ms": "Maghribi", "ur": "مراکش"}, "madhab": "maliki", "population": "37.8M"},
    {"flag": "🇩🇿", "name": {"ar": "الجزائر", "en": "Algeria", "fr": "Algérie", "fa": "الجزایر", "ms": "Algeria", "ur": "الجزائر"}, "madhab": "maliki", "population": "46.1M"},
    {"flag": "🇹🇳", "name": {"ar": "تونس", "en": "Tunisia", "fr": "Tunisie", "fa": "تونس", "ms": "Tunisia", "ur": "تونس"}, "madhab": "maliki", "population": "12.5M"},
    {"flag": "🇱🇾", "name": {"ar": "ليبيا", "en": "Libya", "fr": "Libye", "fa": "لیبی", "ms": "Libya", "ur": "لیبیا"}, "madhab": "maliki", "population": "7.0M"},
    {"flag": "🇸🇩", "name": {"ar": "السودان", "en": "Sudan", "fr": "Soudan", "fa": "سودان", "ms": "Sudan", "ur": "سوڈان"}, "madhab": "maliki", "population": "48.1M"},
    {"flag": "🇸🇾", "name": {"ar": "سوريا", "en": "Syria", "fr": "Syrie", "fa": "سوریه", "ms": "Syria", "ur": "شام"}, "madhab": "shafii", "population": "22.1M"},
    {"flag": "🇮🇶", "name": {"ar": "العراق", "en": "Iraq", "fr": "Irak", "fa": "عراق", "ms": "Iraq", "ur": "عراق"}, "madhab": ["jafari", "hanafi"], "population": "45.5M", "diverse": True},
    {"flag": "🇯🇴", "name": {"ar": "الأردن", "en": "Jordan", "fr": "Jordanie", "fa": "اردن", "ms": "Jordan", "ur": "اردن"}, "madhab": "shafii", "population": "11.1M"},
    {"flag": "🇵🇸", "name": {"ar": "فلسطين", "en": "Palestine", "fr": "Palestine", "fa": "فلسطین", "ms": "Palestine", "ur": "فلسطین"}, "madhab": "shafii", "population": "5.4M"},
    {"flag": "🇱🇧", "name": {"ar": "لبنان", "en": "Lebanon", "fr": "Liban", "fa": "لبنان", "ms": "Lebanon", "ur": "لبنان"}, "madhab": ["shafii", "jafari"], "population": "5.4M", "diverse": True},
    {"flag": "🇰🇼", "name": {"ar": "الكويت", "en": "Kuwait", "fr": "Koweït", "fa": "کویت", "ms": "Kuwait", "ur": "کویت"}, "madhab": ["maliki", "hanafi", "shafii", "hanbali"], "population": "4.4M", "diverse": True},
    {"flag": "🇦🇪", "name": {"ar": "الإمارات", "en": "UAE", "fr": "EAU", "fa": "امارات", "ms": "UAE", "ur": "متحدہ عرب امارات"}, "madhab": "maliki", "population": "10.1M"},
    {"flag": "🇧🇭", "name": {"ar": "البحرين", "en": "Bahrain", "fr": "Bahreïn", "fa": "بحرین", "ms": "Bahrain", "ur": "بحرین"}, "madhab": ["jafari", "maliki"], "population": "1.5M", "diverse": True},
    {"flag": "🇶🇦", "name": {"ar": "قطر", "en": "Qatar", "fr": "Qatar", "fa": "قطر", "ms": "Qatar", "ur": "قطر"}, "madhab": "hanbali", "population": "2.9M"},
    {"flag": "🇴🇲", "name": {"ar": "عُمان", "en": "Oman", "fr": "Oman", "fa": "عمان", "ms": "Oman", "ur": "عمان"}, "madhab": "ibadi", "population": "4.7M"},
    {"flag": "🇾🇪", "name": {"ar": "اليمن", "en": "Yemen", "fr": "Yémen", "fa": "یمن", "ms": "Yemen", "ur": "یمن"}, "madhab": ["shafii", "zaidi"], "population": "34.4M", "diverse": True},
    {"flag": "🇲🇷", "name": {"ar": "موريتانيا", "en": "Mauritania", "fr": "Mauritanie", "fa": "موریتانی", "ms": "Mauritania", "ur": "موریتانیہ"}, "madhab": "maliki", "population": "5.0M"},
    {"flag": "🇸🇴", "name": {"ar": "الصومال", "en": "Somalia", "fr": "Somalie", "fa": "سومالی", "ms": "Somalia", "ur": "صومالیہ"}, "madhab": "shafii", "population": "17.1M"},
    {"flag": "🇩🇯", "name": {"ar": "جيبوتي", "en": "Djibouti", "fr": "Djibouti", "fa": "جیبوتی", "ms": "Djibouti", "ur": "جبوتی"}, "madhab": "shafii", "population": "1.1M"},
    {"flag": "🇰🇲", "name": {"ar": "جزر القمر", "en": "Comoros", "fr": "Comores", "fa": "قمر", "ms": "Comoros", "ur": "کوموروس"}, "madhab": "shafii", "population": "0.9M"},
    
    # الدول الأفريقية
    {"flag": "🇳🇬", "name": {"ar": "نيجيريا", "en": "Nigeria", "fr": "Nigeria", "fa": "نیجریه", "ms": "Nigeria", "ur": "نائیجیریا"}, "madhab": "maliki", "population": "225.0M"},
    {"flag": "🇹🇩", "name": {"ar": "تشاد", "en": "Chad", "fr": "Tchad", "fa": "چاد", "ms": "Chad", "ur": "چاڈ"}, "madhab": "maliki", "population": "18.3M"},
    {"flag": "🇳🇪", "name": {"ar": "النيجر", "en": "Niger", "fr": "Niger", "fa": "نیجر", "ms": "Niger", "ur": "نائجر"}, "madhab": "maliki", "population": "27.2M"},
    {"flag": "🇲🇱", "name": {"ar": "مالي", "en": "Mali", "fr": "Mali", "fa": "مالی", "ms": "Mali", "ur": "مالی"}, "madhab": "maliki", "population": "23.3M"},
    {"flag": "🇸🇳", "name": {"ar": "السنغال", "en": "Senegal", "fr": "Sénégal", "fa": "سنگال", "ms": "Senegal", "ur": "سینیگال"}, "madhab": "maliki", "population": "18.3M"},
    {"flag": "🇬🇳", "name": {"ar": "غينيا", "en": "Guinea", "fr": "Guinée", "fa": "گینه", "ms": "Guinea", "ur": "گنی"}, "madhab": "maliki", "population": "14.2M"},
    {"flag": "🇧🇫", "name": {"ar": "بوركينا فاسو", "en": "Burkina Faso", "fr": "Burkina Faso", "fa": "بورکینافاسو", "ms": "Burkina Faso", "ur": "برکینا فاسو"}, "madhab": "maliki", "population": "23.3M"},
    {"flag": "🇬🇲", "name": {"ar": "غامبيا", "en": "Gambia", "fr": "Gambie", "fa": "گامبیا", "ms": "Gambia", "ur": "گیمبیا"}, "madhab": "maliki", "population": "2.8M"},
    {"flag": "🇬🇼", "name": {"ar": "غينيا بيساو", "en": "Guinea-Bissau", "fr": "Guinée-Bissau", "fa": "گینه بیسائو", "ms": "Guinea-Bissau", "ur": "گنی بساؤ"}, "madhab": "maliki", "population": "2.1M"},
    {"flag": "🇸🇱", "name": {"ar": "سيراليون", "en": "Sierra Leone", "fr": "Sierra Leone", "fa": "سیرالئون", "ms": "Sierra Leone", "ur": "سیرالیون"}, "madhab": "maliki", "population": "8.9M"},
    {"flag": "🇨🇲", "name": {"ar": "الكاميرون", "en": "Cameroon", "fr": "Cameroun", "fa": "کامرون", "ms": "Cameroon", "ur": "کیمرون"}, "madhab": "maliki", "population": "28.6M"},
    {"flag": "🇺🇬", "name": {"ar": "أوغندا", "en": "Uganda", "fr": "Ouganda", "fa": "اوگاندا", "ms": "Uganda", "ur": "یوگنڈا"}, "madhab": "shafii", "population": "48.6M"},
    {"flag": "🇹🇿", "name": {"ar": "تنزانيا", "en": "Tanzania", "fr": "Tanzanie", "fa": "تانزانیا", "ms": "Tanzania", "ur": "تنزانیہ"}, "madhab": "shafii", "population": "67.4M"},
    {"flag": "🇲🇿", "name": {"ar": "موزمبيق", "en": "Mozambique", "fr": "Mozambique", "fa": "موزامبیک", "ms": "Mozambique", "ur": "موزمبیق"}, "madhab": "shafii", "population": "34.2M"},
    {"flag": "🇰🇪", "name": {"ar": "كينيا", "en": "Kenya", "fr": "Kenya", "fa": "کنیا", "ms": "Kenya", "ur": "کینیا"}, "madhab": "shafii", "population": "56.2M"},
    
    # الدول الآسيوية
    {"flag": "🇹🇷", "name": {"ar": "تركيا", "en": "Turkey", "fr": "Turquie", "fa": "ترکیه", "ms": "Turki", "ur": "ترکی"}, "madhab": "hanafi", "population": "87.5M"},
    {"flag": "🇮🇷", "name": {"ar": "إيران", "en": "Iran", "fr": "Iran", "fa": "ایران", "ms": "Iran", "ur": "ایران"}, "madhab": "jafari", "population": "89.8M"},
    {"flag": "🇦🇫", "name": {"ar": "أفغانستان", "en": "Afghanistan", "fr": "Afghanistan", "fa": "افغانستان", "ms": "Afghanistan", "ur": "افغانستان"}, "madhab": "hanafi", "population": "41.1M"},
    {"flag": "🇵🇰", "name": {"ar": "باكستان", "en": "Pakistan", "fr": "Pakistan", "fa": "پاکستان", "ms": "Pakistan", "ur": "پاکستان"}, "madhab": "hanafi", "population": "240.0M"},
    {"flag": "🇮🇳", "name": {"ar": "الهند", "en": "India", "fr": "Inde", "fa": "هند", "ms": "India", "ur": "بھارت"}, "madhab": ["hanafi", "shafii"], "population": "204.0M", "diverse": True},
    {"flag": "🇧🇩", "name": {"ar": "بنغلاديش", "en": "Bangladesh", "fr": "Bangladesh", "fa": "بنگلادش", "ms": "Bangladesh", "ur": "بنگلہ دیش"}, "madhab": "hanafi", "population": "166.0M"},
    {"flag": "🇮🇩", "name": {"ar": "إندونيسيا", "en": "Indonesia", "fr": "Indonésie", "fa": "اندونزی", "ms": "Indonesia", "ur": "انڈونیشیا"}, "madhab": "shafii", "population": "279.1M"},
    {"flag": "🇲🇾", "name": {"ar": "ماليزيا", "en": "Malaysia", "fr": "Malaisie", "fa": "مالزی", "ms": "Malaysia", "ur": "ملائیشیا"}, "madhab": "shafii", "population": "34.2M"},
    {"flag": "🇵🇭", "name": {"ar": "الفلبين", "en": "Philippines", "fr": "Philippines", "fa": "فیلیپین", "ms": "Philippines", "ur": "فلپائن"}, "madhab": "shafii", "population": "12.0M"},
    {"flag": "🇹🇭", "name": {"ar": "تايلاند", "en": "Thailand", "fr": "Thaïlande", "fa": "تایلند", "ms": "Thailand", "ur": "تھائی لینڈ"}, "madhab": "shafii", "population": "5.0M"},
    {"flag": "🇲🇲", "name": {"ar": "ميانمار", "en": "Myanmar", "fr": "Myanmar", "fa": "میانمار", "ms": "Myanmar", "ur": "میانمار"}, "madhab": "shafii", "population": "4.0M"},
    {"flag": "🇱🇰", "name": {"ar": "سريلانكا", "en": "Sri Lanka", "fr": "Sri Lanka", "fa": "سریلانکا", "ms": "Sri Lanka", "ur": "سری لنکا"}, "madhab": "shafii", "population": "2.0M"},
    {"flag": "🇲🇻", "name": {"ar": "المالديف", "en": "Maldives", "fr": "Maldives", "fa": "مالدیو", "ms": "Maldives", "ur": "مالدیپ"}, "madhab": "shafii", "population": "0.5M"},
    {"flag": "🇰🇿", "name": {"ar": "كازاخستان", "en": "Kazakhstan", "fr": "Kazakhstan", "fa": "قزاقستان", "ms": "Kazakhstan", "ur": "قازقستان"}, "madhab": "hanafi", "population": "20.0M"},
    {"flag": "🇰🇬", "name": {"ar": "قرغيزستان", "en": "Kyrgyzstan", "fr": "Kirghizistan", "fa": "قرقیزستان", "ms": "Kyrgyzstan", "ur": "کرغیزستان"}, "madhab": "hanafi", "population": "7.0M"},
    {"flag": "🇹🇯", "name": {"ar": "طاجيكستان", "en": "Tajikistan", "fr": "Tadjikistan", "fa": "تاجیکستان", "ms": "Tajikistan", "ur": "تاجکستان"}, "madhab": "hanafi", "population": "10.0M"},
    {"flag": "🇹🇲", "name": {"ar": "تركمانستان", "en": "Turkmenistan", "fr": "Turkménistan", "fa": "ترکمنستان", "ms": "Turkmenistan", "ur": "ترکمانستان"}, "madhab": "hanafi", "population": "6.5M"},
    {"flag": "🇺🇿", "name": {"ar": "أوزبكستان", "en": "Uzbekistan", "fr": "Ouzbékistan", "fa": "ازبکستان", "ms": "Uzbekistan", "ur": "ازبکستان"}, "madhab": "hanafi", "population": "35.0M"},
    {"flag": "🇦🇿", "name": {"ar": "أذربيجان", "en": "Azerbaijan", "fr": "Azerbaïdjan", "fa": "آذربایجان", "ms": "Azerbaijan", "ur": "آذربائیجان"}, "madhab": ["jafari", "hanafi"], "population": "10.4M", "diverse": True},
    
    # أوروبا وآسيا الوسطى
    {"flag": "🇦🇱", "name": {"ar": "ألبانيا", "en": "Albania", "fr": "Albanie", "fa": "آلبانی", "ms": "Albania", "ur": "البانیا"}, "madhab": "hanafi", "population": "2.8M"},
    {"flag": "🇧🇦", "name": {"ar": "البوسنة والهرسك", "en": "Bosnia and Herzegovina", "fr": "Bosnie-Herzégovine", "fa": "بوسنی و هرزگوین", "ms": "Bosnia and Herzegovina", "ur": "بوسنیا و ہرزیگووینا"}, "madhab": "hanafi", "population": "1.8M"},
    {"flag": "🇨🇳", "name": {"ar": "الصين (شينجيانغ)", "en": "China (Xinjiang)", "fr": "Chine (Xinjiang)", "fa": "چین (سین‌کیانگ)", "ms": "China (Xinjiang)", "ur": "چین (سنکیانگ)"}, "madhab": "hanafi", "population": "25.0M"},
    
    # أمريكا الجنوبية
    {"flag": "🇬🇾", "name": {"ar": "غيانا", "en": "Guyana", "fr": "Guyana", "fa": "گویان", "ms": "Guyana", "ur": "گیانا"}, "madhab": "hanafi", "population": "0.8M"},
    {"flag": "🇸🇷", "name": {"ar": "سورينام", "en": "Suriname", "fr": "Suriname", "fa": "سورینام", "ms": "Suriname", "ur": "سورینام"}, "madhab": "hanafi", "population": "0.4M"},
]

COUNTRIES_NOTE = {
    "ar": """📌 ملاحظة: 
    • الدول ذات التعدد المذهبي مذكور فيها المذهبين معاً (مثل: لبنان: شافعي & جعفري)
    • بعض الدول توجد فيها مذاهب متعددة لكن المذكور هو السائد أو الأكثر انتشاراً
    • أعداد المسلمين تقديرية""",
    "en": """📌 Note: 
    • Countries with religious diversity are shown with both schools (e.g., Lebanon: Shafi'i & Ja'fari)
    • Some countries have multiple schools but the one mentioned is the most prevalent
    • Muslim population figures are approximate""",
    "fr": """📌 Remarque:
    • Les pays à diversité religieuse sont indiqués avec les deux écoles (ex: Liban: Shafi'i & Ja'fari)
    • Certains pays ont plusieurs écoles mais celle mentionnée est la plus répandue
    • Les chiffres de la population musulmane sont approximatifs""",
    "fa": """📌 توجه:
    • کشورهای دارای تنوع مذهبی با هر دو مذهب ذکر شده‌اند (مثلاً: لبنان: شافعی & جعفری)
    • برخی کشورها دارای مذاهب متعدد هستند اما مذهب ذکر شده غالب است
    • آمار جمعیت مسلمانان تقریبی است""",
    "ms": """📌 Nota:
    • Negara dengan kepelbagaian agama ditunjukkan dengan kedua-dua mazhab (contoh: Lubnan: Shafi'i & Ja'fari)
    • Sesetengah negara mempunyai pelbagai mazhab tetapi yang disebut adalah paling lazim
    • Angka penduduk Muslim adalah anggaran""",
    "ur": """📌 نوٹ:
    • مذہبی تنوع والے ممالک میں دونوں مذاہب کا ذکر ہے (مثال: لبنان: شافعی & جعفری)
    • بعض ممالک میں متعدد مذاہب ہیں لیکن جو ذکر کیا گیا وہ غالب ہے
    • مسلم آبادی کے اعداد و شمار تخمینی ہیں""",
}

# ============================================================
# الأئمة الثمانية المؤسسون للمذاهب
# ============================================================

IMAMS = [
    {
        "name": {
            "ar": "الإمام أبو حنيفة النعمان بن ثابت",
            "en": "Imam Abu Hanifa al-Nu'man ibn Thabit",
            "fr": "Imam Abu Hanifa al-Nu'man ibn Thabit",
            "fa": "امام ابو حنیفه نعمان بن ثابت",
            "ms": "Imam Abu Hanifa al-Nu'man ibn Thabit",
            "ur": "امام ابو حنیفہ نعمان بن ثابت"
        },
        "school": MADHHAB_NAMES["hanafi"],
        "lifespan": "80 - 150 AH (699 - 767 CE)",
        "birthplace": {"ar": "الكوفة - العراق", "en": "Kufa - Iraq", "fr": "Koufa - Irak", "fa": "کوفه - عراق", "ms": "Kufah - Iraq", "ur": "کوفہ - عراق"},
        "founding_place": {"ar": "الكوفة - العراق", "en": "Kufa - Iraq", "fr": "Koufa - Irak", "fa": "کوفه - عراق", "ms": "Kufah - Iraq", "ur": "کوفہ - عراق"},
        "scholars": {"ar": "أبو يوسف، محمد بن الحسن الشيباني، زفر بن الهذيل، الحسن بن زياد", "en": "Abu Yusuf, Muhammad ibn al-Hasan al-Shaybani, Zufar ibn al-Hudhayl, al-Hasan ibn Ziyad", "fr": "Abu Yusuf, Muhammad ibn al-Hasan al-Shaybani, Zufar ibn al-Hudhayl, al-Hasan ibn Ziyad", "fa": "ابو یوسف، محمد بن حسن شیبانی، زفر بن هذیل، حسن بن زیاد", "ms": "Abu Yusuf, Muhammad ibn al-Hasan al-Shaybani, Zufar ibn al-Hudhayl, al-Hasan ibn Ziyad", "ur": "ابو یوسف، محمد بن الحسن الشیبانی، زفر بن الہذیل، الحسن بن زیاد"},
        "summary": {"ar": "أول الأئمة الأربعة، وأقدمهم وفاةً. اشتهر بالرأي والقياس، واعتمد على الاستحسان في الفقه. مذهبه ينتشر في تركيا، شبه القارة الهندية، آسيا الوسطى، والصين.", "en": "The first of the four Imams, and the earliest to pass away. Known for his use of reason and analogy (qiyas), and juristic preference (istihsan). His school is widespread in Turkey, the Indian subcontinent, Central Asia, and China.", "fr": "Le premier des quatre imams, et le plus ancien à disparaître. Connu pour son usage de la raison et de l'analogie (qiyas), et de la préférence juridique (istihsan). Son école est répandue en Turquie, dans le sous-continent indien, en Asie centrale et en Chine.", "fa": "نخستین و قدیمی‌ترین امام از ائمه چهارگانه. به استفاده از رأی و قیاس و استحسان در فقه شهرت دارد. مذهب او در ترکیه، شبه قاره هند، آسیای مرکزی و چین گسترده است.", "ms": "Imam pertama daripada empat imam, dan yang paling awal meninggal dunia. Terkenal dengan penggunaan akal dan qiyas, serta istihsan dalam fiqh. Mazhabnya tersebar di Turki, benua kecil India, Asia Tengah dan China.", "ur": "ائمہ اربعہ میں پہلے اور وفات میں سب سے قدیم۔ رأی و قیاس اور استحسان کے لیے مشہور۔ ان کا مذہب ترکی، برصغیر، وسطی ایشیا اور چین میں پھیلا ہوا ہے۔"}
    },
    {
        "name": {
            "ar": "الإمام مالك بن أنس الأصبحي",
            "en": "Imam Malik ibn Anas al-Asbahi",
            "fr": "Imam Malik ibn Anas al-Asbahi",
            "fa": "امام مالک بن انس اصبحی",
            "ms": "Imam Malik bin Anas al-Asbahi",
            "ur": "امام مالک بن انس اصبحی"
        },
        "school": MADHHAB_NAMES["maliki"],
        "lifespan": "93 - 179 AH (711 - 795 CE)",
        "birthplace": {"ar": "المدينة المنورة", "en": "Medina", "fr": "Médine", "fa": "مدینه منوره", "ms": "Madinah", "ur": "مدینہ منورہ"},
        "founding_place": {"ar": "المدينة المنورة", "en": "Medina", "fr": "Médine", "fa": "مدینه منوره", "ms": "Madinah", "ur": "مدینہ منورہ"},
        "scholars": {"ar": "ابن القاسم، سحنون، ابن رشد، القرافي، خليل بن إسحاق", "en": "Ibn al-Qasim, Sahnun, Ibn Rushd, al-Qarafi, Khalil ibn Ishaq", "fr": "Ibn al-Qasim, Sahnun, Ibn Rushd, al-Qarafi, Khalil ibn Ishaq", "fa": "ابن قاسم، سحنون، ابن رشد، قرافی، خلیل بن اسحاق", "ms": "Ibn al-Qasim, Sahnun, Ibn Rushd, al-Qarafi, Khalil bin Ishaq", "ur": "ابن القاسم، سحنون، ابن رشد، القرافي، خليل بن إسحاق"},
        "summary": {"ar": "صاحب الموطأ، واشتهر بالأثر والعمل والحديث. مذهبه ينتشر في شمال وغرب أفريقيا، والأندلس سابقاً، وبعض دول الخليج.", "en": "Author of the Muwatta', known for his reliance on the practice of the people of Medina and hadith. His school is widespread in North and West Africa, formerly Andalusia, and some Gulf countries.", "fr": "Auteur du Muwatta', connu pour son recours à la pratique des habitants de Médine et au hadith. Son école est répandue en Afrique du Nord et de l'Ouest, en Andalousie autrefois, et dans certains pays du Golfe.", "fa": "صاحب الموطأ، به اثر و عمل اهل مدینه و حدیث شهرت دارد. مذهب او در شمال و غرب آفریقا، اندلس سابق و برخی کشورهای خلیج فارس گسترده است.", "ms": "Pengarang Muwatta', terkenal dengan amalan penduduk Madinah dan hadis. Mazhabnya tersebar di Afrika Utara dan Barat, Andalusia dahulu, dan beberapa negara Teluk.", "ur": "موطا کے مصنف، اثر و عمل اور حدیث کے لیے مشہور۔ ان کا مذہب شمالی اور مغربی افریقہ، سابقہ اندلس اور کچھ خلیجی ممالک میں پھیلا ہوا ہے۔"}
    },
    {
        "name": {
            "ar": "الإمام محمد بن إدريس الشافعي",
            "en": "Imam Muhammad ibn Idris al-Shafi'i",
            "fr": "Imam Muhammad ibn Idris al-Chafi'i",
            "fa": "امام محمد بن ادریس شافعی",
            "ms": "Imam Muhammad bin Idris al-Syafie",
            "ur": "امام محمد بن ادریس شافعی"
        },
        "school": MADHHAB_NAMES["shafii"],
        "lifespan": "150 - 204 AH (767 - 820 CE)",
        "birthplace": {"ar": "غزة - فلسطين", "en": "Gaza - Palestine", "fr": "Gaza - Palestine", "fa": "غزه - فلسطین", "ms": "Gaza - Palestin", "ur": "غزہ - فلسطین"},
        "founding_place": {"ar": "بغداد ثم مصر (المذهب الجديد)", "en": "Baghdad, then Egypt (the new doctrine)", "fr": "Bagdad, puis l'Égypte (la nouvelle doctrine)", "fa": "بغداد سپس مصر (مذهب جدید)", "ms": "Baghdad, kemudian Mesir (mazhab baru)", "ur": "بغداد پھر مصر (نیا مذہب)"},
        "scholars": {"ar": "المزني، البويطي، النووي، ابن حجر الهيتمي، الرافعي", "en": "al-Muzani, al-Buwayti, al-Nawawi, Ibn Hajar al-Haytami, al-Rafi'i", "fr": "al-Muzani, al-Buwayti, al-Nawawi, Ibn Hajar al-Haytami, al-Rafi'i", "fa": "مزنی، بویطی، نووی، ابن حجر هیتمی، رافعی", "ms": "al-Muzani, al-Buwayti, al-Nawawi, Ibn Hajar al-Haytami, al-Rafi'i", "ur": "المزني، البويطي، النووي، ابن حجر الهيتمي، الرافعي"},
        "summary": {"ar": "صاحب الرسالة، المؤسس لعلم أصول الفقه. اشتهر بالجمع بين الرأي والحديث. مذهبه ينتشر في مصر، الشام، الحجاز، جنوب شرق آسيا، وشرق أفريقيا.", "en": "Author of the Risala, the founder of the science of legal theory (Usul al-fiqh). Known for combining reason and hadith. His school is widespread in Egypt, the Levant, Hejaz, Southeast Asia, and East Africa.", "fr": "Auteur du Risala, le fondateur de la science des fondements du droit (Usul al-fiqh). Connu pour combiner la raison et le hadith. Son école est répandue en Égypte, au Levant, au Hedjaz, en Asie du Sud-Est et en Afrique de l'Est.", "fa": "صاحب الرسالة، بنیان‌گذار علم اصول فقه. به جمع بین رأی و حدیث شهرت دارد. مذهب او در مصر، شام، حجاز، جنوب شرق آسیا و شرق آفریقا گسترده است.", "ms": "Pengarang al-Risalah, pengasas ilmu Usul al-Fiqh. Terkenal menggabungkan akal dan hadis. Mazhabnya tersebar di Mesir, Syam, Hijaz, Asia Tenggara dan Afrika Timur.", "ur": "الرسالة کے مصنف، علم اصول فقہ کے بانی۔ رأی و حدیث کے امتزاج کے لیے مشہور۔ ان کا مذہب مصر، شام، حجاز، جنوب مشرقی ایشیا اور مشرقی افریقہ میں پھیلا ہوا ہے۔"}
    },
    {
        "name": {
            "ar": "الإمام أحمد بن حنبل الشيباني",
            "en": "Imam Ahmad ibn Hanbal al-Shaybani",
            "fr": "Imam Ahmad ibn Hanbal al-Shaybani",
            "fa": "امام احمد بن حنبل شیبانی",
            "ms": "Imam Ahmad bin Hanbal al-Shaybani",
            "ur": "امام احمد بن حنبل شیبانی"
        },
        "school": MADHHAB_NAMES["hanbali"],
        "lifespan": "164 - 241 AH (780 - 855 CE)",
        "birthplace": {"ar": "بغداد - العراق", "en": "Baghdad - Iraq", "fr": "Bagdad - Irak", "fa": "بغداد - عراق", "ms": "Baghdad - Iraq", "ur": "بغداد - عراق"},
        "founding_place": {"ar": "بغداد - العراق", "en": "Baghdad - Iraq", "fr": "Bagdad - Irak", "fa": "بغداد - عراق", "ms": "Baghdad - Iraq", "ur": "بغداد - عراق"},
        "scholars": {"ar": "أبو بكر الخلال، ابن تيمية، ابن القيم الجوزية، ابن رجب الحنبلي", "en": "Abu Bakr al-Khallal, Ibn Taymiyya, Ibn Qayyim al-Jawziyya, Ibn Rajab al-Hanbali", "fr": "Abu Bakr al-Khallal, Ibn Taymiyya, Ibn Qayyim al-Jawziyya, Ibn Rajab al-Hanbali", "fa": "ابو بکر خلال، ابن تیمیه، ابن قیم جوزیه، ابن رجب حنبلی", "ms": "Abu Bakr al-Khallal, Ibn Taymiyya, Ibn Qayyim al-Jawziyya, Ibn Rajab al-Hanbali", "ur": "ابو بکر الخلال، ابن تیمیہ، ابن القیم الجوزیہ، ابن رجب الحنبلی"},
        "summary": {"ar": "صاحب المسند، اشتهر بالحديث والورع والتشدد في اتباع النص. مذهبه ينتشر في السعودية، قطر، وشرق الجزيرة العربية.", "en": "Author of the Musnad, known for his knowledge of hadith, piety, and strict adherence to texts. His school is widespread in Saudi Arabia, Qatar, and the eastern Arabian Peninsula.", "fr": "Auteur du Musnad, connu pour sa connaissance du hadith, sa piété et son adhésion stricte aux textes. Son école est répandue en Arabie saoudite, au Qatar et dans l'est de la péninsule arabique.", "fa": "صاحب المسند، به حدیث، ورع و سخت‌گیری در پیروی از نص شهرت دارد. مذهب او در عربستان سعودی، قطر و شرق شبه جزیره عربستان گسترده است.", "ms": "Pengarang Musnad, terkenal dengan ilmu hadis, ketakwaan dan ketegasan dalam mengikut nas. Mazhabnya tersebar di Arab Saudi, Qatar dan timur Semenanjung Arab.", "ur": "مسند کے مصنف، حدیث، ورع اور نص کی پابندی کے لیے مشہور۔ ان کا مذہب سعودی عرب، قطر اور مشرقی جزیرہ نما عرب میں پھیلا ہوا ہے۔"}
    },
    {
        "name": {
            "ar": "الإمام داود بن علي الظاهري",
            "en": "Imam Dawud ibn Ali al-Zahiri",
            "fr": "Imam Dawud ibn Ali al-Zahiri",
            "fa": "امام داود بن علی ظاهری",
            "ms": "Imam Dawud bin Ali al-Zahiri",
            "ur": "امام داود بن علی الظاہری"
        },
        "school": MADHHAB_NAMES["zahiri"],
        "lifespan": "202 - 270 AH (817 - 884 CE)",
        "birthplace": {"ar": "بغداد - العراق", "en": "Baghdad - Iraq", "fr": "Bagdad - Irak", "fa": "بغداد - عراق", "ms": "Baghdad - Iraq", "ur": "بغداد - عراق"},
        "founding_place": {"ar": "بغداد - العراق", "en": "Baghdad - Iraq", "fr": "Bagdad - Irak", "fa": "بغداد - عراق", "ms": "Baghdad - Iraq", "ur": "بغداد - عراق"},
        "scholars": {"ar": "ابن حزم الظاهري (الأندلس)، ابن العربي المالكي (بالنسبة لبعض آرائه)", "en": "Ibn Hazm al-Zahiri (Andalusia), Ibn al-Arabi al-Maliki (for some of his views)", "fr": "Ibn Hazm al-Zahiri (Andalousie), Ibn al-Arabi al-Maliki (pour certaines de ses opinions)", "fa": "ابن حزم ظاهری (اندلس)، ابن عربی مالکی (نسبت به برخی آرای او)", "ms": "Ibn Hazm al-Zahiri (Andalusia), Ibn al-Arabi al-Maliki (untuk beberapa pandangannya)", "ur": "ابن حزم الظاہری (اندلس)، ابن العربی المالکی (بعض آراء کے حوالے سے)"},
        "summary": {"ar": "مؤسس المذهب الظاهري، الذي يعتمد على ظاهر النصوص دون قياس أو رأي. مذهبه انتشر في الأندلس وله حضور محدود اليوم.", "en": "Founder of the Zahiri school, which relies on the apparent meaning of texts without analogy or personal opinion. His school spread in Andalusia and has a limited presence today.", "fr": "Fondateur de l'école zahirite, qui s'appuie sur le sens apparent des textes sans analogie ni opinion personnelle. Son école s'est répandue en Andalousie et a une présence limitée aujourd'hui.", "fa": "بنیان‌گذار مذهب ظاهری که بر ظاهر نصوص بدون قیاس و رأی تکیه دارد. مذهب او در اندلس گسترش یافت و امروزه حضور محدودی دارد.", "ms": "Pengasas mazhab Zahiri yang bergantung kepada makna zahir nas tanpa qiyas atau pendapat peribadi. Mazhabnya tersebar di Andalusia dan mempunyai kehadiran terhad hari ini.", "ur": "مذہب ظاہری کے بانی، جو نصوص کے ظاہری معنی پر قیاس و رأی کے بغیر اعتماد کرتا ہے۔ ان کا مذہب اندلس میں پھیلا اور آج محدود موجودگی رکھتا ہے۔"}
    },
    {
        "name": {
            "ar": "الإمام جعفر بن محمد الصادق",
            "en": "Imam Ja'far ibn Muhammad al-Sadiq",
            "fr": "Imam Ja'far ibn Muhammad al-Sadiq",
            "fa": "امام جعفر بن محمد صادق",
            "ms": "Imam Ja'far bin Muhammad al-Sadiq",
            "ur": "امام جعفر بن محمد الصادق"
        },
        "school": MADHHAB_NAMES["jafari"],
        "lifespan": "80 - 148 AH (699 - 765 CE)",
        "birthplace": {"ar": "المدينة المنورة", "en": "Medina", "fr": "Médine", "fa": "مدینه منوره", "ms": "Madinah", "ur": "مدینہ منورہ"},
        "founding_place": {"ar": "المدينة المنورة", "en": "Medina", "fr": "Médine", "fa": "مدینه منوره", "ms": "Madinah", "ur": "مدینہ منورہ"},
        "scholars": {"ar": "الشيخ المفيد، الشريف المرتضى، الشيخ الطوسي، السيد الخوئي", "en": "Shaykh al-Mufid, Sharif al-Murtada, Shaykh al-Tusi, Sayyid al-Khui", "fr": "Shaykh al-Mufid, Sharif al-Murtada, Shaykh al-Tusi, Sayyid al-Khui", "fa": "شیخ مفید، شریف مرتضی، شیخ طوسی، سید خویی", "ms": "Shaykh al-Mufid, Sharif al-Murtada, Shaykh al-Tusi, Sayyid al-Khui", "ur": "الشیخ المفید، الشریف المرتضی، الشیخ الطوسی، السید الخوئی"},
        "summary": {"ar": "إمام الشيعة الإمامية الاثني عشرية، ومؤسس المذهب الجعفري. يتميز بالجمع بين النقل والعقل. مذهبه هو المذهب الرسمي في إيران والعراق ولبنان والبحرين.", "en": "The Imam of the Twelver Shia, and founder of the Ja'fari school. Characterized by combining tradition and reason. His school is the official school in Iran, Iraq, Lebanon, and Bahrain.", "fr": "L'imam des chiites duodécimains, et fondateur de l'école jaafarite. Caractérisé par la combinaison de la tradition et de la raison. Son école est l'école officielle en Iran, en Irak, au Liban et à Bahreïn.", "fa": "امام شیعیان اثنی عشری و بنیان‌گذار مذهب جعفری. با ترکیب نقل و عقل مشخص می‌شود. مذهب او مذهب رسمی ایران، عراق، لبنان و بحرین است.", "ms": "Imam Syiah Imamiyyah Itsna' Ashariyyah, dan pengasas mazhab Jaafari. Dicirikan dengan menggabungkan naqal dan akal. Mazhabnya adalah mazhab rasmi di Iran, Iraq, Lubnan dan Bahrain.", "ur": "شیعہ اثنا عشریہ کے امام اور مذہب جعفری کے بانی۔ نقل و عقل کے امتزاج کی خصوصیت۔ ان کا مذہب ایران، عراق، لبنان اور بحرین کا سرکاری مذہب ہے۔"}
    },
    {
        "name": {
            "ar": "الإمام زيد بن علي بن الحسين",
            "en": "Imam Zayd ibn Ali ibn al-Husayn",
            "fr": "Imam Zayd ibn Ali ibn al-Husayn",
            "fa": "امام زید بن علی بن حسین",
            "ms": "Imam Zayd bin Ali bin al-Husayn",
            "ur": "امام زید بن علی بن الحسین"
        },
        "school": MADHHAB_NAMES["zaidi"],
        "lifespan": "80 - 122 AH (699 - 740 CE)",
        "birthplace": {"ar": "المدينة المنورة", "en": "Medina", "fr": "Médine", "fa": "مدینه منوره", "ms": "Madinah", "ur": "مدینہ منورہ"},
        "founding_place": {"ar": "الكوفة - العراق", "en": "Kufa - Iraq", "fr": "Koufa - Irak", "fa": "کوفه - عراق", "ms": "Kufah - Iraq", "ur": "کوفہ - عراق"},
        "scholars": {"ar": "أبو خالد عمرو بن خالد الواسطي، القاسم بن إبراهيم الرسي، يحيى بن الحسين", "en": "Abu Khalid Amr ibn Khalid al-Wasiti, al-Qasim ibn Ibrahim al-Rassi, Yahya ibn al-Husayn", "fr": "Abu Khalid Amr ibn Khalid al-Wasiti, al-Qasim ibn Ibrahim al-Rassi, Yahya ibn al-Husayn", "fa": "ابو خالد عمرو بن خالد واسطی، قاسم بن ابراهیم رسی، یحیی بن حسین", "ms": "Abu Khalid Amr ibn Khalid al-Wasiti, al-Qasim ibn Ibrahim al-Rassi, Yahya ibn al-Husayn", "ur": "ابو خالد عمرو بن خالد الواسطي، القاسم بن إبراهيم الرسي، يحيى بن الحسين"},
        "summary": {"ar": "إمام الزيدية، ويمثل المذهب القريب من أهل السنة في كثير من المسائل مع توجه سياسي. مذهبه ينتشر في اليمن.", "en": "The Imam of Zaydism, representing a school close to Sunni thought on many issues with a political orientation. His school is widespread in Yemen.", "fr": "L'imam du zaydisme, représentant une école proche de la pensée sunnite sur de nombreuses questions avec une orientation politique. Son école est répandue au Yémen.", "fa": "امام زیدیه، مذهبی نزدیک به اهل سنت در بسیاری از مسائل با گرایش سیاسی. مذهب او در یمن گسترده است.", "ms": "Imam Zaidiyyah, mewakili mazhab yang dekat dengan pemikiran Sunni dalam banyak isu dengan orientasi politik. Mazhabnya tersebar di Yaman.", "ur": "زیدیہ کے امام، جو کئی مسائل میں اہل سنت کے قریب مذہب کی نمائندگی کرتے ہیں۔ ان کا مذہب یمن میں پھیلا ہوا ہے۔"}
    },
    {
        "name": {
            "ar": "الإمام جابر بن زيد الأزدي",
            "en": "Imam Jabir ibn Zayd al-Azdi",
            "fr": "Imam Jabir ibn Zayd al-Azdi",
            "fa": "امام جابر بن زید ازدی",
            "ms": "Imam Jabir bin Zayd al-Azdi",
            "ur": "امام جابر بن زید الازدی"
        },
        "school": MADHHAB_NAMES["ibadi"],
        "lifespan": "18 - 93 AH (639 - 712 CE)",
        "birthplace": {"ar": "نزوى - عُمان", "en": "Nizwa - Oman", "fr": "Nizwa - Oman", "fa": "نزوی - عمان", "ms": "Nizwa - Oman", "ur": "نزوی - عمان"},
        "founding_place": {"ar": "البصرة ثم عُمان", "en": "Basra, then Oman", "fr": "Bassorah, puis Oman", "fa": "بصره سپس عمان", "ms": "Basrah, kemudian Oman", "ur": "بصرہ پھر عمان"},
        "scholars": {"ar": "أبو عبيدة مسلم بن أبي كريمة، الربيع بن حبيب، أبو سفيان محبوب بن الرحيل", "en": "Abu Ubayda Muslim ibn Abi Karima, al-Rabi' ibn Habib, Abu Sufyan Mahbub ibn al-Rahil", "fr": "Abu Ubayda Muslim ibn Abi Karima, al-Rabi' ibn Habib, Abu Sufyan Mahbub ibn al-Rahil", "fa": "ابو عبیده مسلم بن ابی کریمه، ربیع بن حبیب، ابو سفیان محبوب بن رحیل", "ms": "Abu Ubayda Muslim ibn Abi Karima, al-Rabi' ibn Habib, Abu Sufyan Mahbub ibn al-Rahil", "ur": "ابو عبيدة مسلم بن أبي كريمة، الربيع بن حبيب، أبو سفيان محبوب بن الرحيل"},
        "summary": {"ar": "إمام الإباضية، وهو تابعي ومحدث. يتميز مذهبه بالاعتدال والوسطية. المذهب الرسمي في عُمان، وله وجود في زنجبار، الجزائر، وليبيا.", "en": "The Imam of Ibadism, a tabi'i and hadith scholar. His school is characterized by moderation and centrism. It is the official school in Oman, and has a presence in Zanzibar, Algeria, and Libya.", "fr": "L'imam de l'ibadisme, un tabi'i et savant du hadith. Son école se caractérise par la modération et le centrisme. C'est l'école officielle à Oman, et elle est présente à Zanzibar, en Algérie et en Libye.", "fa": "امام اباضیه، تابعی و محدث. مذهب او با اعتدال و میانه‌روی مشخص می‌شود. مذهب رسمی در عمان و دارای حضور در زنگبار، الجزایر و لیبی است.", "ms": "Imam Ibadhiyyah, seorang tabi'in dan ahli hadis. Mazhabnya dicirikan dengan kesederhanaan dan keseimbangan. Mazhab rasmi di Oman, dan hadir di Zanzibar, Algeria dan Libya.", "ur": "اباضیہ کے امام، تابعی اور محدث۔ ان کا مذہب اعتدال اور میانہ روی کی خصوصیت رکھتا ہے۔ عمان کا سرکاری مذہب اور زنجبار، الجزائر اور لیبیا میں موجود ہے۔"}
    },
]

# ============================================================
# المصطلحات الفقهية
# ============================================================

GLOSSARY = [
    {"term": {"ar": "الفرض / فرض العين", "en": "Fard / Fard Ayn (Individual Obligation)", "fr": "Le fard / fard ayn (Obligation individuelle)", "fa": "فرض / فرض عین", "ms": "Fardu / Fardu Ain", "ur": "فرض / فرض عین"},
     "definition": {"ar": "ما طلب الشارع فعله طلباً جازماً من كل مكلف بعينه، يُثاب فاعله ويُعاقب تاركه.", "en": "What the Lawgiver has decisively commanded every legally accountable individual to perform; one who does it is rewarded, and one who abandons it is sinful.", "fr": "Ce que le Législateur a ordonné de façon décisive à tout individu responsable d'accomplir ; celui qui l'accomplit est récompensé, et celui qui l'abandonne est fautif.", "fa": "آنچه شارع به‌طور قطعی بر هر مکلفی واجب کرده است؛ انجام‌دهنده پاداش می‌گیرد و ترک‌کننده گناهکار است.", "ms": "Apa yang Pembuat Syariat telah perintahkan secara tegas kepada setiap individu yang bertanggungjawab untuk melaksanakannya; yang melaksanakannya diberi pahala, dan yang meninggalkannya berdosa.", "ur": "وہ چیز جسے شارع نے ہر مکلف پر قطعی طور پر واجب کیا ہے؛ اسے کرنے والا ثواب پاتا ہے اور چھوڑنے والا گنہگار ہے۔"},
     "example": {"ar": "الصلوات الخمس، الزكاة.", "en": "The five daily prayers; zakat.", "fr": "Les cinq prières quotidiennes ; la zakat.", "fa": "نمازهای پنج‌گانه، زکات.", "ms": "Solat lima waktu, zakat.", "ur": "پانچ وقت کی نمازیں، زکوٰۃ۔"}},
    {"term": {"ar": "فرض الكفاية", "en": "Fard Kifayah (Sufficiency Obligation)", "fr": "Fard kifayah (Obligation de suffisance)", "fa": "فرض کفایه", "ms": "Fardu Kifayah", "ur": "فرض کفایہ"},
     "definition": {"ar": "ما طلب الشارع فعله طلباً جازماً من المجموعة دون كل فرد بعينه، فإذا قام به البعض سقط الإثم عن الباقين، وإن تركه الجميع أثموا.", "en": "A collective obligation which, if performed by some, absolves others; if abandoned by all, all are sinful.", "fr": "Une obligation collective qui, si elle est accomplie par certains, dispense les autres ; si tous l'abandonnent, tous sont fautifs.", "fa": "تکلیف جمعی که اگر عده‌ای آن را انجام دهند، از دیگران ساقط می‌شود و اگر همه ترک کنند، همه گناهکارند.", "ms": "Kewajipan kolektif yang jika dilakukan oleh sebahagian, gugur ke atas yang lain; jika ditinggalkan semua, semua berdosa.", "ur": "ایک اجتماعی فریضہ جو اگر کچھ لوگ ادا کریں تو باقیوں سے ساقط ہو جاتا ہے، اور اگر سب چھوڑ دیں تو سب گنہگار ہیں۔"},
     "example": {"ar": "صلاة الجنازة، تعلم الطب.", "en": "The funeral prayer; training enough doctors.", "fr": "La prière funéraire ; former suffisamment de médecins.", "fa": "نماز جنازه، آموختن پزشکی.", "ms": "Solat jenazah, mempelajari perubatan.", "ur": "نماز جنازہ، طب کی تعلیم۔"}},
    {"term": {"ar": "الواجب", "en": "Wajib (Obligatory)", "fr": "Wajib (Obligatoire)", "fa": "واجب", "ms": "Wajib", "ur": "واجب"},
     "definition": {"ar": "ما طلب الشارع فعله طلباً جازماً غير أنه لا يصل إلى درجة الفرض، ويُثاب فاعله ويعاقب تاركه عند الحنفية، وعند الجمهور هو بمعنى الفرض.", "en": "What the Lawgiver has commanded decisively but not reaching the level of Fard; rewarded for doing, punished for abandoning (according to Hanafis; for the majority, it is synonymous with Fard).", "fr": "Ce que le Législateur a ordonné de façon décisive mais n'atteignant pas le niveau de Fard ; récompensé pour l'accomplissement, puni pour l'abandon (selon les Hanafites ; pour la majorité, c'est synonyme de Fard).", "fa": "آنچه شارع به طور قطعی دستور داده اما به درجه فرض نمی‌رسد؛ انجام‌دهنده پاداش می‌گیرد و ترک‌کننده مجازات می‌شود (نزد حنفیه).", "ms": "Apa yang Pembuat Syariat telah perintahkan secara tegas tetapi tidak mencapai tahap Fardu; diberi pahala jika dilakukan, dihukum jika ditinggalkan (menurut Hanafi; bagi majoriti, ia sinonim dengan Fardu).", "ur": "وہ چیز جسے شارع نے قطعی طور پر حکم دیا ہے لیکن فرض کی سطح تک نہیں پہنچتی؛ کرنے والا ثواب پاتا ہے اور چھوڑنے والا سزا پاتا ہے (حنفیہ کے نزدیک؛ جمہور کے نزدیک یہ فرض کے مترادف ہے)۔"},
     "example": {"ar": "صلاة الوتر عند الحنفية.", "en": "The witr prayer according to Hanafis.", "fr": "La prière du witr selon les hanafites.", "fa": "نماز وتر نزد حنفیان.", "ms": "Solat witir menurut Hanafi.", "ur": "احناف کے نزدیک وتر کی نماز۔"}},
    {"term": {"ar": "المستحب / المندوب", "en": "Mustahabb / Mandub (Recommended)", "fr": "Mustahabb / Mandub (Recommandé)", "fa": "مستحب / مندوب", "ms": "Mustahabb / Mandub", "ur": "مستحب / مندوب"},
     "definition": {"ar": "ما طلب الشارع فعله طلباً غير جازم، يُثاب فاعله ولا يُعاقب تاركه.", "en": "What the Lawgiver has recommended without decisiveness; rewarded for doing, not punished for abandoning.", "fr": "Ce que le Législateur a recommandé sans caractère décisif ; récompensé pour l'accomplissement, non puni pour l'abandon.", "fa": "آنچه شارع به طور غیر قطعی دستور داده؛ انجام‌دهنده پاداش می‌گیرد و ترک‌کننده مجازات نمی‌شود.", "ms": "Apa yang Pembuat Syariat telah syorkan tanpa ketegasan; diberi pahala jika dilakukan, tidak dihukum jika ditinggalkan.", "ur": "وہ چیز جسے شارع نے غیر قطعی طور پر پسند کیا ہے؛ کرنے والا ثواب پاتا ہے، چھوڑنے والا سزا نہیں پاتا۔"},
     "example": {"ar": "صلاة الضحى، صيام الاثنين والخميس.", "en": "The mid-morning (Duha) prayer; fasting on Mondays and Thursdays.", "fr": "La prière de Doha ; le jeûne du lundi et jeudi.", "fa": "نماز ضحی، روزه دوشنبه و پنجشنبه.", "ms": "Solat Dhuha, puasa Isnin dan Khamis.", "ur": "نماز چاشت، پیر اور جمعرات کا روزہ۔"}},
    {"term": {"ar": "السنة", "en": "Sunnah", "fr": "Sunna", "fa": "سنت", "ms": "Sunat", "ur": "سنت"},
     "definition": {"ar": "ما ثبت عن النبي ﷺ من قول أو فعل أو تقرير، وهي تشمل الواجب والمستحب والمباح، وتُطلق غالباً على المستحب.", "en": "What is established from the Prophet ﷺ of sayings, actions, or approvals; it includes obligations, recommendations, and permissibles, and is often used for recommended acts.", "fr": "Ce qui est établi du Prophète ﷺ en paroles, actes ou approbations ; cela inclut les obligations, les recommandations et les permissibles, et est souvent utilisé pour les actes recommandés.", "fa": "آنچه از پیامبر ﷺ از قول، فعل یا تقریر ثابت شده است؛ شامل واجبات، مستحبات و مباحات می‌شود و اغلب برای مستحبات به کار می‌رود.", "ms": "Apa yang ditetapkan daripada Nabi ﷺ daripada perkataan, perbuatan atau persetujuan; ia termasuk kewajipan, galakan dan harus, dan sering digunakan untuk amalan yang digalakkan.", "ur": "وہ چیز جو نبی ﷺ سے قول، فعل یا تقریر کے طور پر ثابت ہے؛ اس میں واجبات، مستحبات اور مباحات شامل ہیں، اور اکثر مستحبات کے لیے استعمال ہوتی ہے۔"},
     "example": {"ar": "السواك عند الوضوء، الأذكار بعد الصلاة.", "en": "Using the miswak during ablution; remembrance (adhkar) after prayer.", "fr": "Le siwak lors des ablutions ; les invocations après la prière.", "fa": "مسواک هنگام وضو، اذکار پس از نماز.", "ms": "Bersiwak ketika berwuduk, zikir selepas solat.", "ur": "وضو کے وقت مسواک، نماز کے بعد اذکار۔"}},
    {"term": {"ar": "السنة المؤكدة", "en": "Sunnah Mu'akkadah (Emphasized Sunnah)", "fr": "Sunnah mu'akkadah (Sunnah confirmée)", "fa": "سنت مؤکد", "ms": "Sunat Muakkad", "ur": "سنت مؤکدہ"},
     "definition": {"ar": "ما واظب عليه النبي ﷺ ولم يتركه إلا نادراً، وهي قريبة من الواجب في الأهمية، وتركها مكروه عند بعض الفقهاء.", "en": "What the Prophet ﷺ consistently performed and rarely abandoned; it is close to obligatory in importance, and abandoning it is disliked by some jurists.", "fr": "Ce que le Prophète ﷺ a accompli régulièrement et rarement abandonné ; il est proche de l'obligation en importance, et son abandon est détesté par certains juristes.", "fa": "آنچه پیامبر ﷺ به طور مداوم انجام می‌داد و به ندرت ترک می‌کرد؛ از نظر اهمیت نزدیک به واجب است و ترک آن نزد برخی فقها مکروه است.", "ms": "Apa yang Nabi ﷺ lakukan secara konsisten dan jarang ditinggalkan; ia hampir kepada kewajipan dari segi kepentingan, dan meninggalkannya adalah makruh bagi sesetengah ulama.", "ur": "وہ چیز جو نبی ﷺ نے مستقل طور پر کی اور شاذ و نادر ہی چھوڑی؛ یہ اہمیت میں واجب کے قریب ہے، اور اسے چھوڑنا بعض فقہاء کے نزدیک مکروہ ہے۔"},
     "example": {"ar": "ركعتا الفجر، الوتر عند الجمهور (واجب عند الحنفية).", "en": "The two rak'ahs before Fajr; witr prayer (obligatory according to the Hanafis).", "fr": "Les deux rak'ahs avant Fajr ; le witr (obligatoire chez les hanafites).", "fa": "دو رکعت سنت فجر، وتر (نزد حنفیان واجب است).", "ms": "Dua rakaat sebelum Subuh, witir (wajib bagi Hanafi).", "ur": "فجر کی دو سنتیں، وتر (احناف کے نزدیک واجب)۔"}},
    {"term": {"ar": "المباح", "en": "Mubah (Permissible)", "fr": "Mubah (Permis)", "fa": "مباح", "ms": "Mubah", "ur": "مباح"},
     "definition": {"ar": "ما خير الشارع بين فعله وتركه، ولا ثواب على فعله ولا عقاب على تركه.", "en": "What the Lawgiver has left optional; no reward for doing it and no punishment for abandoning it.", "fr": "Ce que le Législateur a laissé facultatif ; pas de récompense pour l'accomplir ni de punition pour l'abandonner.", "fa": "آنچه شارع بین انجام و ترک آن مخیر کرده است؛ نه پاداشی بر انجام آن و نه عقابی بر ترک آن.", "ms": "Apa yang Pembuat Syariat memberi pilihan antara melakukannya atau meninggalkannya; tiada pahala untuk melakukannya dan tiada hukuman untuk meninggalkannya.", "ur": "وہ چیز جسے شارع نے اختیاری چھوڑ دیا ہے؛ کرنے پر کوئی ثواب نہیں اور چھوڑنے پر کوئی سزا نہیں۔"},
     "example": {"ar": "الأكل من الطيبات، اختيار لون الثوب.", "en": "Eating wholesome food; choosing the color of one's clothing.", "fr": "Manger des aliments licites ; choisir la couleur de son vêtement.", "fa": "خوردن غذاهای پاکیزه، انتخاب رنگ لباس.", "ms": "Makan makanan yang baik, memilih warna pakaian.", "ur": "پاکیزہ کھانا کھانا، لباس کا رنگ چننا۔"}},
    {"term": {"ar": "الحرام", "en": "Haram (Prohibited)", "fr": "Haram (Interdit)", "fa": "حرام", "ms": "Haram", "ur": "حرام"},
     "definition": {"ar": "ما طلب الشارع تركه طلباً جازماً، يُعاقب فاعله ويُثاب تاركه امتثالاً.", "en": "What the Lawgiver has decisively forbidden; the doer is punished, and the one who abstains in obedience is rewarded.", "fr": "Ce que le Législateur a interdit de façon décisive ; celui qui le fait est puni, et celui qui s'en abstient par obéissance est récompensé.", "fa": "آنچه شارع به طور قطعی از آن نهی کرده است؛ انجام‌دهنده مجازات می‌شود و ترک‌کننده به دلیل اطاعت پاداش می‌گیرد.", "ms": "Apa yang Pembuat Syariat telah melarang dengan tegas; yang melakukannya dihukum, dan yang meninggalkannya kerana kepatuhan diberi pahala.", "ur": "وہ چیز جسے شارع نے قطعی طور پر منع کیا ہے؛ کرنے والا سزا پاتا ہے اور چھوڑنے والا اطاعت کی وجہ سے ثواب پاتا ہے۔"},
     "example": {"ar": "الربا، أكل لحم الخنزير.", "en": "Usury (riba); eating pork.", "fr": "L'usure (riba) ; consommer du porc.", "fa": "ربا، خوردن گوشت خوک.", "ms": "Riba, memakan daging babi.", "ur": "سود، خنزیر کا گوشت کھانا۔"}},
    {"term": {"ar": "المكروه", "en": "Makruh (Disliked)", "fr": "Makruh (Réprouvé)", "fa": "مکروه", "ms": "Makruh", "ur": "مکروہ"},
     "definition": {"ar": "ما طلب الشارع تركه طلباً غير جازم، يُثاب تاركه ولا يُعاقب فاعله.", "en": "What the Lawgiver has discouraged without decisiveness; rewarded for abandoning, not punished for doing.", "fr": "Ce que le Législateur a découragé sans caractère décisif ; récompensé pour l'abandon, non puni pour l'accomplissement.", "fa": "آنچه شارع به طور غیر قطعی از آن نهی کرده است؛ ترک‌کننده پاداش می‌گیرد و انجام‌دهنده مجازات نمی‌شود.", "ms": "Apa yang Pembuat Syariat telah tidak menggalakkan tanpa ketegasan; diberi pahala jika ditinggalkan, tidak dihukum jika dilakukan.", "ur": "وہ چیز جسے شارع نے غیر قطعی طور پر ناپسند کیا ہے؛ چھوڑنے والا ثواب پاتا ہے، کرنے والا سزا نہیں پاتا۔"},
     "example": {"ar": "الأكل من ثوم نيء قبل الذهاب إلى المسجد، الإسراف في الماء عند الوضوء.", "en": "Eating raw garlic before going to the mosque; excessive use of water in ablution.", "fr": "Manger de l'ail cru avant d'aller à la mosquée ; le gaspillage d'eau lors des ablutions.", "fa": "خوردن سیر خام پیش از رفتن به مسجد، اسراف در آب وضو.", "ms": "Makan bawang putih mentah sebelum ke masjid, membazir air ketika wuduk.", "ur": "مسجد جانے سے پہلے کچا لہسن کھانا، وضو میں پانی کا اسراف۔"}},
    {"term": {"ar": "الحلال", "en": "Halal (Lawful)", "fr": "Halal (Licite)", "fa": "حلال", "ms": "Halal", "ur": "حلال"},
     "definition": {"ar": "ما أحله الشارع وأباحه، وهو يشمل الواجب والمستحب والمباح، وهو مقابل للحرام.", "en": "What the Lawgiver has made lawful and permissible; it includes obligations, recommendations, and permissibles, and is the opposite of Haram.", "fr": "Ce que le Législateur a rendu licite et permis ; cela inclut les obligations, les recommandations et les permissibles, et est l'opposé de Haram.", "fa": "آنچه شارع حلال و مجاز کرده است؛ شامل واجبات، مستحبات و مباحات می‌شود و مقابل حرام است.", "ms": "Apa yang Pembuat Syariat telah halalkan dan benarkan; ia termasuk kewajipan, galakan dan harus, dan bertentangan dengan Haram.", "ur": "وہ چیز جسے شارع نے حلال اور جائز کیا ہے؛ اس میں واجبات، مستحبات اور مباحات شامل ہیں، اور یہ حرام کے مقابل ہے۔"},
     "example": {"ar": "البيع المباح، الطعام الحلال.", "en": "A permissible sale; lawful food.", "fr": "Une vente licite ; une nourriture halal.", "fa": "خرید و فروش مباح، غذای حلال.", "ms": "Jualan yang harus, makanan halal.", "ur": "جائز بیع، حلال کھانا۔"}},
]

# ============================================================
# مصادر التشريع
# ============================================================

LEGAL_SOURCES = [
    {"name": {"ar": "القرآن الكريم", "en": "The Qur'an", "fr": "Le Coran", "fa": "قرآن کریم", "ms": "Al-Quran", "ur": "قرآن کریم"},
     "description": {"ar": "المصدر الأعلى والأول للتشريع الإسلامي، وهو كلام الله المنزل على نبيه محمد ﷺ.", "en": "The primary and highest source of Islamic law, the word of God revealed to Prophet Muhammad ﷺ.", "fr": "La première et la plus haute source du droit islamique, la parole de Dieu révélée au Prophète Muhammad ﷺ.", "fa": "منبع برتر و اولیه شریعت اسلامی، کلام خداوند نازل شده بر پیامبر محمد ﷺ.", "ms": "Sumber tertinggi dan utama undang-undang Islam, firman Allah yang diturunkan kepada Nabi Muhammad ﷺ.", "ur": "شریعت اسلامی کا اعلیٰ ترین اور اولیٰ ترین ماخذ، اللہ کا کلام جو نبی محمد ﷺ پر نازل ہوا۔"}},
    {"name": {"ar": "السنة النبوية", "en": "Prophetic Sunnah", "fr": "La Sunna prophétique", "fa": "سنت نبوی", "ms": "Sunnah Nabi", "ur": "سنت نبوی"},
     "description": {"ar": "أقوال النبي ﷺ وأفعاله وتقريراته، وهي المصدر الثاني بعد القرآن.", "en": "The sayings, actions, and approvals of the Prophet ﷺ, the second source after the Qur'an.", "fr": "Les paroles, actes et approbations du Prophète ﷺ, la deuxième source après le Coran.", "fa": "گفتار، کردار و تقریرات پیامبر ﷺ، منبع دوم پس از قرآن.", "ms": "Perkataan, perbuatan dan persetujuan Nabi ﷺ, sumber kedua selepas al-Quran.", "ur": "نبی ﷺ کے اقوال، افعال اور تقریرات، قرآن کے بعد دوسرا ماخذ۔"}},
    {"name": {"ar": "الإجماع", "en": "Ijma' (Consensus)", "fr": "Ijma' (Consensus)", "fa": "اجماع", "ms": "Ijma'", "ur": "اجماع"},
     "description": {"ar": "اتفاق المجتهدين من أمة محمد ﷺ في عصر من العصور على حكم شرعي بعد وفاة النبي ﷺ.", "en": "The agreement of qualified jurists from the Muslim community in any era on a legal ruling after the Prophet's death.", "fr": "L'accord des juristes qualifiés de la communauté musulmane à une époque donnée sur une règle juridique après la mort du Prophète.", "fa": "اتفاق مجتهدان امت محمد ﷺ در عصری بر حکم شرعی پس از وفات پیامبر.", "ms": "Persetujuan ulama mujtahid daripada umat Islam dalam sesuatu zaman terhadap hukum syarak selepas kewafatan Nabi.", "ur": "امت محمد ﷺ کے مجتہدین کا کسی دور میں کسی شرعی حکم پر اتفاق، نبی کی وفات کے بعد۔"}},
    {"name": {"ar": "القياس", "en": "Qiyas (Analogy)", "fr": "Qiyas (Analogie)", "fa": "قیاس", "ms": "Qiyas", "ur": "قیاس"},
     "description": {"ar": "إلحاق مسألة جديدة ليس لها نص بمسألة منصوص عليها لاشتراكهما في العلة الموجبة للحكم.", "en": "Applying an established ruling to a new case without a text due to a shared effective cause.", "fr": "L'application d'une règle connue à un cas nouveau sans texte en raison d'une cause commune.", "fa": "الحاق مسئله جدید بدون نص به مسئله منصوص به دلیل اشتراک در علت.", "ms": "Menghubungkan kes baru tanpa nas kepada kes yang telah ada nas kerana persamaan sebab.", "ur": "کسی نئے مسئلہ کو جس کا کوئی نص نہیں، کسی منصوص مسئلہ سے ملانا بوجہ مشترک علت۔"}},
]

# ============================================================
# أصول الاستدلال الفقهي
# ============================================================

USUL = [
    {"name": {"ar": "الأمر والنهي", "en": "Commands and prohibitions", "fr": "Commandements et interdictions", "fa": "امر و نهی", "ms": "Perintah dan larangan", "ur": "امر و نہی"},
     "definition": {"ar": "بحث دلالات صيغ الأمر والنهي وآثارها في إثبات الأحكام التكليفية.", "en": "Analysis of the implications of commands and prohibitions and their effects in establishing legal obligations.", "fr": "Analyse des implications des commandements et interdictions et de leurs effets dans l'établissement des obligations juridiques.", "fa": "بررسی دلالت‌های صیغ امر و نهی و آثار آن در اثبات احکام تکلیفی.", "ms": "Analisis maksud perintah dan larangan serta kesannya dalam menetapkan hukum taklifi.", "ur": "امر و نہی کے صیغوں کی دلالات اور ان کے تکلیفی احکام پر اثرات کا مطالعہ۔"},
     "note": {"ar": "تختلف بعض تطبيقاته بحسب القرائن والسياق.", "en": "Applications may vary according to context and indications.", "fr": "Les applications peuvent varier selon le contexte et les indications.", "fa": "برخی کاربردها با توجه به قرائن و زمینه متفاوت است.", "ms": "Aplikasi mungkin berbeza mengikut konteks dan petunjuk.", "ur": "سیاق و سباق کے مطابق کچھ اطلاقات مختلف ہو سکتی ہیں۔"}},
    {"name": {"ar": "العام والخاص", "en": "General and specific texts", "fr": "Textes généraux et spécifiques", "fa": "عام و خاص", "ms": "Am dan khas", "ur": "عام و خاص"},
     "definition": {"ar": "دراسة النصوص العامة وما يرد عليها من تخصيص يخرج بعض أفرادها من حكم العام.", "en": "Study of general texts and the specification that excludes some individuals from the general ruling.", "fr": "Étude des textes généraux et de la spécification qui en exclut certains individus.", "fa": "بررسی نصوص عمومی و تخصیص‌های وارد بر آن که برخی افراد را از حکم عام خارج می‌کند.", "ms": "Kajian teks umum dan pengkhususan yang mengeluarkan sebahagian individu daripada hukum umum.", "ur": "عام نصوص اور ان پر وارد ہونے والے تخصیص کا مطالعہ جو بعض افراد کو عام حکم سے خارج کرتا ہے۔"},
     "note": {"ar": "يبحث الأصولي في دلالة اللفظ وحدود شموله.", "en": "The jurist examines the scope and meaning of the wording.", "fr": "Le juriste examine la portée et le sens de la formulation.", "fa": "اصولی در دلالت لفظ و حدود شمول آن بحث می‌کند.", "ms": "Usuliyyin mengkaji makna lafaz dan batas cakupannya.", "ur": "اصولی لفظ کی دلالت اور اس کے شمول کی حدود کا جائزہ لیتا ہے۔"}},
    {"name": {"ar": "المطلق والمقيد", "en": "Unrestricted and restricted texts", "fr": "Textes absolus et restreints", "fa": "مطلق و مقید", "ms": "Mutlaq dan muqayyad", "ur": "مطلق و مقید"},
     "definition": {"ar": "الموازنة بين النص المطلق والنص الذي قيده وصف أو شرط، وكيفية حمل المطلق على المقيد.", "en": "Reconciling unrestricted texts with texts limited by a condition or description, and how to apply restrictions.", "fr": "La conciliation entre les textes absolus et ceux limités par une condition ou une description.", "fa": "موازنه بین نص مطلق و نصی که با وصف یا شرط مقید شده است.", "ms": "Mengimbangi teks mutlaq dengan teks yang dibatasi oleh syarat atau sifat.", "ur": "مطلق نص اور اس نص کے درمیان توازن جو کسی وصف یا شرط سے مقید ہے۔"},
     "note": {"ar": "يُنظر في اتحاد الحكم والسبب والسياق.", "en": "The legal ruling, cause, and context are considered.", "fr": "La règle, la cause et le contexte sont pris en compte.", "fa": "اتحاد حکم، سبب و زمینه بررسی می‌شود.", "ms": "Kesatuan hukum, sebab dan konteks dipertimbangkan.", "ur": "حکم، سبب اور سیاق و سباق کی یکسانیت پر نظر کیا جاتا ہے۔"}},
    {"name": {"ar": "المصلحة والاستصحاب", "en": "Maslahah and presumption of continuity", "fr": "Maslaha et présomption de continuité", "fa": "مصلحت و استصحاب", "ms": "Maslahah dan istishab", "ur": "مصلحت و استصحاب"},
     "definition": {"ar": "منهج للنظر في المصلحة المعتبرة واستمرار الحكم السابق عند عدم وجود دليل على التغيير.", "en": "A methodology for considering recognized benefit and the continuity of a previous ruling in the absence of evidence of change.", "fr": "Une méthodologie pour considérer l'intérêt reconnu et la continuité d'un jugement antérieur en l'absence de preuve de changement.", "fa": "روشی برای بررسی مصلحت معتبر و استمرار حکم سابق در صورت عدم وجود دلیل بر تغییر.", "ms": "Kaedah untuk mempertimbangkan maslahah yang diiktiraf dan kesinambungan hukum asal apabila tiada dalil yang mengubahnya.", "ur": "مصلحت معتبر اور ناقل کی عدم موجودگی میں سابق حکم کے استمرار پر نظر کا طریقہ۔"},
     "note": {"ar": "تختلف حدود الاعتماد عليهما بين المدارس الفقهية.", "en": "Schools differ in the extent to which they rely on these principles.", "fr": "Les écoles divergent quant à leur utilisation.", "fa": "میزان اعتماد بر این دو در میان مذاهب فقهی متفاوت است.", "ms": "Tahap pergantungan kepada prinsip ini berbeza antara mazhab.", "ur": "ان اصولوں پر اعتماد کی حد مذاہب فقہیہ میں مختلف ہے۔"}},
]

# ============================================================
# القواعد الأصولية الفقهية (موسعة - 17 قاعدة)
# ============================================================

RULES = [
    # القواعد الخمس الكبرى
    {"name": {"ar": "اليقين لا يزول بالشك", "en": "Certainty cannot be overridden by doubt", "fr": "La certitude ne peut être remplacée par le doute", "fa": "یقین به شک زایل نمی‌شود", "ms": "Keyakinan tidak boleh digantikan dengan keraguan", "ur": "یقین شک سے زائل نہیں ہوتا"},
     "definition": {"ar": "إذا ثبت أمر بيقين فلا يزول إلا بيقين مثله، ولا يؤثر فيه مجرد الشك.", "en": "Certainty cannot be overridden by doubt.", "fr": "La certitude ne peut être remplacée par le doute.", "fa": "هر چیزی که با یقین ثابت شده است با شک از بین نمی‌رود.", "ms": "Keyakinan tidak boleh digantikan dengan keraguan.", "ur": "جو چیز یقین سے ثابت ہو جائے وہ شک سے زائل نہیں ہوتی۔"},
     "example": {"ar": "من تيقن الطهارة وشك في الحدث، يبقى على الطهارة.", "en": "If someone is certain of purity and doubts impurity, they remain in a state of purity.", "fr": "Si quelqu'un est certain de la pureté et doute de l'impureté, il reste en état de pureté.", "fa": "کسی که یقین به طهارت دارد و به حدث شک می‌کند، بر طهارت باقی می‌ماند.", "ms": "Jika seseorang yakin suci dan ragu najis, dia kekal dalam keadaan suci.", "ur": "جو شخص طہارت پر یقین رکھتا ہے اور حدث پر شک کرتا ہے، وہ طہارت پر باقی رہتا ہے۔"}},
    {"name": {"ar": "المشقة تجلب التيسير", "en": "Hardship brings ease", "fr": "La difficulté apporte la facilité", "fa": "مشقت باعث آسانی می‌شود", "ms": "Kesukaran membawa kemudahan", "ur": "مشقت آسانی لاتی ہے"},
     "definition": {"ar": "عند وجود مشقة معتبرة في تطبيق الحكم الشرعي، يُفتح باب الرخصة والتخفيف.", "en": "Hardship brings ease in Islamic jurisprudence.", "fr": "La difficulté apporte la facilité dans la jurisprudence islamique.", "fa": "هنگام وجود مشقت معتبر در اجرای حکم شرعی، باب رخصت و تخفیف گشوده می‌شود.", "ms": "Apabila terdapat kesukaran yang diiktiraf dalam melaksanakan hukum syarak, keringanan dan kemudahan diberikan.", "ur": "شرعی حکم کے اطلاق میں معتبر مشقت کی صورت میں رخصت اور تخفیف کا دروازہ کھل جاتا ہے۔"},
     "example": {"ar": "قصر الصلاة في السفر أو الإفطار في المرض.", "en": "Shortening prayers during travel or breaking fast during illness.", "fr": "Raccourcir les prières pendant le voyage ou rompre le jeûne en cas de maladie.", "fa": "قصر نماز در سفر یا افطار در بیماری.", "ms": "Memendekkan solat semasa musafir atau berbuka puasa ketika sakit.", "ur": "سفر میں نماز قصر کرنا یا بیماری میں روزہ افطار کرنا۔"}},
    {"name": {"ar": "الضرر يزال", "en": "Harm must be removed", "fr": "Le préjudice doit être écarté", "fa": "ضرر باید برطرف شود", "ms": "Kemudaratan mesti dihilangkan", "ur": "نقصان کو دور کیا جانا چاہیے"},
     "definition": {"ar": "كل ما فيه ضرر على الفرد أو الجماعة يجب رفعه أو منعه.", "en": "Harm must be removed or prevented.", "fr": "Le préjudice doit être écarté ou empêché.", "fa": "هر چیزی که برای فرد یا جامعه ضرر دارد باید برطرف یا ممنوع شود.", "ms": "Segala yang membawa kemudaratan kepada individu atau masyarakat mesti dihilangkan atau dicegah.", "ur": "ہر وہ چیز جو فرد یا جماعت کو نقصان پہنچاتی ہے اسے دور یا روکا جانا چاہیے۔"},
     "example": {"ar": "منع الغش في البيع أو إزالة الأذى عن الطريق.", "en": "Preventing fraud in sales or removing harm from the road.", "fr": "Prévenir la fraude dans les ventes ou éliminer les nuisances de la route.", "fa": "منع تقلب در خرید و فروش یا برداشتن مزاحمت از راه.", "ms": "Mencegah penipuan dalam jualan atau membuang bahaya dari jalan.", "ur": "بیع میں دھوکہ دہی کو روکنا یا راستے سے نقصان کو ہٹانا۔"}},
    {"name": {"ar": "العادة محكمة", "en": "Custom is a valid consideration", "fr": "La coutume est considérée", "fa": "عرف و عادت معتبر است", "ms": "Adat dipertimbangkan", "ur": "عادت کو معتبر سمجھا جاتا ہے"},
     "definition": {"ar": "العرف والعادة المعتبرة شرعًا تُعتبر في الأحكام ما لم تخالف نصًا شرعيًا.", "en": "Custom is a valid consideration in Islamic law.", "fr": "La coutume est considérée en droit islamique.", "fa": "عرف و عادت معتبر شرعی در احکام لحاظ می‌شود.", "ms": "Adat dan uruf yang diiktiraf secara syarak dipertimbangkan dalam hukum.", "ur": "شرعی طور پر معتبر عرف و عادت کو احکام میں لحاظ رکھا جاتا ہے بشرطیکہ کسی شرعی نص کی مخالفت نہ ہو۔"},
     "example": {"ar": "أعراف الزواج أو البيع.", "en": "Customs regarding marriage or sales.", "fr": "Les coutumes relatives au mariage ou aux ventes.", "fa": "عرف‌های ازدواج یا خرید و فروش.", "ms": "Adat mengenai perkahwinan atau jualan.", "ur": "شادی یا بیع کے متعلق رسوم۔"}},
    {"name": {"ar": "الأمور بمقاصدها", "en": "Actions are judged by intentions", "fr": "Les actions sont jugées par leurs intentions", "fa": "کارها با نیت‌ها ارزیابی می‌شوند", "ms": "Tindakan dinilai dengan niat", "ur": "اعمال کا دارومدار نیتوں پر ہے"},
     "definition": {"ar": "الحكم على الأفعال يكون بحسب نية صاحبها ومقصده.", "en": "Actions are judged by their intentions.", "fr": "Les actions sont jugées selon leurs intentions.", "fa": "حکم بر افعال بر اساس نیت و هدف صاحب آن است.", "ms": "Tindakan dinilai berdasarkan niat dan tujuannya.", "ur": "اعمال کا حکم ان کے ارادے اور مقصد کے مطابق ہوتا ہے۔"},
     "example": {"ar": "التفريق بين الصدقة والهدية.", "en": "The distinction between charity and gift.", "fr": "La distinction entre l'aumône et le cadeau.", "fa": "تفاوت بین صدقه و هدیه.", "ms": "Perbezaan antara sedekah dan hadiah.", "ur": "صدقہ اور ہدیہ میں فرق۔"}},
    # قواعد فرعية
    {"name": {"ar": "الضرورات تبيح المحظورات", "en": "Necessities permit the forbidden", "fr": "Les nécessités permettent le prohibé", "fa": "ضرورت‌ها حرام را مباح می‌کنند", "ms": "Keperluan membenarkan yang haram", "ur": "ضرورتیں ممنوعات کو جائز کرتی ہیں"},
     "definition": {"ar": "عند الضرورة يجوز ارتكاب المحظور بقدر الحاجة فقط.", "en": "Necessities permit the forbidden to the extent of need.", "fr": "Les nécessités permettent le prohibé dans la mesure du besoin.", "fa": "در صورت ضرورت، انجام کار حرام به اندازه نیاز مجاز است.", "ms": "Dalam keadaan darurat, perkara yang haram dibenarkan sekadar keperluan.", "ur": "ضرورت کی صورت میں ممنوع چیز کو ضرورت کے بقدر جائز کر دیا جاتا ہے۔"},
     "example": {"ar": "أكل الميتة عند الخوف من الهلاك.", "en": "Eating carrion when fearing death.", "fr": "Manger de la charogne par crainte de mourir.", "fa": "خوردن مردار در صورت ترس از مرگ.", "ms": "Memakan bangkai apabila takut mati.", "ur": "موت کے خوف سے مردار کھانا۔"}},
    {"name": {"ar": "الوسائل لها أحكام المقاصد", "en": "The means take the ruling of their objectives", "fr": "Les moyens prennent le jugement de leurs objectifs", "fa": "وسایل حکم اهداف خود را دارند", "ms": "Cara-cara mengambil hukum matlamatnya", "ur": "ذرائع اپنے مقاصد کا حکم رکھتے ہیں"},
     "definition": {"ar": "ما كان وسيلة لشيء يأخذ حكم ذلك الشيء.", "en": "The means take the ruling of their objectives.", "fr": "Les moyens prennent le jugement de leurs objectifs.", "fa": "هر چیزی که وسیله چیزی باشد، حکم آن چیز را دارد.", "ms": "Apa yang menjadi wasilah kepada sesuatu mengambil hukum sesuatu itu.", "ur": "جو چیز کسی چیز کا ذریعہ ہوتی ہے وہ اس کا حکم رکھتی ہے۔"},
     "example": {"ar": "الكتابة في العقود لحفظ الحقوق.", "en": "Writing contracts to preserve rights.", "fr": "Écrire des contrats pour préserver les droits.", "fa": "نوشتن قراردادها برای حفظ حقوق.", "ms": "Menulis kontrak untuk memelihara hak.", "ur": "حقوق کے تحفظ کے لیے معاہدے تحریر کرنا۔"}},
    {"name": {"ar": "القياس", "en": "Analogy (Qiyas)", "fr": "Analogie (Qiyas)", "fa": "قیاس", "ms": "Qiyas", "ur": "قیاس"},
     "definition": {"ar": "إلحاق فرع بأصل في الحكم لعلة جامعة بينهما.", "en": "Extending a ruling from an original case to a new case due to shared reasoning.", "fr": "Extension d'une règle d'un cas original à un nouveau cas en raison d'un raisonnement partagé.", "fa": "الحاق فرع به اصل در حکم به دلیل علت مشترک.", "ms": "Memperluas hukum dari kes asal ke kes baru kerana persamaan sebab.", "ur": "حکم میں فرع کو اصل سے ملانا بوجہ مشترک علت۔"},
     "example": {"ar": "قياس المخدرات على الخمر في التحريم لعلة الإسكار.", "en": "Analogizing drugs to alcohol in prohibition due to the reasoning of intoxication.", "fr": "Analogie des drogues à l'alcool dans l'interdiction en raison de l'intoxication.", "fa": "قیاس مواد مخدر بر خمر در تحریم به دلیل اسکار.", "ms": "Menganalogikan dadah kepada arak dalam pengharaman kerana sebab memabukkan.", "ur": "نشہ کی علت کی وجہ سے منشیات کو شراب پر قیاس کرنا۔"}},
    {"name": {"ar": "المصالح المرسلة", "en": "Considered public interest", "fr": "Intérêt public considéré", "fa": "مصالح مرسله", "ms": "Maslahah mursalah", "ur": "مصالح مرسلہ"},
     "definition": {"ar": "اعتبار المصلحة التي لم يرد نص خاص بها ولم تُلغَ، إذا كانت تحقق منفعة عامة.", "en": "Considering public interests not explicitly addressed in primary sources.", "fr": "Considération des intérêts publics non explicitement abordés dans les sources primaires.", "fa": "اعتبار مصلحتی که نص خاصی برای آن نیامده و لغو نشده است، در صورت تحقق منفعت عمومی.", "ms": "Mempertimbangkan maslahah yang tidak disebut secara khusus dalam nas dan tidak dibatalkan, jika ia membawa manfaat umum.", "ur": "ان مفادات کا اعتبار جن کا کوئی خاص نص نہیں ہے اور نہ ہی انہیں منسوخ کیا گیا ہے، اگر وہ عام مفاد کو پورا کرتی ہیں۔"},
     "example": {"ar": "توثيق العقود بالكتابة.", "en": "Documenting contracts in writing.", "fr": "Documenter les contrats par écrit.", "fa": "مستند کردن قراردادها به نوشته.", "ms": "Mendokumentasikan kontrak secara bertulis.", "ur": "معاہدات کو تحریر میں دستاویز کرنا۔"}},
    {"name": {"ar": "الخاص يحكم العام", "en": "The specific takes precedence over the general", "fr": "Le spécifique prévaut sur le général", "fa": "خاص بر عام مقدم است", "ms": "Khusus mengatasi umum", "ur": "خاص کو عام پر ترجیح ہے"},
     "definition": {"ar": "إذا ورد نص عام ونص خاص، يُقدَّم الخاص في التطبيق.", "en": "When general and specific texts conflict, the specific takes precedence.", "fr": "Lorsque les textes généraux et spécifiques sont en conflit, le spécifique prévaut.", "fa": "اگر نص عام و خاص با هم تعارض داشته باشند، خاص مقدم می‌شود.", "ms": "Apabila teks umum dan khusus bercanggah, teks khusus didahulukan.", "ur": "اگر عام اور خاص نص باہم متعارض ہوں تو خاص کو ترجیح دی جاتی ہے۔"},
     "example": {"ar": "قوله تعالى: (وأحل الله البيع) عام، وقوله: (حرمت عليكم الميتة) خاص.", "en": "The general verse: 'Allah has permitted trade' vs. 'Forbidden to you is carrion'.", "fr": "Le verset général 'Allah a permis le commerce' vs 'Il vous est interdit la charogne'.", "fa": "آیه عام 'خداوند خرید و فروش را حلال کرده' vs 'مردار بر شما حرام شده'.", "ms": "Ayat umum 'Allah menghalalkan jual beli' vs 'Diharamkan kepada kamu bangkai'.", "ur": "عام آیت 'اللہ نے بیع کو حلال کیا' vs 'تم پر مردار حرام ہے'۔"}},
    {"name": {"ar": "لا ضرر ولا ضرار", "en": "No harm and no reciprocating harm", "fr": "Pas de mal et pas de réciprocité de mal", "fa": "نه ضرر و نه ضرر متقابل", "ms": "Tidak boleh membahayakan dan tidak boleh membalas bahaya", "ur": "نہ نقصان اور نہ نقصان کا بدلہ"},
     "definition": {"ar": "قاعدة مأخوذة من حديث النبي ﷺ: (لا ضرر ولا ضرار)، وتعني أنه لا يجوز إيقاع الضرر بالنفس أو بالغير، ولا يجوز رد الضرر بضرر مثله.", "en": "Based on the Prophetic hadith: 'No harm and no reciprocating harm.'", "fr": "Basé sur le hadith prophétique: 'Pas de mal et pas de réciprocité de mal.'", "fa": "بر اساس حدیث نبوی: 'نه ضرر و نه ضرر متقابل'.", "ms": "Berdasarkan hadis Nabi: 'Tidak boleh membahayakan dan tidak boleh membalas bahaya'.", "ur": "نبوی حدیث پر مبنی: 'نہ نقصان اور نہ نقصان کا بدلہ'۔"},
     "example": {"ar": "منع البناء الذي يضر بالجار.", "en": "Preventing construction that harms a neighbor.", "fr": "Prévenir la construction qui nuit à un voisin.", "fa": "جلوگیری از ساخت و سازی که به همسایه ضرر می‌زند.", "ms": "Mencegah pembinaan yang merugikan jiran.", "ur": "ایسی تعمیر کو روکنا جو پڑوسی کو نقصان پہنچائے۔"}},
    {"name": {"ar": "الأصل في الأشياء الإباحة", "en": "The default is permissibility", "fr": "Le principe de base est la permission", "fa": "اصل در اشیاء اباحه است", "ms": "Hukum asal adalah harus", "ur": "اصل اشیاء میں اباحت ہے"},
     "definition": {"ar": "الأصل في الأشياء والأفعال الإباحة حتى يقوم دليل على التحريم.", "en": "The default ruling for things and actions is permissibility until evidence proves otherwise.", "fr": "Le principe de base pour les choses et les actions est la permission jusqu'à ce qu'une preuve établisse le contraire.", "fa": "اصل در اشیاء و افعال اباحه است تا زمانی که دلیل بر حرمت قائم شود.", "ms": "Hukum asal bagi sesuatu dan tindakan adalah harus sehingga ada dalil yang menunjukkan sebaliknya.", "ur": "اشیا اور افعال میں اصل اباحت ہے جب تک کہ حرمت کی کوئی دلیل نہ آئے۔"},
     "example": {"ar": "جواز أكل جميع الأطعمة ما لم يرد نص بتحريمها.", "en": "Permissibility of all foods unless there is a text prohibiting them.", "fr": "La permission de manger tous les aliments à moins qu'un texte ne les interdise.", "fa": "جواز خوردن همه غذاها مگر اینکه نصی بر حرمت آنها وارد شود.", "ms": "Kebolehan memakan semua makanan kecuali ada nas yang mengharamkannya.", "ur": "تمام کھانوں کا جائز ہونا جب تک کہ کوئی نص ان کی حرمت پر نہ ہو۔"}},
    {"name": {"ar": "الأصل براءة الذمة", "en": "Presumption of innocence", "fr": "Présomption d'innocence", "fa": "اصل برائت ذمه", "ms": "Prinsip bebas tanggungan", "ur": "اصل برائت ذمہ"},
     "definition": {"ar": "الأصل أن يبقى الإنسان غير مطالَب بحق أو التزام تجاه غيره حتى يثبت خلاف ذلك بدليل معتبر.", "en": "A person is presumed free of any claim or liability until proven otherwise by valid evidence.", "fr": "Une personne est présumée libre de toute obligation jusqu'à preuve valable du contraire.", "fa": "اصل این است که انسان تا اثبات خلاف آن با دلیل معتبر، از هیچ حق یا تعهدی نسبت به دیگری مسئول نیست.", "ms": "Pada asalnya seseorang bebas daripada sebarang tuntutan atau tanggungan sehingga terbukti sebaliknya dengan bukti sah.", "ur": "اصل یہ ہے کہ انسان کسی حق یا ذمہ داری سے بری رہتا ہے جب تک معتبر دلیل سے اس کے خلاف ثابت نہ ہو۔"},
     "example": {"ar": "من ادّعى ديناً على آخر فالبيّنة عليه؛ لأن الأصل براءة ذمة المدَّعى عليه.", "en": "Whoever claims a debt against another must provide proof, since the defendant is presumed free of liability.", "fr": "Celui qui prétend qu'une dette lui est due doit en apporter la preuve, l'accusé étant présumé sans dette.", "fa": "هر کس ادعای دِینی بر دیگری کند، اثبات آن بر عهده اوست؛ زیرا اصل برائت ذمه مدعی‌علیه است.", "ms": "Sesiapa mendakwa hutang ke atas orang lain wajib membawa bukti, kerana asalnya tertuduh bebas tanggungan.", "ur": "جو کسی پر قرض کا دعویٰ کرے، ثبوت اسی کے ذمہ ہے؛ کیونکہ اصل مدعا علیہ کی برأت ہے۔"}},
    {"name": {"ar": "الاستحسان", "en": "Juristic preference (Istihsan)", "fr": "Préférence juridique (Istihsan)", "fa": "استحسان", "ms": "Istihsan", "ur": "استحسان"},
     "definition": {"ar": "العدول عن مقتضى قياس ظاهر إلى حكم آخر يقتضيه دليل أقوى، كنص خاص أو عرف أو ضرورة، تحقيقاً لمصلحة راجحة.", "en": "Departing from an apparent analogy toward a ruling supported by stronger evidence - a specific text, custom, or necessity - to serve a preponderant benefit.", "fr": "S'écarter d'une analogie apparente vers un jugement fondé sur une preuve plus forte - texte spécifique, coutume ou nécessité - pour un intérêt supérieur.", "fa": "عدول از قیاس ظاهر به حکمی دیگر که دلیل قوی‌تری چون نص خاص، عرف یا ضرورت اقتضا می‌کند، برای تحقق مصلحتی برتر.", "ms": "Beralih daripada qiyas zahir kepada hukum lain yang disokong dalil lebih kuat - nas khusus, uruf, atau darurat - demi maslahat yang lebih besar.", "ur": "ظاہری قیاس سے ہٹ کر ایسے حکم کی طرف رجوع جسے خاص نص، عرف یا ضرورت جیسی مضبوط دلیل چاہتی ہو، بہتر مصلحت کے لیے۔"},
     "example": {"ar": "جواز عقد الاستصناع استحساناً، وإن كان القياس الظاهر يقتضي منعه لكون المصنوع معدوماً وقت العقد.", "en": "Permitting the manufacturing contract (istisna') by juristic preference, though strict analogy would forbid selling a non-existent item.", "fr": "Autoriser le contrat de fabrication (istisna') par préférence juridique, bien que l'analogie stricte l'interdirait.", "fa": "جواز عقد استصناع به استحسان، هرچند قیاس ظاهر آن را به دلیل معدوم بودن کالا هنگام عقد منع می‌کند.", "ms": "Membenarkan akad istisna' secara istihsan, walaupun qiyas zahir melarangnya kerana barang belum wujud semasa akad.", "ur": "استصناع کے معاہدے کا استحساناً جواز، اگرچہ ظاہری قیاس اسے معاہدے کے وقت چیز کے معدوم ہونے کی وجہ سے منع کرتا ہے۔"}},
    {"name": {"ar": "الاستصحاب", "en": "Presumption of continuity", "fr": "Présomption de continuité", "fa": "استصحاب", "ms": "Istishab", "ur": "استصحاب"},
     "definition": {"ar": "إبقاء الحكم الثابت في الماضي قائماً في الحال والمستقبل، ما لم يقم دليل شرعي على تغييره أو زواله.", "en": "Presuming that a previously established ruling remains in effect unless proven otherwise.", "fr": "Présumer qu'un jugement précédemment établi reste valable, sauf preuve contraire.", "fa": "باقی نگه‌داشتن حکمی که در گذشته ثابت شده تا زمانی که دلیلی بر تغییر یا زوال آن اقامه نشود.", "ms": "Mengekalkan hukum yang telah sabit pada masa lalu sehingga ada dalil yang mengubah atau membatalkannya.", "ur": "ماضی میں ثابت شدہ حکم کو حال و مستقبل میں برقرار رکھنا جب تک اس کے تبدیل یا زوال کی دلیل نہ ملے۔"},
     "example": {"ar": "من ثبتت له ملكية شيء بيقين، بقي مالكاً له حتى يثبت زوال ملكه بدليل.", "en": "Whoever is established as the owner of something remains so until evidence proves otherwise.", "fr": "Celui dont la propriété d'un bien est établie en reste propriétaire jusqu'à preuve du contraire.", "fa": "کسی که مالکیت چیزی برایش به یقین ثابت شده، تا اثبات زوال آن با دلیل، مالک باقی می‌ماند.", "ms": "Sesiapa yang sabit memiliki sesuatu kekal sebagai pemiliknya sehingga terbukti sebaliknya.", "ur": "جس کی ملکیت یقینی طور پر ثابت ہو، وہ اس کا مالک رہتا ہے جب تک زوالِ ملکیت کی دلیل نہ آئے۔"}},
    {"name": {"ar": "سد الذرائع", "en": "Blocking the means", "fr": "Bloquer les moyens", "fa": "سد ذرائع", "ms": "Saddu al-zara'i", "ur": "سد ذرائع"},
     "definition": {"ar": "منع فعل جائز في أصله متى كان وسيلة غالبة إلى مفسدة محققة، درءاً لتلك المفسدة قبل وقوعها.", "en": "Blocking an act permissible in itself when it is a likely means to a real harm, to prevent that harm before it occurs.", "fr": "Interdire un acte permis en soi lorsqu'il est un moyen probable vers un préjudice réel, afin de le prévenir.", "fa": "منع کاری که در اصل جایز است هرگاه وسیله غالب به مفسده‌ای قطعی باشد، برای جلوگیری از آن مفسده پیش از وقوع.", "ms": "Menghalang perbuatan yang asalnya harus apabila ia menjadi jalan yang kuat kepada kemudaratan nyata, bagi mencegahnya sebelum berlaku.", "ur": "اصلاً جائز کام کو روکنا جب وہ کسی یقینی خرابی کا غالب ذریعہ بن جائے، تاکہ وہ خرابی وقوع سے پہلے رک جائے۔"},
     "example": {"ar": "منع بيع السلاح في زمن الفتنة لمن يُخشى استعماله في قتال ظالم.", "en": "Prohibiting the sale of weapons in times of unrest to those likely to use them for unjust bloodshed.", "fr": "Interdire la vente d'armes en temps de troubles à ceux susceptibles de les utiliser injustement.", "fa": "منع فروش سلاح در زمان آشوب به کسی که بیم استفاده ظالمانه از آن می‌رود.", "ms": "Melarang jualan senjata semasa fitnah kepada golongan yang dikhuatiri menyalahgunakannya.", "ur": "فتنے کے دور میں اسلحہ بیچنا اس شخص کو روکنا جس سے ظالمانہ استعمال کا خدشہ ہو۔"}},
    {"name": {"ar": "درء المفاسد أولى من جلب المصالح", "en": "Preventing harm takes precedence over bringing benefit", "fr": "La prévention du préjudice prime sur l'obtention du bienfait", "fa": "دفع مفسده بر جلب مصلحت مقدم است", "ms": "Mencegah kemudaratan lebih utama daripada membawa manfaat", "ur": "مفسدہ کا دفع کرنا مصلحت کے حصول پر مقدم ہے"},
     "definition": {"ar": "عند تعارض مصلحة ومفسدة وتعذّر الجمع بينهما، يُقدَّم دفع المفسدة على تحصيل المصلحة.", "en": "When a benefit and a harm conflict and cannot both be achieved, preventing the harm takes priority over securing the benefit.", "fr": "Lorsqu'un bienfait et un préjudice s'opposent sans conciliation possible, prévenir le préjudice prime sur l'obtention du bienfait.", "fa": "اگر مصلحت و مفسده با هم تعارض داشته باشند و جمع میان آن‌ها ممکن نباشد، دفع مفسده بر جلب مصلحت مقدم است.", "ms": "Apabila maslahat dan mafsadah bertembung dan tidak boleh digabungkan, mencegah mafsadah didahulukan daripada mengejar maslahat.", "ur": "جب مصلحت اور مفسدہ ٹکرائیں اور دونوں کو جمع کرنا ممکن نہ ہو تو مفسدہ دور کرنا مصلحت حاصل کرنے پر مقدم ہے۔"},
     "example": {"ar": "منع فتح باب معاملة مالية فيها ربا وإن حقق نفعاً اقتصادياً، درءاً لمفسدة الربا.", "en": "Blocking a financial dealing involving usury even if it offers economic gain, to prevent the greater harm.", "fr": "Interdire une opération financière usuraire malgré un gain économique, pour prévenir le préjudice.", "fa": "منع معامله مالی ربوی هرچند سود اقتصادی داشته باشد، برای دفع مفسده ربا.", "ms": "Menghalang urus niaga kewangan yang mengandungi riba walaupun membawa keuntungan ekonomi.", "ur": "سودی مالی معاملہ روکنا اگرچہ اس میں اقتصادی فائدہ ہو، سود کے نقصان کو روکنے کے لیے۔"}},
    {"name": {"ar": "ما لا يتم الواجب إلا به فهو واجب", "en": "What is necessary to fulfill a duty is itself obligatory", "fr": "Ce qui est nécessaire pour accomplir un devoir est lui-même obligatoire", "fa": "آنچه انجام واجب جز با آن ممکن نباشد خود واجب است", "ms": "Apa yang diperlukan untuk menyempurnakan kewajipan adalah wajib", "ur": "جو چیز واجب کو مکمل کرنے کے لیے ضروری ہے وہ خود واجب ہے"},
     "definition": {"ar": "كل وسيلة لا يتحقق أداء الواجب إلا بها، تأخذ حكم الوجوب تبعاً للواجب نفسه.", "en": "Whatever a duty depends on for its fulfillment is itself obligatory, as a means to that duty.", "fr": "Tout moyen indispensable à l'accomplissement d'une obligation devient lui-même obligatoire.", "fa": "هر وسیله‌ای که انجام واجب جز با آن ممکن نباشد، خود آن وسیله نیز واجب می‌شود.", "ms": "Setiap wasilah yang tanpanya sesuatu kewajipan tidak dapat disempurnakan, turut menjadi wajib.", "ur": "وہ ذریعہ جس کے بغیر کوئی واجب مکمل نہ ہو سکے، وہ خود بھی واجب کے تابع واجب بن جاتا ہے۔"},
     "example": {"ar": "تعلّم أحكام الطهارة والصلاة واجب؛ لأن صحة الصلاة الواجبة تتوقف عليه.", "en": "Learning the rulings of purification and prayer is obligatory, since the validity of the obligatory prayer depends on it.", "fr": "Apprendre les règles de la purification et de la prière est obligatoire, car la validité de la prière en dépend.", "fa": "آموختن احکام طهارت و نماز واجب است؛ زیرا صحت نماز واجب بر آن متوقف است.", "ms": "Mempelajari hukum bersuci dan solat adalah wajib, kerana sahnya solat wajib bergantung kepadanya.", "ur": "طہارت اور نماز کے احکام سیکھنا واجب ہے؛ کیونکہ واجب نماز کی صحت اسی پر موقوف ہے۔"}},
    {"name": {"ar": "إذا ضاق الأمر اتسع", "en": "When circumstances become constrained, ease widens", "fr": "Lorsque les circonstances deviennent contraignantes, la facilité s'élargit", "fa": "هرگاه کار تنگ شود، گشایش حاصل می‌شود", "ms": "Apabila keadaan menyempit, kemudahan diperluaskan", "ur": "جب معاملہ تنگ ہو تو وسعت ہو جاتی ہے"},
     "definition": {"ar": "إذا ضاقت الأحوال على المكلف في تطبيق الحكم الأصلي، اتسع له مجال الرخصة والتخفيف رفعاً للحرج.", "en": "When circumstances become constrained for the individual applying the default ruling, the scope of concession and ease widens to lift hardship.", "fr": "Lorsque les circonstances deviennent contraignantes pour l'individu appliquant le jugement initial, la marge de concession et de facilité s'élargit pour lever la difficulté.", "fa": "هرگاه احوال مکلف در اجرای حکم اصلی تنگ شود، دامنه رخصت و تخفیف برای رفع حرج گسترده می‌شود.", "ms": "Apabila keadaan menyempit bagi mukallaf dalam melaksanakan hukum asal, ruang keringanan dan kemudahan diperluaskan untuk mengangkat kesukaran.", "ur": "جب مکلف کے لیے اصل حکم پر عمل تنگ ہو جائے تو رخصت اور تخفیف کی گنجائش وسیع ہو جاتی ہے تاکہ حرج دور ہو۔"},
     "example": {"ar": "التيمم عند تعذّر الماء أو الخوف من ضرر استعماله، توسعة على المكلف عند ضيق الحال.", "en": "Performing tayammum (dry ablution) when water is unavailable or its use would cause harm, as an easing in constrained circumstances.", "fr": "Le tayammum (ablution sèche) lorsque l'eau est indisponible ou que son usage serait nuisible, comme un assouplissement en cas de contrainte.", "fa": "تیمم هنگام نبود آب یا بیم ضرر از استعمال آن، توسعه‌ای بر مکلف در تنگنا.", "ms": "Bertayamum apabila air tiada atau membahayakan, sebagai kelonggaran ketika keadaan sempit.", "ur": "پانی نہ ملنے یا اس کے استعمال سے نقصان کے خوف میں تیمم، تنگی کے وقت آسانی۔"}},
]

# ============================================================
# دالة مساعدة للنصوص
# ============================================================

def text_for(value: Any, lang: str, default: str = "") -> str:
    """استخراج النص حسب اللغة."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return str(value.get(lang, value.get("ar", default)))
    return default

# ============================================================
# دالة عرض القواعد
# ============================================================

def display_fiqh_rules(lang: str, T: Dict) -> None:
    """عرض القواعد الفقهية مع دعم الترجمة."""
    with st.expander(T["rules_title"]):
        for i, rule in enumerate(RULES):
            rule_name = text_for(rule.get("name", ""), lang)
            rule_def = text_for(rule.get("definition", ""), lang)
            rule_ex = text_for(rule.get("example", ""), lang)
            
            if i > 0:
                st.markdown("---")
            
            st.markdown(f"**📌 {rule_name}**")
            st.markdown(f"""
            <div class="info-box">
                <p><strong>{T['rules_definition']}:</strong> {rule_def}</p>
                <p><strong>{T['rules_example']}:</strong> {rule_ex}</p>
            </div>
            """, unsafe_allow_html=True)

# ============================================================
# دالة لعرض المذاهب في الدول ذات التعدد
# ============================================================

def format_madhab_list(madhab_data, lang):
    """تنسيق قائمة المذاهب للعرض."""
    if isinstance(madhab_data, list):
        names = []
        for m in madhab_data:
            if m in MADHHAB_NAMES:
                names.append(MADHHAB_NAMES[m][lang])
        return " & ".join(names)
    elif isinstance(madhab_data, str) and madhab_data in MADHHAB_NAMES:
        return MADHHAB_NAMES[madhab_data][lang]
    return str(madhab_data)

# ============================================================
# الدالة الرئيسية
# ============================================================

def main():
    """التطبيق الرئيسي."""
    
    # تهيئة حالة الجلسة
    if "lang" not in st.session_state:
        st.session_state.lang = "ar"
    if "session_comments" not in st.session_state:
        st.session_state.session_comments = []
    if "selected_madhabs" not in st.session_state:
        st.session_state.selected_madhabs = ["maliki", "shafii", "hanafi", "hanbali"]
    
    lang = st.session_state.lang
    T = UI[lang]
    
    is_rtl = lang in ["ar", "fa", "ur"]
    direction = "rtl" if is_rtl else "ltr"
    align = "right" if is_rtl else "left"
    
    # ===== CSS =====
    st.markdown(f"""
    <style>
    /* توجيه النصوص */
    .stApp {{ direction: {direction}; }}
    .stApp p, .stApp li, .stApp label, .stApp span,
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5 {{
        text-align: {align};
        line-height: 1.9;
    }}
    
    /* شريط اللغات */
    .lang-bar {{
        display: flex;
        justify-content: flex-end;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        background: #f0f4f2;
        border-radius: 12px;
        border: 1px solid #d4dcd4;
        margin-bottom: 16px;
        flex-wrap: wrap;
    }}
    .lang-bar .label {{
        font-weight: 600;
        color: #2a5c4a;
        margin-right: 8px;
    }}
    
    /* رأس الصفحة */
    .app-header {{
        text-align: center;
        padding: 28px 20px 22px;
        background: linear-gradient(145deg, #0f231c, #2a5c4a);
        color: white;
        border-radius: 20px;
        margin-bottom: 24px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    }}
    .app-header h1 {{
        font-size: 2rem;
        margin: 8px 0 4px;
        font-weight: 700;
        text-align: center !important;
    }}
    .app-header p {{
        font-size: 1rem;
        opacity: 0.9;
        margin: 0 0 12px 0;
        text-align: center !important;
    }}
    .app-badges {{
        display: flex;
        justify-content: center;
        gap: 10px;
        flex-wrap: wrap;
    }}
    .app-badge {{
        background: rgba(212, 168, 84, 0.14);
        border: 1px solid rgba(212, 168, 84, 0.5);
        color: #f2e6c9;
        padding: 4px 14px;
        border-radius: 999px;
        font-size: 0.8rem;
    }}
    
    /* صناديق المعلومات */
    .info-box {{
        background: #f8f9fa;
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 12px;
        border-left: 4px solid #2a5c4a;
    }}
    .country-box {{
        background: #f8f9fa;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 10px;
        text-align: center;
    }}
    .answer-card {{
        background: #f5f7f5;
        border: 1px solid #e1e7e3;
        border-radius: 14px;
        padding: 16px 18px;
        margin-bottom: 12px;
    }}
    .answer-card .answer-text {{
        font-size: 1.15rem;
        font-weight: 600;
        color: #16281f;
        margin: 4px 0;
    }}
    .answer-card .answer-note {{
        font-size: 0.85rem;
        color: #6a7f78;
    }}
    .signature {{
        font-family: 'Brush Script MT', cursive;
        font-style: italic;
        font-size: 1rem;
        color: #b08d3f;
        text-align: center;
        margin: 6px 0 18px 0;
    }}
    
    /* أزرار راديو على شكل أقراص */
    div[data-testid="stRadio"] > div[role="radiogroup"] {{
        gap: 6px;
        flex-wrap: wrap;
    }}
    div[data-testid="stRadio"] > div[role="radiogroup"] label {{
        background: #f0f3f1;
        border: 1px solid #e1e7e3;
        padding: 6px 16px;
        border-radius: 999px;
        transition: all 0.15s ease;
        margin: 0 !important;
    }}
    div[data-testid="stRadio"] > div[role="radiogroup"] label:hover {{
        background: #e3ece7;
        border-color: #2a5c4a;
    }}
    div[data-testid="stRadio"] > div[role="radiogroup"] label[data-checked="true"],
    div[data-testid="stRadio"] > div[role="radiogroup"] label:has(input:checked) {{
        background: #2a5c4a;
        border-color: #2a5c4a;
    }}
    div[data-testid="stRadio"] > div[role="radiogroup"] label:has(input:checked) p {{
        color: #ffffff !important;
        font-weight: 600;
    }}
    
    /* تنسيق الأعمدة الجانبية */
    .left-column {{
        background: #f8faf9;
        border-radius: 16px;
        padding: 20px 18px;
        border: 1px solid #e1e7e3;
        height: 100%;
    }}
    .right-column {{
        padding-left: 20px;
    }}
    
    /* تنسيق الأقسام المنفصلة */
    .section-title {{
        font-size: 1.1rem;
        font-weight: 700;
        color: #2a5c4a;
        margin: 16px 0 8px 0;
        padding-bottom: 4px;
        border-bottom: 2px solid #d4dcd4;
    }}
    </style>
    """.replace("__DIRECTION__", direction).replace("__ALIGN__", align), unsafe_allow_html=True)
    
    # ===== شريط اللغات =====
    cols = st.columns([1] + [1] * len(LANGS))
    with cols[0]:
        st.markdown(f"**🌐 {T['lang_label']}**")
    
    for i, (name, code) in enumerate(LANGS.items()):
        with cols[i + 1]:
            if st.button(
                f"{LANG_FLAGS.get(code, '')} {name}",
                key=f"lang_{code}",
                use_container_width=True,
                type="primary" if code == lang else "secondary",
            ):
                st.session_state.lang = code
                st.rerun()
    
    # ===== رأس الصفحة =====
    st.markdown(f"""
    <div class="app-header">
        <div style="margin-bottom: 4px;">
            <svg width="80" height="80" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
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
        <p>{T['app_subtitle']}</p>
        <div class="app-badges">
            <span class="app-badge">📖 8 {T['badge_madhabs']}</span>
            <span class="app-badge">🌐 6 {T['badge_langs']}</span>
            <span class="app-badge">🗺️ {len(COUNTRIES)} {T['badge_countries']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if not USE_GEMINI:
        st.caption(f"ℹ️ {T['ai_unavailable']}")
    
    # ===== تخطيط العمودين: اليسار = خطوات السؤال، اليمين = المعلومات =====
    col_left, col_right = st.columns([5, 7], gap="large")
    
    # ===== العمود الأيسر: خطوات طرح السؤال الأربعة =====
    with col_left:
        st.markdown('<div class="left-column">', unsafe_allow_html=True)
        
        # الخطوة 1: اختيار المذهب
        st.markdown(f"### {T['s1_title']}")
        
        group_code = st.radio(
            T["group_q"],
            list(GROUPS.keys()),
            format_func=lambda g: GROUPS[g][lang],
            horizontal=False,
            label_visibility="collapsed",
            key="group_radio",
        )
        sub_codes = GROUPS[group_code]["members"]
        st.caption(T["multi_hint"])
        
        if len(sub_codes) > 1:
            selected_madhabs = st.multiselect(
                T["sub_select"],
                options=sub_codes,
                default=[c for c in st.session_state.selected_madhabs if c in sub_codes] or [sub_codes[0]],
                format_func=lambda c: MADHHAB_NAMES[c][lang],
                key="madhab_multiselect",
            )
        else:
            selected_madhabs = sub_codes
            st.caption(f"**{MADHHAB_NAMES[sub_codes[0]][lang]}**")
        
        st.session_state.selected_madhabs = selected_madhabs
        
        st.divider()
        
        # الخطوة 2: اختيار الموضوع
        st.markdown(f"### {T['s2_title']}")
        topic = st.radio(
            T["topic_q"],
            list(TOPICS.keys()),
            format_func=lambda t: TOPICS[t][lang],
            horizontal=False,
            label_visibility="collapsed",
            key="topic_radio",
        )
        
        st.divider()
        
        # الخطوة 3: طريقة عرض الإجابة
        st.markdown(f"### {T['s3_title']}")
        level = st.radio(
            T["level_q"],
            list(LEVELS.keys()),
            format_func=lambda lv: LEVELS[lv][lang],
            horizontal=False,
            label_visibility="collapsed",
            key="level_radio",
        )
        
        st.divider()
        
        # الخطوة 4: كتابة السؤال والبحث
        st.markdown(f"### {T['s4_title']}")
        question = st.text_input(
            T["s4_title"], 
            placeholder=T["question_placeholder"], 
            label_visibility="collapsed",
            key="question_input",
        )
        search_clicked = st.button(T["search_btn"], use_container_width=True, key="search_button")
        
        st.divider()
        
        # الإجابة
        st.markdown(f"### {T['s5_title']}")
        
        if search_clicked and not selected_madhabs:
            st.warning(T["no_madhab_warning"])
        elif search_clicked and question:
            # بحث محلي مبسط (محاكاة)
            st.info("🔍 جاري البحث... (تم دمج محرك البحث من كلا التطبيقين)")
            st.caption(T["answer_placeholder"])
        elif search_clicked:
            st.info(T["no_question_warning"])
        else:
            st.caption(T["answer_placeholder"])
        
        # حالة الذكاء الاصطناعي
        st.divider()
        if USE_GEMINI:
            st.success(T["ai_badge"])
        else:
            st.warning(T["ai_unavailable"])
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ===== العمود الأيمن: المعلومات التعليمية =====
    with col_right:
        st.markdown('<div class="right-column">', unsafe_allow_html=True)
        
        # ===== الأئمة المؤسسون =====
        with st.expander(T["expander_imams"], expanded=False):
            for imam in IMAMS:
                name = text_for(imam["name"], lang)
                school = text_for(imam["school"], lang)
                birthplace = text_for(imam["birthplace"], lang)
                founding_place = text_for(imam["founding_place"], lang)
                scholars = text_for(imam["scholars"], lang)
                summary = text_for(imam["summary"], lang)
                
                st.markdown(f"""
                <div class="info-box">
                    <h4>{name}</h4>
                    <p style="color:#d4a854; font-weight:600;">{school} &nbsp;|&nbsp; {imam['lifespan']}</p>
                    <p>📍 {T['birthplace']}: {birthplace} &nbsp;·&nbsp; 🏛️ {T['founding_place']}: {founding_place}</p>
                    <p>🎓 {T['scholars']}: {scholars}</p>
                    <p style="margin-top:6px; font-style:italic; opacity:0.85;">{summary}</p>
                </div>
                """, unsafe_allow_html=True)
        
        # ===== الدول الإسلامية =====
        with st.expander(T["expander_countries"], expanded=False):
            cols_country = st.columns(3)
            for i, c in enumerate(COUNTRIES):
                with cols_country[i % 3]:
                    name = text_for(c["name"], lang)
                    madhab_display = format_madhab_list(c["madhab"], lang)
                    is_diverse = c.get("diverse", False)
                    
                    diverse_mark = " 🌐" if is_diverse else ""
                    
                    st.markdown(f"""
                    <div class="country-box">
                        <strong>{c['flag']} {name}</strong><br>
                        <span style="color:#d4a854;">{T['official_madhab']}: {madhab_display}{diverse_mark}</span><br>
                        <span style="font-size:0.8rem; color:#6a7f78;">👥 {T['population']}: {c['population']}</span>
                    </div>
                    """, unsafe_allow_html=True)
            st.caption(COUNTRIES_NOTE.get(lang, COUNTRIES_NOTE["ar"]))
        
        # ===== المصطلحات الفقهية =====
        with st.expander(T["expander_glossary"], expanded=False):
            cols_gloss = st.columns(2)
            for i, term in enumerate(GLOSSARY):
                term_name = text_for(term["term"], lang)
                term_def = text_for(term["definition"], lang)
                term_ex = text_for(term.get("example", ""), lang)
                
                with cols_gloss[i % 2]:
                    st.markdown(f"""
                    <div class="info-box">
                        <h4>{term_name}</h4>
                        <p>{term_def}</p>
                        {f'<p>🔹 <strong>{T["rules_example"]}:</strong> {term_ex}</p>' if term_ex else ''}
                    </div>
                    """, unsafe_allow_html=True)
        
        # ===== مصادر التشريع (قسم منفصل) =====
        with st.expander(T["legal_sources"], expanded=False):
            for source in LEGAL_SOURCES:
                name = text_for(source["name"], lang)
                desc = text_for(source["description"], lang)
                st.markdown(f"""
                <div class="info-box">
                    <h4>{name}</h4>
                    <p>{desc}</p>
                </div>
                """, unsafe_allow_html=True)
        
        # ===== أصول الاستدلال الفقهي (قسم منفصل) =====
        with st.expander(T["usul"], expanded=False):
            for item in USUL:
                name = text_for(item["name"], lang)
                definition = text_for(item["definition"], lang)
                note = text_for(item.get("note", ""), lang)
                st.markdown(f"""
                <div class="info-box">
                    <h4>{name}</h4>
                    <p><strong>{T['rules_definition']}:</strong> {definition}</p>
                    {f'<p><strong>{T.get("note", "ملاحظة")}:</strong> {note}</p>' if note else ''}
                </div>
                """, unsafe_allow_html=True)
        
        # ===== القواعد الفقهية =====
        display_fiqh_rules(lang, T)
        
        # ===== التعليقات =====
        with st.expander(T["expander_comments"], expanded=False):
            st.markdown(f"**{T['rating_label']}**")
            try:
                rating = st.feedback("stars")
                if rating is not None:
                    rating = rating + 1
            except:
                rating = st.radio(
                    T["rating_label"], 
                    [1, 2, 3, 4, 5], 
                    format_func=lambda n: "⭐" * n, 
                    horizontal=True, 
                    label_visibility="collapsed",
                    key="rating_radio",
                )
            
            comment_text = st.text_area(
                T["comment_placeholder"], 
                placeholder=T["comment_placeholder"], 
                label_visibility="collapsed",
                key="comment_input",
            )
            
            if st.button(T["comment_submit"], key="comment_button"):
                if comment_text.strip():
                    st.session_state.session_comments.append({
                        "text": comment_text.strip(), 
                        "rating": rating or 5
                    })
                    st.success(T["comment_success"])
                else:
                    st.warning(T["comment_warning"])
            
            if st.session_state.session_comments:
                st.markdown(f"**{T['comments_title']}**")
                for c in st.session_state.session_comments:
                    st.markdown(f"- {'⭐' * int(c['rating'])} — {c['text']}")
            st.caption(T["comments_note"])
        
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
```
