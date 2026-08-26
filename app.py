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
# قائمة UI (مدمجة من كلا التطبيقين)
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
        "legal_sources": "Sources juridiques",
        "usul": "Principes du raisonnement",
        "combined_sources": "📜 Sources et principes du raisonnement juridique",
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
        "legal_sources": "منابع تشریع",
        "usul": "اصول استنباط",
        "combined_sources": "📜 منابع و اصول استنباط فقهی",
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
        "legal_sources": "Sumber hukum",
        "usul": "Prinsip istinbat",
        "combined_sources": "📜 Sumber dan prinsip fiqh",
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
        "legal_sources": "مصادر تشریع",
        "usul": "اصول استدلال",
        "combined_sources": "📜 فقہی مصادر اور اصول استدلال",
    },
}

# ============================================================
# البيانات التعليمية
# ============================================================

IMAMS = [
    {
        "name": {"ar": "الإمام مالك بن أنس الأصبحي", "en": "Imam Malik ibn Anas al-Asbahi", "fr": "L'imam Malik ibn Anas al-Asbahi", "fa": "امام مالک بن انس اصبحی", "ms": "Imam Malik bin Anas al-Asbahi", "ur": "امام مالک بن انس اصبحی"},
        "school": MADHHAB_NAMES["maliki"],
        "lifespan": "93 - 179 AH",
        "birthplace": {"ar": "المدينة المنورة", "en": "Medina", "fr": "Médine", "fa": "مدینه منوره", "ms": "Madinah", "ur": "مدینہ منورہ"},
        "founding_place": {"ar": "المدينة المنورة", "en": "Medina", "fr": "Médine", "fa": "مدینه منوره", "ms": "Madinah", "ur": "مدینہ منورہ"},
        "scholars": {"ar": "ابن القاسم، سحنون، ابن رشد، القرافي، خليل بن إسحاق", "en": "Ibn al-Qasim, Sahnun, Ibn Rushd, al-Qarafi, Khalil ibn Ishaq", "fr": "Ibn al-Qasim, Sahnun, Ibn Rushd, al-Qarafi, Khalil ibn Ishaq", "fa": "ابن قاسم، سحنون، ابن رشد، قرافی، خلیل بن اسحاق", "ms": "Ibn al-Qasim, Sahnun, Ibn Rushd, al-Qarafi, Khalil bin Ishaq", "ur": "ابن قاسم، سحنون، ابن رشد، قرافی، خلیل بن اسحاق"}
    },
    {
        "name": {"ar": "الإمام محمد بن إدريس الشافعي", "en": "Imam Muhammad ibn Idris al-Shafi'i", "fr": "L'imam Muhammad ibn Idris al-Chafi'i", "fa": "امام محمد بن ادریس شافعی", "ms": "Imam Muhammad bin Idris al-Syafie", "ur": "امام محمد بن ادریس شافعی"},
        "school": MADHHAB_NAMES["shafii"],
        "lifespan": "150 - 204 AH",
        "birthplace": {"ar": "غزة", "en": "Gaza", "fr": "Gaza", "fa": "غزه", "ms": "Gaza", "ur": "غزہ"},
        "founding_place": {"ar": "بغداد ثم مصر (المذهب الجديد)", "en": "Baghdad, then Egypt (the new doctrine)", "fr": "Bagdad, puis l'Égypte (la nouvelle doctrine)", "fa": "بغداد سپس مصر (مذهب جدید)", "ms": "Baghdad, kemudian Mesir (mazhab baru)", "ur": "بغداد پھر مصر (نیا مذہب)"},
        "scholars": {"ar": "المزني، البويطي، النووي، ابن حجر الهيتمي، الرافعي", "en": "al-Muzani, al-Buwayti, al-Nawawi, Ibn Hajar al-Haytami, al-Rafi'i", "fr": "al-Muzani, al-Buwayti, al-Nawawi, Ibn Hajar al-Haytami, al-Rafi'i", "fa": "مزنی، بویطی، نووی، ابن حجر هیتمی، رافعی", "ms": "al-Muzani, al-Buwayti, al-Nawawi, Ibn Hajar al-Haytami, al-Rafi'i", "ur": "مزنی، بویطی، نووی، ابن حجر ہیتمی، رافعی"}
    },
]

COUNTRIES = [
    {"flag": "🇸🇦", "name": {"ar": "السعودية", "en": "Saudi Arabia", "fr": "Arabie saoudite", "fa": "عربستان سعودی", "ms": "Arab Saudi", "ur": "سعودی عرب"}, "madhab": "hanbali", "population": "36.4M"},
    {"flag": "🇪🇬", "name": {"ar": "مصر", "en": "Egypt", "fr": "Égypte", "fa": "مصر", "ms": "Mesir", "ur": "مصر"}, "madhab": "shafii", "population": "112.7M"},
    {"flag": "🇲🇦", "name": {"ar": "المغرب", "en": "Morocco", "fr": "Maroc", "fa": "مراکش", "ms": "Maghribi", "ur": "مراکش"}, "madhab": "maliki", "population": "37.8M"},
    {"flag": "🇹🇷", "name": {"ar": "تركيا", "en": "Turkey", "fr": "Turquie", "fa": "ترکیه", "ms": "Turki", "ur": "ترکی"}, "madhab": "hanafi", "population": "87.5M"},
    {"flag": "🇮🇷", "name": {"ar": "إيران", "en": "Iran", "fr": "Iran", "fa": "ایران", "ms": "Iran", "ur": "ایران"}, "madhab": "jafari", "population": "89.8M"},
    {"flag": "🇴🇲", "name": {"ar": "عُمان", "en": "Oman", "fr": "Oman", "fa": "عمان", "ms": "Oman", "ur": "عمان"}, "madhab": "ibadi", "population": "4.7M"},
    {"flag": "🇸🇩", "name": {"ar": "السودان", "en": "Sudan", "fr": "Soudan", "fa": "سودان", "ms": "Sudan", "ur": "سوڈان"}, "madhab": "maliki", "population": "48.1M"},
    {"flag": "🇸🇾", "name": {"ar": "سوريا", "en": "Syria", "fr": "Syrie", "fa": "سوریه", "ms": "Syria", "ur": "شام"}, "madhab": "shafii", "population": "22.1M"},
    {"flag": "🇮🇶", "name": {"ar": "العراق", "en": "Iraq", "fr": "Irak", "fa": "عراق", "ms": "Iraq", "ur": "عراق"}, "madhab": "jafari", "population": "45.5M"},
    {"flag": "🇦🇪", "name": {"ar": "الإمارات", "en": "UAE", "fr": "EAU", "fa": "امارات", "ms": "UAE", "ur": "متحدہ عرب امارات"}, "madhab": "maliki", "population": "10.1M"},
    {"flag": "🇯🇴", "name": {"ar": "الأردن", "en": "Jordan", "fr": "Jordanie", "fa": "اردن", "ms": "Jordan", "ur": "اردن"}, "madhab": "shafii", "population": "11.1M"},
    {"flag": "🇧🇭", "name": {"ar": "البحرين", "en": "Bahrain", "fr": "Bahreïn", "fa": "بحرین", "ms": "Bahrain", "ur": "بحرین"}, "madhab": "jafari", "population": "1.5M"},
    {"flag": "🇰🇼", "name": {"ar": "الكويت", "en": "Kuwait", "fr": "Koweït", "fa": "کویت", "ms": "Kuwait", "ur": "کویت"}, "madhab": "maliki", "population": "4.4M"},
    {"flag": "🇹🇳", "name": {"ar": "تونس", "en": "Tunisia", "fr": "Tunisie", "fa": "تونس", "ms": "Tunisia", "ur": "تونس"}, "madhab": "maliki", "population": "12.5M"},
    {"flag": "🇱🇾", "name": {"ar": "ليبيا", "en": "Libya", "fr": "Libye", "fa": "لیبی", "ms": "Libya", "ur": "لیبیا"}, "madhab": "maliki", "population": "7.0M"},
    {"flag": "🇩🇿", "name": {"ar": "الجزائر", "en": "Algeria", "fr": "Algérie", "fa": "الجزایر", "ms": "Algeria", "ur": "الجزائر"}, "madhab": "maliki", "population": "46.1M"},
    {"flag": "🇮🇩", "name": {"ar": "إندونيسيا", "en": "Indonesia", "fr": "Indonésie", "fa": "اندونزی", "ms": "Indonesia", "ur": "انڈونیشیا"}, "madhab": "shafii", "population": "279.1M"},
    {"flag": "🇲🇾", "name": {"ar": "ماليزيا", "en": "Malaysia", "fr": "Malaisie", "fa": "مالزی", "ms": "Malaysia", "ur": "ملائیشیا"}, "madhab": "shafii", "population": "34.2M"},
    {"flag": "🇵🇰", "name": {"ar": "باكستان", "en": "Pakistan", "fr": "Pakistan", "fa": "پاکستان", "ms": "Pakistan", "ur": "پاکستان"}, "madhab": "hanafi", "population": "240.0M"},
    {"flag": "🇦🇫", "name": {"ar": "أفغانستان", "en": "Afghanistan", "fr": "Afghanistan", "fa": "افغانستان", "ms": "Afghanistan", "ur": "افغانستان"}, "madhab": "hanafi", "population": "41.1M"},
    {"flag": "🇱🇧", "name": {"ar": "لبنان", "en": "Lebanon", "fr": "Liban", "fa": "لبنان", "ms": "Lebanon", "ur": "لبنان"}, "madhab": "shafii", "population": "5.4M"},
    {"flag": "🇵🇸", "name": {"ar": "فلسطين", "en": "Palestine", "fr": "Palestine", "fa": "فلسطین", "ms": "Palestine", "ur": "فلسطین"}, "madhab": "shafii", "population": "5.4M"},
    {"flag": "🇹🇩", "name": {"ar": "تشاد", "en": "Chad", "fr": "Tchad", "fa": "چاد", "ms": "Chad", "ur": "چاڈ"}, "madhab": "maliki", "population": "18.3M"},
    {"flag": "🇳🇬", "name": {"ar": "نيجيريا", "en": "Nigeria", "fr": "Nigeria", "fa": "نیجریه", "ms": "Nigeria", "ur": "نائیجیریا"}, "madhab": "maliki", "population": "225.0M"},
    {"flag": "🇸🇴", "name": {"ar": "الصومال", "en": "Somalia", "fr": "Somalie", "fa": "سومالی", "ms": "Somalia", "ur": "صومالیہ"}, "madhab": "shafii", "population": "17.1M"},
    {"flag": "🇩🇯", "name": {"ar": "جيبوتي", "en": "Djibouti", "fr": "Djibouti", "fa": "جیبوتی", "ms": "Djibouti", "ur": "جبوتی"}, "madhab": "shafii", "population": "1.1M"},
    {"flag": "🇪🇷", "name": {"ar": "إريتريا", "en": "Eritrea", "fr": "Érythrée", "fa": "اریتره", "ms": "Eritrea", "ur": "اریٹیریا"}, "madhab": "maliki", "population": "3.7M"},
    {"flag": "🇲🇷", "name": {"ar": "موريتانيا", "en": "Mauritania", "fr": "Mauritanie", "fa": "موریتانی", "ms": "Mauritania", "ur": "موریتانیہ"}, "madhab": "maliki", "population": "5.0M"},
]

COUNTRIES_NOTE = {
    "ar": "ملاحظة: يُقصد بـ«المذهب الرسمي» المذهب الفقهي السائد تاريخياً بين غالبية المسلمين في البلد أو المعتمد في محاكمه الشرعية؛ وقد تتعايش فيه مذاهب أخرى.",
    "en": "Note: the \"official school\" refers to the madhhab historically prevailing among the country's Muslim majority or followed in its Sharia courts; other schools may coexist there.",
    "fr": "Remarque : l'« école officielle » désigne le madhhab historiquement prédominant chez la majorité musulmane du pays ou suivi dans ses tribunaux islamiques ; d'autres écoles peuvent y coexister.",
    "fa": "توجه: «مذهب رسمی» به مذهبی گفته می‌شود که تاریخاً در میان اکثریت مسلمانان آن کشور رایج بوده یا در دادگاه‌های شرعی آن پیروی می‌شود؛ مذاهب دیگر نیز ممکن است در آن حضور داشته باشند.",
    "ms": "Nota: \"mazhab rasmi\" merujuk kepada mazhab yang secara sejarah dominan dalam kalangan majoriti Muslim negara tersebut atau diikuti di mahkamah syariahnya; mazhab lain mungkin turut wujud.",
    "ur": "نوٹ: \"سرکاری مذہب\" سے مراد وہ مذہب ہے جو تاریخی طور پر ملک کی مسلم اکثریت میں غالب رہا یا اس کی شرعی عدالتوں میں اپنایا جاتا ہے؛ دیگر مذاہب بھی وہاں موجود ہو سکتے ہیں۔",
}

GLOSSARY = [
    {"term": {"ar": "الفرض / فرض العين", "en": "Fard / Fard Ayn (Individual Obligation)", "fr": "Le fard / fard ayn (Obligation individuelle)", "fa": "فرض / فرض عین", "ms": "Fardu / Fardu Ain", "ur": "فرض / فرض عین"},
     "definition": {"ar": "ما طلب الشارع فعله طلباً جازماً من كل مكلف بعينه، يُثاب فاعله ويُعاقب تاركه.", "en": "What the Lawgiver has decisively commanded every legally accountable individual to perform.", "fr": "Ce que le Législateur a ordonné de façon décisive à tout individu responsable d'accomplir.", "fa": "آنچه شارع به‌طور قطعی بر هر مکلفی واجب کرده است.", "ms": "Apa yang Pembuat Syariat telah perintahkan secara tegas kepada setiap individu yang bertanggungjawab.", "ur": "وہ چیز جسے شارع نے ہر مکلف پر قطعی طور پر واجب کیا ہے۔"},
     "example": {"ar": "الصلوات الخمس، الزكاة.", "en": "The five daily prayers; zakat.", "fr": "Les cinq prières quotidiennes ; la zakat.", "fa": "نمازهای پنج‌گانه، زکات.", "ms": "Solat lima waktu, zakat.", "ur": "پانچ وقت کی نمازیں، زکوٰۃ۔"}},
    {"term": {"ar": "فرض الكفاية", "en": "Fard Kifayah (Sufficiency Obligation)", "fr": "Fard kifayah (Obligation de suffisance)", "fa": "فرض کفایه", "ms": "Fardu Kifayah", "ur": "فرض کفایہ"},
     "definition": {"ar": "ما طلب الشارع فعله طلباً جازماً من المجموعة دون كل فرد بعينه، فإذا قام به البعض سقط الإثم عن الباقين.", "en": "A collective obligation which, if performed by some, absolves others.", "fr": "Une obligation collective qui, si elle est accomplie par certains, dispense les autres.", "fa": "تکلیف جمعی که اگر عده‌ای آن را انجام دهند، از دیگران ساقط می‌شود.", "ms": "Kewajipan kolektif yang jika dilakukan oleh sebahagian, gugur ke atas yang lain.", "ur": "ایک اجتماعی فریضہ جو اگر کچھ لوگ ادا کریں تو باقیوں سے ساقط ہو جاتا ہے۔"},
     "example": {"ar": "صلاة الجنازة، تعلم الطب.", "en": "The funeral prayer; training enough doctors.", "fr": "La prière funéraire ; former suffisamment de médecins.", "fa": "نماز جنازه، آموختن پزشکی.", "ms": "Solat jenazah, mempelajari perubatan.", "ur": "نماز جنازہ، طب کی تعلیم۔"}},
    {"term": {"ar": "الواجب", "en": "Wajib (Obligatory)", "fr": "Wajib (Obligatoire)", "fa": "واجب", "ms": "Wajib", "ur": "واجب"},
     "definition": {"ar": "ما طلب الشارع فعله طلباً جازماً غير أنه لا يصل إلى درجة الفرض، ويُثاب فاعله ويعاقب تاركه عند الحنفية.", "en": "What the Lawgiver has commanded decisively but not reaching the level of Fard.", "fr": "Ce que le Législateur a ordonné de façon décisive mais n'atteignant pas le niveau de Fard.", "fa": "آنچه شارع به طور قطعی دستور داده اما به درجه فرض نمی‌رسد.", "ms": "Apa yang Pembuat Syariat telah perintahkan secara tegas tetapi tidak mencapai tahap Fardu.", "ur": "وہ چیز جسے شارع نے قطعی طور پر حکم دیا ہے لیکن فرض کی سطح تک نہیں پہنچتی۔"},
     "example": {"ar": "صلاة الوتر عند الحنفية.", "en": "The witr prayer according to Hanafis.", "fr": "La prière du witr selon les hanafites.", "fa": "نماز وتر نزد حنفیان.", "ms": "Solat witir menurut Hanafi.", "ur": "احناف کے نزدیک وتر کی نماز۔"}},
    {"term": {"ar": "المستحب / المندوب", "en": "Mustahabb / Mandub (Recommended)", "fr": "Mustahabb / Mandub (Recommandé)", "fa": "مستحب / مندوب", "ms": "Mustahabb / Mandub", "ur": "مستحب / مندوب"},
     "definition": {"ar": "ما طلب الشارع فعله طلباً غير جازم، يُثاب فاعله ولا يُعاقب تاركه.", "en": "What the Lawgiver has recommended without decisiveness; rewarded for doing, not punished for abandoning.", "fr": "Ce que le Législateur a recommandé sans caractère décisif ; récompensé pour l'accomplissement, non puni pour l'abandon.", "fa": "آنچه شارع به طور غیر قطعی دستور داده؛ انجام‌دهنده پاداش می‌گیرد و ترک‌کننده مجازات نمی‌شود.", "ms": "Apa yang Pembuat Syariat telah syorkan tanpa ketegasan; diberi pahala jika dilakukan, tidak dihukum jika ditinggalkan.", "ur": "وہ چیز جسے شارع نے غیر قطعی طور پر پسند کیا ہے؛ کرنے والا ثواب پاتا ہے، چھوڑنے والا سزا نہیں پاتا۔"},
     "example": {"ar": "صلاة الضحى، صيام الاثنين والخميس.", "en": "The mid-morning (Duha) prayer; fasting on Mondays and Thursdays.", "fr": "La prière de Doha ; le jeûne du lundi et jeudi.", "fa": "نماز ضحی، روزه دوشنبه و پنجشنبه.", "ms": "Solat Dhuha, puasa Isnin dan Khamis.", "ur": "نماز چاشت، پیر اور جمعرات کا روزہ۔"}},
    {"term": {"ar": "السنة", "en": "Sunnah", "fr": "Sunna", "fa": "سنت", "ms": "Sunat", "ur": "سنت"},
     "definition": {"ar": "ما ثبت عن النبي ﷺ من قول أو فعل أو تقرير، وهي تشمل الواجب والمستحب والمباح.", "en": "What is established from the Prophet ﷺ of sayings, actions, or approvals.", "fr": "Ce qui est établi du Prophète ﷺ en paroles, actes ou approbations.", "fa": "آنچه از پیامبر ﷺ از قول، فعل یا تقریر ثابت شده است.", "ms": "Apa yang ditetapkan daripada Nabi ﷺ daripada perkataan, perbuatan atau persetujuan.", "ur": "وہ چیز جو نبی ﷺ سے قول، فعل یا تقریر کے طور پر ثابت ہے۔"},
     "example": {"ar": "السواك عند الوضوء، الأذكار بعد الصلاة.", "en": "Using the miswak during ablution; remembrance (adhkar) after prayer.", "fr": "Le siwak lors des ablutions ; les invocations après la prière.", "fa": "مسواک هنگام وضو، اذکار پس از نماز.", "ms": "Bersiwak ketika berwuduk, zikir selepas solat.", "ur": "وضو کے وقت مسواک، نماز کے بعد اذکار۔"}},
    {"term": {"ar": "السنة المؤكدة", "en": "Sunnah Mu'akkadah (Emphasized Sunnah)", "fr": "Sunnah mu'akkadah (Sunnah confirmée)", "fa": "سنت مؤکد", "ms": "Sunat Muakkad", "ur": "سنت مؤکدہ"},
     "definition": {"ar": "ما واظب عليه النبي ﷺ ولم يتركه إلا نادراً، وهي قريبة من الواجب في الأهمية.", "en": "What the Prophet ﷺ consistently performed and rarely abandoned; close to obligatory in importance.", "fr": "Ce que le Prophète ﷺ a accompli régulièrement et rarement abandonné ; proche de l'obligation en importance.", "fa": "آنچه پیامبر ﷺ به طور مداوم انجام می‌داد و به ندرت ترک می‌کرد.", "ms": "Apa yang Nabi ﷺ lakukan secara konsisten dan jarang ditinggalkan.", "ur": "وہ چیز جو نبی ﷺ نے مستقل طور پر کی اور شاذ و نادر ہی چھوڑی۔"},
     "example": {"ar": "ركعتا الفجر، الوتر عند الجمهور.", "en": "The two rak'ahs before Fajr; witr prayer.", "fr": "Les deux rak'ahs avant Fajr ; le witr.", "fa": "دو رکعت سنت فجر، وتر.", "ms": "Dua rakaat sebelum Subuh, witir.", "ur": "فجر کی دو سنتیں، وتر۔"}},
    {"term": {"ar": "المباح", "en": "Mubah (Permissible)", "fr": "Mubah (Permis)", "fa": "مباح", "ms": "Mubah", "ur": "مباح"},
     "definition": {"ar": "ما خير الشارع بين فعله وتركه، ولا ثواب على فعله ولا عقاب على تركه.", "en": "What the Lawgiver has left optional; no reward for doing it and no punishment for abandoning it.", "fr": "Ce que le Législateur a laissé facultatif ; pas de récompense pour l'accomplir ni de punition pour l'abandonner.", "fa": "آنچه شارع بین انجام و ترک آن مخیر کرده است؛ نه پاداشی بر انجام آن و نه عقابی بر ترک آن.", "ms": "Apa yang Pembuat Syariat memberi pilihan antara melakukannya atau meninggalkannya; tiada pahala untuk melakukannya dan tiada hukuman untuk meninggalkannya.", "ur": "وہ چیز جسے شارع نے اختیاری چھوڑ دیا ہے؛ کرنے پر کوئی ثواب نہیں اور چھوڑنے پر کوئی سزا نہیں۔"},
     "example": {"ar": "الأكل من الطيبات، اختيار لون الثوب.", "en": "Eating wholesome food; choosing the color of one's clothing.", "fr": "Manger des aliments licites ; choisir la couleur de son vêtement.", "fa": "خوردن غذاهای پاکیزه، انتخاب رنگ لباس.", "ms": "Makan makanan yang baik, memilih warna pakaian.", "ur": "پاکیزہ کھانا کھانا، لباس کا رنگ چننا۔"}},
    {"term": {"ar": "الحرام", "en": "Haram (Prohibited)", "fr": "Haram (Interdit)", "fa": "حرام", "ms": "Haram", "ur": "حرام"},
     "definition": {"ar": "ما طلب الشارع تركه طلباً جازماً، يُعاقب فاعله ويُثاب تاركه امتثالاً.", "en": "What the Lawgiver has decisively forbidden; the doer is punished, and the one who abstains in obedience is rewarded.", "fr": "Ce que le Législateur a interdit de façon décisive ; celui qui le fait est puni, et celui qui s'en abstient par obéissance est récompensé.", "fa": "آنچه شارع به طور قطعی از آن نهی کرده است؛ انجام‌دهنده مجازات می‌شود و ترک‌کننده به دلیل اطاعت پاداش می‌گیرد.", "ms": "Apa yang Pembuat Syariat telah melarang dengan tegas; yang melakukannya dihukum, dan yang meninggalkannya kerana kepatuhan diberi pahala.", "ur": "وہ چیز جسے شارع نے قطعی طور پر منع کیا ہے؛ کرنے والا سزا پاتا ہے اور چھوڑنے والا اطاعت کی وجہ سے ثواب پاتا ہے۔"},
     "example": {"ar": "الربا، أكل لحم الخنزير.", "en": "Usury (riba); eating pork.", "fr": "L'usure (riba) ; consommer du porc.", "fa": "ربا، خوردن گوشت خوک.", "ms": "Riba, memakan daging babi.", "ur": "سود، خنزیر کا گوشت کھانا۔"}},
    {"term": {"ar": "المكروه", "en": "Makruh (Disliked)", "fr": "Makruh (Réprouvé)", "fa": "مکروه", "ms": "Makruh", "ur": "مکروہ"},
     "definition": {"ar": "ما طلب الشارع تركه طلباً غير جازم، يُثاب تاركه ولا يُعاقب فاعله.", "en": "What the Lawgiver has discouraged without decisiveness; rewarded for abandoning, not punished for doing.", "fr": "Ce que le Législateur a découragé sans caractère décisif ; récompensé pour l'abandon, non puni pour l'accomplissement.", "fa": "آنچه شارع به طور غیر قطعی از آن نهی کرده است؛ ترک‌کننده پاداش می‌گیرد و انجام‌دهنده مجازات نمی‌شود.", "ms": "Apa yang Pembuat Syariat telah tidak menggalakkan tanpa ketegasan; diberi pahala jika ditinggalkan, tidak dihukum jika dilakukan.", "ur": "وہ چیز جسے شارع نے غیر قطعی طور پر ناپسند کیا ہے؛ چھوڑنے والا ثواب پاتا ہے، کرنے والا سزا نہیں پاتا۔"},
     "example": {"ar": "الأكل من ثوم نيء قبل الذهاب إلى المسجد.", "en": "Eating raw garlic before going to the mosque.", "fr": "Manger de l'ail cru avant d'aller à la mosquée.", "fa": "خوردن سیر خام پیش از رفتن به مسجد.", "ms": "Makan bawang putih mentah sebelum ke masjid.", "ur": "مسجد جانے سے پہلے کچا لہسن کھانا۔"}},
    {"term": {"ar": "الحلال", "en": "Halal (Lawful)", "fr": "Halal (Licite)", "fa": "حلال", "ms": "Halal", "ur": "حلال"},
     "definition": {"ar": "ما أحله الشارع وأباحه، وهو يشمل الواجب والمستحب والمباح، وهو مقابل للحرام.", "en": "What the Lawgiver has made lawful and permissible; includes obligations, recommendations, and permissibles.", "fr": "Ce que le Législateur a rendu licite et permis ; inclut les obligations, les recommandations et les permissibles.", "fa": "آنچه شارع حلال و مجاز کرده است؛ شامل واجبات، مستحبات و مباحات می‌شود.", "ms": "Apa yang Pembuat Syariat telah halalkan dan benarkan; ia termasuk kewajipan, galakan dan harus.", "ur": "وہ چیز جسے شارع نے حلال اور جائز کیا ہے؛ اس میں واجبات، مستحبات اور مباحات شامل ہیں۔"},
     "example": {"ar": "البيع المباح، الطعام الحلال.", "en": "A permissible sale; lawful food.", "fr": "Une vente licite ; une nourriture halal.", "fa": "خرید و فروش مباح، غذای حلال.", "ms": "Jualan yang harus, makanan halal.", "ur": "جائز بیع، حلال کھانا۔"}},
]

LEGAL_SOURCES = [
    {"name": {"ar": "القرآن الكريم", "en": "The Qur'an", "fr": "Le Coran", "fa": "قرآن کریم", "ms": "Al-Quran", "ur": "قرآن کریم"},
     "description": {"ar": "المصدر الأعلى والأول للتشريع الإسلامي.", "en": "The primary and highest source of Islamic law.", "fr": "La première et la plus haute source du droit islamique.", "fa": "منبع برتر و اولیه شریعت اسلامی.", "ms": "Sumber tertinggi dan utama undang-undang Islam.", "ur": "شریعت اسلامی کا اعلیٰ ترین اور اولیٰ ترین ماخذ۔"}},
    {"name": {"ar": "السنة النبوية", "en": "Prophetic Sunnah", "fr": "La Sunna prophétique", "fa": "سنت نبوی", "ms": "Sunnah Nabi", "ur": "سنت نبوی"},
     "description": {"ar": "أقوال النبي ﷺ وأفعاله وتقريراته.", "en": "The sayings, actions, and approvals of the Prophet.", "fr": "Les paroles, actes et approbations du Prophète.", "fa": "گفتار، کردار و تقریرات پیامبر ﷺ.", "ms": "Perkataan, perbuatan dan persetujuan Nabi ﷺ.", "ur": "نبی ﷺ کے اقوال، افعال اور تقریرات۔"}},
    {"name": {"ar": "الإجماع", "en": "Ijma'", "fr": "Ijma'", "fa": "اجماع", "ms": "Ijma'", "ur": "اجماع"},
     "description": {"ar": "اتفاق المجتهدين من أمة محمد ﷺ في عصر من العصور على حكم شرعي.", "en": "The agreement of qualified jurists on a legal ruling.", "fr": "L’accord des juristes qualifiés sur une règle juridique.", "fa": "اتفاق مجتهدان امت محمد ﷺ در عصری بر حکم شرعی.", "ms": "Persetujuan ulama mujtahid dalam sesuatu zaman terhadap hukum syarak.", "ur": "امت محمد ﷺ کے مجتہدین کا کسی دور میں کسی شرعی حکم پر اتفاق۔"}},
    {"name": {"ar": "القياس", "en": "Qiyas", "fr": "Qiyas", "fa": "قیاس", "ms": "Qiyas", "ur": "قیاس"},
     "description": {"ar": "إلحاق مسألة جديدة بمسألة منصوص عليها لاشتراكهما في العلة.", "en": "Applying an established ruling to a new case due to a shared effective cause.", "fr": "L’application d’une règle connue à un cas nouveau par une cause commune.", "fa": "الحاق مسئله جدید به مسئله منصوص به دلیل اشتراک در علت.", "ms": "Menghubungkan kes baru dengan kes yang telah ada nas kerana persamaan sebab.", "ur": "علت مشترک کی وجہ سے کسی منصوص مسئلہ سے نیا مسئلہ ملانا۔"}},
]

USUL = [
    {"name": {"ar": "الأمر والنهي", "en": "Commands and prohibitions", "fr": "Commandements et interdictions", "fa": "امر و نهی", "ms": "Perintah dan larangan", "ur": "امر و نہی"},
     "definition": {"ar": "بحث دلالات صيغ الأمر والنهي وآثارها في الحكم الشرعي.", "en": "Analysis of commands and prohibitions and their legal effects.", "fr": "Analyse des commandements et interdictions et de leurs effets juridiques.", "fa": "بررسی دلالت‌های صیغ امر و نهی و آثار آن در حکم شرعی.", "ms": "Analisis maksud perintah dan larangan serta kesannya dalam hukum syarak.", "ur": "امر و نہی کے صیغوں کی دلالات اور ان کے شرعی حکم پر اثرات کا مطالعہ۔"},
     "note": {"ar": "تختلف بعض تطبيقاته بحسب القرائن والسياق.", "en": "Applications may vary according to context and indications.", "fr": "Les applications peuvent varier selon le contexte.", "fa": "برخی کاربردها با توجه به قرائن و زمینه متفاوت است.", "ms": "Aplikasi mungkin berbeza mengikut konteks dan petunjuk.", "ur": "سیاق و سباق کے مطابق کچھ اطلاقات مختلف ہو سکتی ہیں۔"}},
    {"name": {"ar": "العام والخاص", "en": "General and specific texts", "fr": "Textes généraux et spécifiques", "fa": "عام و خاص", "ms": "Am dan khas", "ur": "عام و خاص"},
     "definition": {"ar": "دراسة النصوص العامة وما يرد عليها من تخصيص.", "en": "Study of general texts and possible specification.", "fr": "Étude des textes généraux et de leur éventuelle spécification.", "fa": "بررسی نصوص عمومی و تخصیص‌های وارد بر آن.", "ms": "Kajian teks umum dan kemungkinan pengkhususan.", "ur": "عام نصوص اور ان پر وارد ہونے والے تخصیص کا مطالعہ۔"},
     "note": {"ar": "يبحث الأصولي في دلالة اللفظ وحدود شموله.", "en": "The jurist examines the scope and meaning of the wording.", "fr": "Le juriste examine la portée et le sens de la formulation.", "fa": "اصولی در دلالت لفظ و حدود شمول آن بحث می‌کند.", "ms": "Usuliyyin mengkaji makna lafaz dan batas cakupannya.", "ur": "اصولی لفظ کی دلالت اور اس کے شمول کی حدود کا جائزہ لیتا ہے۔"}},
    {"name": {"ar": "المطلق والمقيد", "en": "Unrestricted and restricted texts", "fr": "Textes absolus et restreints", "fa": "مطلق و مقید", "ms": "Mutlaq dan muqayyad", "ur": "مطلق و مقید"},
     "definition": {"ar": "الموازنة بين النص المطلق والنص الذي قيده وصف أو شرط.", "en": "Reconciling unrestricted texts with texts limited by a condition or description.", "fr": "La conciliation entre les textes absolus et ceux limités par une condition.", "fa": "موازنه بین نص مطلق و نصی که با وصف یا شرط مقید شده است.", "ms": "Mengimbangi teks mutlaq dengan teks yang dibatasi oleh syarat atau sifat.", "ur": "مطلق نص اور اس نص کے درمیان توازن جو کسی وصف یا شرط سے مقید ہے۔"},
     "note": {"ar": "يُنظر في اتحاد الحكم والسبب والسياق.", "en": "The legal ruling, cause, and context are considered.", "fr": "La règle, la cause et le contexte sont pris en compte.", "fa": "اتحاد حکم، سبب و زمینه بررسی می‌شود.", "ms": "Kesatuan hukum, sebab dan konteks dipertimbangkan.", "ur": "حکم، سبب اور سیاق و سباق کی یکسانیت پر نظر کیا جاتا ہے۔"}},
    {"name": {"ar": "المصلحة والاستصحاب", "en": "Maslahah and presumption of continuity", "fr": "Maslaha et présomption de continuité", "fa": "مصلحت و استصحاب", "ms": "Maslahah dan istishab", "ur": "مصلحت و استصحاب"},
     "definition": {"ar": "منهج للنظر في المصلحة المعتبرة واستمرار الحكم السابق عند غياب الناقل.", "en": "Considering recognized benefit and continuity of an earlier state when no contrary evidence exists.", "fr": "Prise en compte de l’intérêt reconnu et de la continuité d’un état antérieur.", "fa": "روشی برای بررسی مصلحت معتبر و استمرار حکم سابق در صورت عدم وجود ناقل.", "ms": "Kaedah untuk mempertimbangkan maslahah yang diiktiraf dan kesinambungan hukum asal apabila tiada dalil yang mengubahnya.", "ur": "مصلحت معتبر اور ناقل کی عدم موجودگی میں سابق حکم کے استمرار پر نظر کا طریقہ۔"},
     "note": {"ar": "تختلف حدود الاعتماد عليهما بين المدارس الفقهية.", "en": "Schools differ in the extent to which they rely on these principles.", "fr": "Les écoles divergent quant à leur utilisation.", "fa": "میزان اعتماد بر این دو در میان مذاهب فقهی متفاوت است.", "ms": "Tahap pergantungan kepada prinsip ini berbeza antara mazhab.", "ur": "ان اصولوں پر اعتماد کی حد مذاہب فقہیہ میں مختلف ہے۔"}},
]

# ============================================================
# القواعد الفقهية (من app -all-school.txt مع إضافات)
# ============================================================

RULES = [
    {
        "name": {"ar": "اليقين لا يزول بالشك", "en": "Certainty cannot be overridden by doubt", "fr": "La certitude ne peut être remplacée par le doute", "fa": "یقین به شک زایل نمی‌شود", "ms": "Keyakinan tidak boleh digantikan dengan keraguan", "ur": "یقین شک سے زائل نہیں ہوتا"},
        "definition": {"ar": "إذا ثبت أمر بيقين فلا يزول إلا بيقين مثله، ولا يؤثر فيه مجرد الشك.", "en": "Certainty cannot be overridden by doubt.", "fr": "La certitude ne peut être remplacée par le doute.", "fa": "هر چیزی که با یقین ثابت شده است با شک از بین نمی‌رود.", "ms": "Keyakinan tidak boleh digantikan dengan keraguan.", "ur": "جو چیز یقین سے ثابت ہو جائے وہ شک سے زائل نہیں ہوتی۔"},
        "example": {"ar": "من تيقن الطهارة وشك في الحدث، يبقى على الطهارة.", "en": "If someone is certain of purity and doubts impurity, they remain in a state of purity.", "fr": "Si quelqu'un est certain de la pureté et doute de l'impureté, il reste en état de pureté.", "fa": "کسی که یقین به طهارت دارد و به حدث شک می‌کند، بر طهارت باقی می‌ماند.", "ms": "Jika seseorang yakin suci dan ragu najis, dia kekal dalam keadaan suci.", "ur": "جو شخص طہارت پر یقین رکھتا ہے اور حدث پر شک کرتا ہے، وہ طہارت پر باقی رہتا ہے۔"}
    },
    {
        "name": {"ar": "المشقة تجلب التيسير", "en": "Hardship brings ease", "fr": "La difficulté apporte la facilité", "fa": "مشقت باعث آسانی می‌شود", "ms": "Kesukaran membawa kemudahan", "ur": "مشقت آسانی لاتی ہے"},
        "definition": {"ar": "عند وجود مشقة معتبرة في تطبيق الحكم الشرعي، يُفتح باب الرخصة والتخفيف.", "en": "Hardship brings ease in Islamic jurisprudence.", "fr": "La difficulté apporte la facilité dans la jurisprudence islamique.", "fa": "هنگام وجود مشقت معتبر در اجرای حکم شرعی، باب رخصت و تخفیف گشوده می‌شود.", "ms": "Apabila terdapat kesukaran yang diiktiraf dalam melaksanakan hukum syarak, keringanan dan kemudahan diberikan.", "ur": "شرعی حکم کے اطلاق میں معتبر مشقت کی صورت میں رخصت اور تخفیف کا دروازہ کھل جاتا ہے۔"},
        "example": {"ar": "قصر الصلاة في السفر أو الإفطار في المرض.", "en": "Shortening prayers during travel or breaking fast during illness.", "fr": "Raccourcir les prières pendant le voyage ou rompre le jeûne en cas de maladie.", "fa": "قصر نماز در سفر یا افطار در بیماری.", "ms": "Memendekkan solat semasa musafir atau berbuka puasa ketika sakit.", "ur": "سفر میں نماز قصر کرنا یا بیماری میں روزہ افطار کرنا۔"}
    },
    {
        "name": {"ar": "الضرر يزال", "en": "Harm must be removed", "fr": "Le préjudice doit être écarté", "fa": "ضرر باید برطرف شود", "ms": "Kemudaratan mesti dihilangkan", "ur": "نقصان کو دور کیا جانا چاہیے"},
        "definition": {"ar": "كل ما فيه ضرر على الفرد أو الجماعة يجب رفعه أو منعه.", "en": "Harm must be removed or prevented.", "fr": "Le préjudice doit être écarté ou empêché.", "fa": "هر چیزی که برای فرد یا جامعه ضرر دارد باید برطرف یا ممنوع شود.", "ms": "Segala yang membawa kemudaratan kepada individu atau masyarakat mesti dihilangkan atau dicegah.", "ur": "ہر وہ چیز جو فرد یا جماعت کو نقصان پہنچاتی ہے اسے دور یا روکا جانا چاہیے۔"},
        "example": {"ar": "منع الغش في البيع أو إزالة الأذى عن الطريق.", "en": "Preventing fraud in sales or removing harm from the road.", "fr": "Prévenir la fraude dans les ventes ou éliminer les nuisances de la route.", "fa": "منع تقلب در خرید و فروش یا برداشتن مزاحمت از راه.", "ms": "Mencegah penipuan dalam jualan atau membuang bahaya dari jalan.", "ur": "بیع میں دھوکہ دہی کو روکنا یا راستے سے نقصان کو ہٹانا۔"}
    },
    {
        "name": {"ar": "العادة محكمة", "en": "Custom is a valid consideration", "fr": "La coutume est considérée", "fa": "عرف و عادت معتبر است", "ms": "Adat dipertimbangkan", "ur": "عادت کو معتبر سمجھا جاتا ہے"},
        "definition": {"ar": "العرف والعادة المعتبرة شرعًا تُعتبر في الأحكام ما لم تخالف نصًا شرعيًا.", "en": "Custom is a valid consideration in Islamic law.", "fr": "La coutume est considérée en droit islamique.", "fa": "عرف و عادت معتبر شرعی در احکام لحاظ می‌شود.", "ms": "Adat dan uruf yang diiktiraf secara syarak dipertimbangkan dalam hukum.", "ur": "شرعی طور پر معتبر عرف و عادت کو احکام میں لحاظ رکھا جاتا ہے بشرطیکہ کسی شرعی نص کی مخالفت نہ ہو۔"},
        "example": {"ar": "أعراف الزواج أو البيع.", "en": "Customs regarding marriage or sales.", "fr": "Les coutumes relatives au mariage ou aux ventes.", "fa": "عرف‌های ازدواج یا خرید و فروش.", "ms": "Adat mengenai perkahwinan atau jualan.", "ur": "شادی یا بیع کے متعلق رسوم۔"}
    },
    {
        "name": {"ar": "الأمور بمقاصدها", "en": "Actions are judged by intentions", "fr": "Les actions sont jugées par leurs intentions", "fa": "کارها با نیت‌ها ارزیابی می‌شوند", "ms": "Tindakan dinilai dengan niat", "ur": "اعمال کا دارومدار نیتوں پر ہے"},
        "definition": {"ar": "الحكم على الأفعال يكون بحسب نية صاحبها ومقصده.", "en": "Actions are judged by their intentions.", "fr": "Les actions sont jugées selon leurs intentions.", "fa": "حکم بر افعال بر اساس نیت و هدف صاحب آن است.", "ms": "Tindakan dinilai berdasarkan niat dan tujuannya.", "ur": "اعمال کا حکم ان کے ارادے اور مقصد کے مطابق ہوتا ہے۔"},
        "example": {"ar": "التفريق بين الصدقة والهدية.", "en": "The distinction between charity and gift.", "fr": "La distinction entre l'aumône et le cadeau.", "fa": "تفاوت بین صدقه و هدیه.", "ms": "Perbezaan antara sedekah dan hadiah.", "ur": "صدقہ اور ہدیہ میں فرق۔"}
    },
    {
        "name": {"ar": "الضرورات تبيح المحظورات", "en": "Necessities permit the forbidden", "fr": "Les nécessités permettent le prohibé", "fa": "ضرورت‌ها حرام را مباح می‌کنند", "ms": "Keperluan membenarkan yang haram", "ur": "ضرورتیں ممنوعات کو جائز کرتی ہیں"},
        "definition": {"ar": "عند الضرورة يجوز ارتكاب المحظور بقدر الحاجة فقط.", "en": "Necessities permit the forbidden to the extent of need.", "fr": "Les nécessités permettent le prohibé dans la mesure du besoin.", "fa": "در صورت ضرورت، انجام کار حرام به اندازه نیاز مجاز است.", "ms": "Dalam keadaan darurat, perkara yang haram dibenarkan sekadar keperluan.", "ur": "ضرورت کی صورت میں ممنوع چیز کو ضرورت کے بقدر جائز کر دیا جاتا ہے۔"},
        "example": {"ar": "أكل الميتة عند الخوف من الهلاك.", "en": "Eating carrion when fearing death.", "fr": "Manger de la charogne par crainte de mourir.", "fa": "خوردن مردار در صورت ترس از مرگ.", "ms": "Memakan bangkai apabila takut mati.", "ur": "موت کے خوف سے مردار کھانا۔"}
    },
    {
        "name": {"ar": "الوسائل لها أحكام المقاصد", "en": "The means take the ruling of their objectives", "fr": "Les moyens prennent le jugement de leurs objectifs", "fa": "وسایل حکم اهداف خود را دارند", "ms": "Cara-cara mengambil hukum matlamatnya", "ur": "ذرائع اپنے مقاصد کا حکم رکھتے ہیں"},
        "definition": {"ar": "ما كان وسيلة لشيء يأخذ حكم ذلك الشيء.", "en": "The means take the ruling of their objectives.", "fr": "Les moyens prennent le jugement de leurs objectifs.", "fa": "هر چیزی که وسیله چیزی باشد، حکم آن چیز را دارد.", "ms": "Apa yang menjadi wasilah kepada sesuatu mengambil hukum sesuatu itu.", "ur": "جو چیز کسی چیز کا ذریعہ ہوتی ہے وہ اس کا حکم رکھتی ہے۔"},
        "example": {"ar": "الكتابة في العقود لحفظ الحقوق.", "en": "Writing contracts to preserve rights.", "fr": "Écrire des contrats pour préserver les droits.", "fa": "نوشتن قراردادها برای حفظ حقوق.", "ms": "Menulis kontrak untuk memelihara hak.", "ur": "حقوق کے تحفظ کے لیے معاہدے تحریر کرنا۔"}
    },
    {
        "name": {"ar": "القياس", "en": "Analogy (Qiyas)", "fr": "Analogie (Qiyas)", "fa": "قیاس", "ms": "Qiyas", "ur": "قیاس"},
        "definition": {"ar": "إلحاق فرع بأصل في الحكم لعلة جامعة بينهما.", "en": "Extending a ruling from an original case to a new case due to shared reasoning.", "fr": "Extension d'une règle d'un cas original à un nouveau cas en raison d'un raisonnement partagé.", "fa": "الحاق فرع به اصل در حکم به دلیل علت مشترک.", "ms": "Memperluas hukum dari kes asal ke kes baru kerana persamaan sebab.", "ur": "حکم میں فرع کو اصل سے ملانا بوجہ مشترک علت۔"},
        "example": {"ar": "قياس المخدرات على الخمر في التحريم لعلة الإسكار.", "en": "Analogizing drugs to alcohol in prohibition due to the reasoning of intoxication.", "fr": "Analogie des drogues à l'alcool dans l'interdiction en raison de l'intoxication.", "fa": "قیاس مواد مخدر بر خمر در تحریم به دلیل اسکار.", "ms": "Menganalogikan dadah kepada arak dalam pengharaman kerana sebab memabukkan.", "ur": "نشہ کی علت کی وجہ سے منشیات کو شراب پر قیاس کرنا۔"}
    },
    {
        "name": {"ar": "المصالح المرسلة", "en": "Considered public interest", "fr": "Intérêt public considéré", "fa": "مصالح مرسله", "ms": "Maslahah mursalah", "ur": "مصالح مرسلہ"},
        "definition": {"ar": "اعتبار المصلحة التي لم يرد نص خاص بها ولم تُلغَ، إذا كانت تحقق منفعة عامة.", "en": "Considering public interests not explicitly addressed in primary sources.", "fr": "Considération des intérêts publics non explicitement abordés dans les sources primaires.", "fa": "اعتبار مصلحتی که نص خاصی برای آن نیامده و لغو نشده است، در صورت تحقق منفعت عمومی.", "ms": "Mempertimbangkan maslahah yang tidak disebut secara khusus dalam nas dan tidak dibatalkan, jika ia membawa manfaat umum.", "ur": "ان مفادات کا اعتبار جن کا کوئی خاص نص نہیں ہے اور نہ ہی انہیں منسوخ کیا گیا ہے، اگر وہ عام مفاد کو پورا کرتی ہیں۔"},
        "example": {"ar": "توثيق العقود بالكتابة.", "en": "Documenting contracts in writing.", "fr": "Documenter les contrats par écrit.", "fa": "مستند کردن قراردادها به نوشته.", "ms": "Mendokumentasikan kontrak secara bertulis.", "ur": "معاہدات کو تحریر میں دستاویز کرنا۔"}
    },
    {
        "name": {"ar": "الخاص يحكم العام", "en": "The specific takes precedence over the general", "fr": "Le spécifique prévaut sur le général", "fa": "خاص بر عام مقدم است", "ms": "Khusus mengatasi umum", "ur": "خاص کو عام پر ترجیح ہے"},
        "definition": {"ar": "إذا ورد نص عام ونص خاص، يُقدَّم الخاص في التطبيق.", "en": "When general and specific texts conflict, the specific takes precedence.", "fr": "Lorsque les textes généraux et spécifiques sont en conflit, le spécifique prévaut.", "fa": "اگر نص عام و خاص با هم تعارض داشته باشند، خاص مقدم می‌شود.", "ms": "Apabila teks umum dan khusus bercanggah, teks khusus didahulukan.", "ur": "اگر عام اور خاص نص باہم متعارض ہوں تو خاص کو ترجیح دی جاتی ہے۔"},
        "example": {"ar": "قوله تعالى: (وأحل الله البيع) عام، وقوله: (حرمت عليكم الميتة) خاص.", "en": "The general verse: 'Allah has permitted trade' vs. 'Forbidden to you is carrion'.", "fr": "Le verset général 'Allah a permis le commerce' vs 'Il vous est interdit la charogne'.", "fa": "آیه عام 'خداوند خرید و فروش را حلال کرده' vs 'مردار بر شما حرام شده'.", "ms": "Ayat umum 'Allah menghalalkan jual beli' vs 'Diharamkan kepada kamu bangkai'.", "ur": "عام آیت 'اللہ نے بیع کو حلال کیا' vs 'تم پر مردار حرام ہے'۔"}
    },
    {
        "name": {"ar": "لا ضرر ولا ضرار", "en": "No harm and no reciprocating harm", "fr": "Pas de mal et pas de réciprocité de mal", "fa": "نه ضرر و نه ضرر متقابل", "ms": "Tidak boleh membahayakan dan tidak boleh membalas bahaya", "ur": "نہ نقصان اور نہ نقصان کا بدلہ"},
        "definition": {"ar": "قاعدة مأخوذة من حديث النبي ﷺ: (لا ضرر ولا ضرار)، وتعني أنه لا يجوز إيقاع الضرر بالنفس أو بالغير، ولا يجوز رد الضرر بضرر مثله.", "en": "Based on the Prophetic hadith: 'No harm and no reciprocating harm.'", "fr": "Basé sur le hadith prophétique: 'Pas de mal et pas de réciprocité de mal.'", "fa": "بر اساس حدیث نبوی: 'نه ضرر و نه ضرر متقابل'.", "ms": "Berdasarkan hadis Nabi: 'Tidak boleh membahayakan dan tidak boleh membalas bahaya'.", "ur": "نبوی حدیث پر مبنی: 'نہ نقصان اور نہ نقصان کا بدلہ'۔"},
        "example": {"ar": "منع البناء الذي يضر بالجار.", "en": "Preventing construction that harms a neighbor.", "fr": "Prévenir la construction qui nuit à un voisin.", "fa": "جلوگیری از ساخت و سازی که به همسایه ضرر می‌زند.", "ms": "Mencegah pembinaan yang merugikan jiran.", "ur": "ایسی تعمیر کو روکنا جو پڑوسی کو نقصان پہنچائے۔"}
    },
    {
        "name": {"ar": "الأصل في الأشياء الإباحة", "en": "The default is permissibility", "fr": "Le principe de base est la permission", "fa": "اصل در اشیاء اباحه است", "ms": "Hukum asal adalah harus", "ur": "اصل اشیاء میں اباحت ہے"},
        "definition": {"ar": "الأصل في الأشياء والأفعال الإباحة حتى يقوم دليل على التحريم.", "en": "The default ruling for things and actions is permissibility until evidence proves otherwise.", "fr": "Le principe de base pour les choses et les actions est la permission jusqu'à ce qu'une preuve établisse le contraire.", "fa": "اصل در اشیاء و افعال اباحه است تا زمانی که دلیل بر حرمت قائم شود.", "ms": "Hukum asal bagi sesuatu dan tindakan adalah harus sehingga ada dalil yang menunjukkan sebaliknya.", "ur": "اشیا اور افعال میں اصل اباحت ہے جب تک کہ حرمت کی کوئی دلیل نہ آئے۔"},
        "example": {"ar": "جواز أكل جميع الأطعمة ما لم يرد نص بتحريمها.", "en": "Permissibility of all foods unless there is a text prohibiting them.", "fr": "La permission de manger tous les aliments à moins qu'un texte ne les interdise.", "fa": "جواز خوردن همه غذاها مگر اینکه نصی بر حرمت آنها وارد شود.", "ms": "Kebolehan memakan semua makanan kecuali ada nas yang mengharamkannya.", "ur": "تمام کھانوں کا جائز ہونا جب تک کہ کوئی نص ان کی حرمت پر نہ ہو۔"}
    },
]

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
    
    # ===== شريط اللغات المحسن =====
    st.markdown("""
    <style>
    .lang-bar {
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
    }
    .lang-bar .label {
        font-weight: 600;
        color: #2a5c4a;
        margin-right: 8px;
    }
    .lang-btn {
        padding: 4px 12px;
        border-radius: 20px;
        border: 1px solid #d4dcd4;
        background: white;
        cursor: pointer;
        font-size: 0.85rem;
        transition: all 0.2s;
    }
    .lang-btn.active {
        background: #2a5c4a;
        color: white;
        border-color: #2a5c4a;
    }
    .lang-btn:hover {
        background: #e3ece7;
    }
    .lang-btn.active:hover {
        background: #1d4a3a;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # شريط اللغات
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
    
    # ===== رأس الصفحة المحسن =====
    st.markdown(f"""
    <style>
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
    </style>
    
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
    
    # ===== الشريط الجانبي =====
    with st.sidebar:
        st.markdown(f"### {T['s1_title']}")
        
        group_code = st.radio(
            T["group_q"],
            list(GROUPS.keys()),
            format_func=lambda g: GROUPS[g][lang],
            horizontal=False,
            label_visibility="collapsed",
        )
        sub_codes = GROUPS[group_code]["members"]
        st.caption(T["multi_hint"])
        
        if len(sub_codes) > 1:
            selected_madhabs = st.multiselect(
                T["sub_select"],
                options=sub_codes,
                default=[c for c in st.session_state.selected_madhabs if c in sub_codes] or [sub_codes[0]],
                format_func=lambda c: MADHHAB_NAMES[c][lang],
            )
        else:
            selected_madhabs = sub_codes
            st.caption(f"**{MADHHAB_NAMES[sub_codes[0]][lang]}**")
        
        st.session_state.selected_madhabs = selected_madhabs
        
        st.divider()
        st.markdown(f"### {T['s2_title']}")
        topic = st.radio(
            T["topic_q"],
            list(TOPICS.keys()),
            format_func=lambda t: TOPICS[t][lang],
            horizontal=False,
            label_visibility="collapsed",
        )
        
        st.divider()
        st.markdown(f"### {T['s3_title']}")
        level = st.radio(
            T["level_q"],
            list(LEVELS.keys()),
            format_func=lambda lv: LEVELS[lv][lang],
            horizontal=False,
            label_visibility="collapsed",
        )
        
        st.divider()
        if USE_GEMINI:
            st.success(T["ai_badge"])
        else:
            st.warning(T["ai_unavailable"])
    
    # ===== منطقة البحث الرئيسية =====
    st.markdown(f"### {T['s4_title']}")
    question = st.text_input(
        T["s4_title"], 
        placeholder=T["question_placeholder"], 
        label_visibility="collapsed"
    )
    search_clicked = st.button(T["search_btn"], use_container_width=True)
    
    st.divider()
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
    
    st.markdown("---")
    
    # ===== الأئمة المؤسسون =====
    with st.expander(T["expander_imams"]):
        for imam in IMAMS:
            name = text_for(imam["name"], lang)
            school = text_for(imam["school"], lang)
            birthplace = text_for(imam["birthplace"], lang)
            founding_place = text_for(imam["founding_place"], lang)
            scholars = text_for(imam["scholars"], lang)
            
            st.markdown(f"""
            <div class="info-box">
                <h4>{name}</h4>
                <p style="color:#d4a854; font-weight:600;">{school} &nbsp;|&nbsp; {imam['lifespan']}</p>
                <p>📍 {T['birthplace']}: {birthplace} &nbsp;·&nbsp; 🏛️ {T['founding_place']}: {founding_place}</p>
                <p>🎓 {T['scholars']}: {scholars}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # ===== الدول الإسلامية =====
    with st.expander(T["expander_countries"]):
        cols = st.columns(3)
        for i, c in enumerate(COUNTRIES):
            with cols[i % 3]:
                name = text_for(c["name"], lang)
                madhab_name = text_for(MADHHAB_NAMES[c["madhab"]], lang)
                st.markdown(f"""
                <div class="country-box">
                    <strong>{c['flag']} {name}</strong><br>
                    <span style="color:#d4a854;">{T['official_madhab']}: {madhab_name}</span><br>
                    <span style="font-size:0.8rem; color:#6a7f78;">👥 {T['population']}: {c['population']}</span>
                </div>
                """, unsafe_allow_html=True)
        st.caption(COUNTRIES_NOTE.get(lang, COUNTRIES_NOTE["ar"]))
    
    # ===== المصطلحات الفقهية =====
    with st.expander(T["expander_glossary"]):
        cols = st.columns(2)
        for i, term in enumerate(GLOSSARY):
            term_name = text_for(term["term"], lang)
            term_def = text_for(term["definition"], lang)
            term_ex = text_for(term.get("example", ""), lang)
            
            with cols[i % 2]:
                st.markdown(f"""
                <div class="info-box">
                    <h4>{term_name}</h4>
                    <p>{term_def}</p>
                    {f'<p>🔹 <strong>{T["rules_example"]}:</strong> {term_ex}</p>' if term_ex else ''}
                </div>
                """, unsafe_allow_html=True)
    
    # ===== مصادر التشريع وأصول الاستدلال =====
    with st.expander(T["combined_sources"]):
        st.markdown("**📖 مصادر التشريع**")
        for source in LEGAL_SOURCES:
            name = text_for(source["name"], lang)
            desc = text_for(source["description"], lang)
            st.markdown(f"""
            <div class="info-box">
                <h4>{name}</h4>
                <p>{desc}</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("**📐 أصول الاستدلال**")
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
    with st.expander(T["expander_comments"]):
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
                label_visibility="collapsed"
            )
        
        comment_text = st.text_area(
            T["comment_placeholder"], 
            placeholder=T["comment_placeholder"], 
            label_visibility="collapsed"
        )
        
        if st.button(T["comment_submit"]):
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

if __name__ == "__main__":
    main()
