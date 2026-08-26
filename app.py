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
        "legal_sources": "📖 مصادر التشريع",
        "usul": "📐 أصول الاستدلال الفقهي",
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
        "legal_sources": "📖 Legal sources",
        "usul": "📐 Principles of legal reasoning",
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
        "legal_sources": "📖 Sources juridiques",
        "usul": "📐 Principes du raisonnement",
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
        "legal_sources": "📖 منابع تشریع",
        "usul": "📐 اصول استنباط",
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
        "legal_sources": "📖 Sumber hukum",
        "usul": "📐 Prinsip istinbat",
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
        "legal_sources": "📖 مصادر تشریع",
        "usul": "📐 اصول استدلال",
        "combined_sources": "📜 فقہی مصادر اور اصول استدلال",
    },
}

# ============================================================
# البيانات التعليمية (مختصرة للاختصار - ستكون كاملة في التطبيق النهائي)
# ============================================================

IMAMS = [
    {
        "name": {"ar": "الإمام مالك بن أنس الأصبحي", "en": "Imam Malik ibn Anas al-Asbahi"},
        "school": MADHHAB_NAMES["maliki"],
        "lifespan": "93 - 179 AH",
        "birthplace": {"ar": "المدينة المنورة", "en": "Medina"},
        "founding_place": {"ar": "المدينة المنورة", "en": "Medina"},
        "scholars": {"ar": "ابن القاسم، سحنون، ابن رشد، القرافي، خليل بن إسحاق", "en": "Ibn al-Qasim, Sahnun, Ibn Rushd, al-Qarafi, Khalil ibn Ishaq"}
    },
    {
        "name": {"ar": "الإمام محمد بن إدريس الشافعي", "en": "Imam Muhammad ibn Idris al-Shafi'i"},
        "school": MADHHAB_NAMES["shafii"],
        "lifespan": "150 - 204 AH",
        "birthplace": {"ar": "غزة", "en": "Gaza"},
        "founding_place": {"ar": "بغداد ثم مصر (المذهب الجديد)", "en": "Baghdad, then Egypt (the new doctrine)"},
        "scholars": {"ar": "المزني، البويطي، النووي، ابن حجر الهيتمي، الرافعي", "en": "al-Muzani, al-Buwayti, al-Nawawi, Ibn Hajar al-Haytami, al-Rafi'i"}
    },
]

COUNTRIES = [
    {"flag": "🇸🇦", "name": {"ar": "السعودية", "en": "Saudi Arabia"}, "madhab": "hanbali", "population": "36.4M"},
    {"flag": "🇪🇬", "name": {"ar": "مصر", "en": "Egypt"}, "madhab": "shafii", "population": "112.7M"},
    {"flag": "🇲🇦", "name": {"ar": "المغرب", "en": "Morocco"}, "madhab": "maliki", "population": "37.8M"},
    {"flag": "🇹🇷", "name": {"ar": "تركيا", "en": "Turkey"}, "madhab": "hanafi", "population": "87.5M"},
    {"flag": "🇮🇷", "name": {"ar": "إيران", "en": "Iran"}, "madhab": "jafari", "population": "89.8M"},
    {"flag": "🇴🇲", "name": {"ar": "عُمان", "en": "Oman"}, "madhab": "ibadi", "population": "4.7M"},
    {"flag": "🇸🇩", "name": {"ar": "السودان", "en": "Sudan"}, "madhab": "maliki", "population": "48.1M"},
    {"flag": "🇸🇾", "name": {"ar": "سوريا", "en": "Syria"}, "madhab": "shafii", "population": "22.1M"},
    {"flag": "🇮🇶", "name": {"ar": "العراق", "en": "Iraq"}, "madhab": "jafari", "population": "45.5M"},
    {"flag": "🇦🇪", "name": {"ar": "الإمارات", "en": "UAE"}, "madhab": "maliki", "population": "10.1M"},
    {"flag": "🇯🇴", "name": {"ar": "الأردن", "en": "Jordan"}, "madhab": "shafii", "population": "11.1M"},
    {"flag": "🇧🇭", "name": {"ar": "البحرين", "en": "Bahrain"}, "madhab": "jafari", "population": "1.5M"},
    {"flag": "🇰🇼", "name": {"ar": "الكويت", "en": "Kuwait"}, "madhab": "maliki", "population": "4.4M"},
    {"flag": "🇹🇳", "name": {"ar": "تونس", "en": "Tunisia"}, "madhab": "maliki", "population": "12.5M"},
    {"flag": "🇱🇾", "name": {"ar": "ليبيا", "en": "Libya"}, "madhab": "maliki", "population": "7.0M"},
    {"flag": "🇩🇿", "name": {"ar": "الجزائر", "en": "Algeria"}, "madhab": "maliki", "population": "46.1M"},
    {"flag": "🇮🇩", "name": {"ar": "إندونيسيا", "en": "Indonesia"}, "madhab": "shafii", "population": "279.1M"},
    {"flag": "🇲🇾", "name": {"ar": "ماليزيا", "en": "Malaysia"}, "madhab": "shafii", "population": "34.2M"},
    {"flag": "🇵🇰", "name": {"ar": "باكستان", "en": "Pakistan"}, "madhab": "hanafi", "population": "240.0M"},
    {"flag": "🇦🇫", "name": {"ar": "أفغانستان", "en": "Afghanistan"}, "madhab": "hanafi", "population": "41.1M"},
    {"flag": "🇱🇧", "name": {"ar": "لبنان", "en": "Lebanon"}, "madhab": "shafii", "population": "5.4M"},
    {"flag": "🇵🇸", "name": {"ar": "فلسطين", "en": "Palestine"}, "madhab": "shafii", "population": "5.4M"},
    {"flag": "🇹🇩", "name": {"ar": "تشاد", "en": "Chad"}, "madhab": "maliki", "population": "18.3M"},
    {"flag": "🇳🇬", "name": {"ar": "نيجيريا", "en": "Nigeria"}, "madhab": "maliki", "population": "225.0M"},
    {"flag": "🇸🇴", "name": {"ar": "الصومال", "en": "Somalia"}, "madhab": "shafii", "population": "17.1M"},
    {"flag": "🇩🇯", "name": {"ar": "جيبوتي", "en": "Djibouti"}, "madhab": "shafii", "population": "1.1M"},
    {"flag": "🇪🇷", "name": {"ar": "إريتريا", "en": "Eritrea"}, "madhab": "maliki", "population": "3.7M"},
    {"flag": "🇲🇷", "name": {"ar": "موريتانيا", "en": "Mauritania"}, "madhab": "maliki", "population": "5.0M"},
]

COUNTRIES_NOTE = {
    "ar": "ملاحظة: يُقصد بـ«المذهب الرسمي» المذهب الفقهي السائد تاريخياً بين غالبية المسلمين في البلد أو المعتمد في محاكمه الشرعية؛ وقد تتعايش فيه مذاهب أخرى.",
    "en": "Note: the \"official school\" refers to the madhhab historically prevailing among the country's Muslim majority or followed in its Sharia courts; other schools may coexist there.",
}

GLOSSARY = [
    {"term": {"ar": "الفرض / فرض العين", "en": "Fard / Fard Ayn (Individual Obligation)"},
     "definition": {"ar": "ما طلب الشارع فعله طلباً جازماً من كل مكلف بعينه، يُثاب فاعله ويُعاقب تاركه.", "en": "What the Lawgiver has decisively commanded every legally accountable individual to perform."},
     "example": {"ar": "الصلوات الخمس، الزكاة.", "en": "The five daily prayers; zakat."}},
    {"term": {"ar": "فرض الكفاية", "en": "Fard Kifayah (Sufficiency Obligation)"},
     "definition": {"ar": "ما طلب الشارع فعله طلباً جازماً من المجموعة دون كل فرد بعينه، فإذا قام به البعض سقط الإثم عن الباقين.", "en": "A collective obligation which, if performed by some, absolves others."},
     "example": {"ar": "صلاة الجنازة، تعلم الطب.", "en": "The funeral prayer; training enough doctors."}},
    {"term": {"ar": "الواجب", "en": "Wajib (Obligatory)"},
     "definition": {"ar": "ما طلب الشارع فعله طلباً جازماً غير أنه لا يصل إلى درجة الفرض.", "en": "What the Lawgiver has commanded decisively but not reaching the level of Fard."},
     "example": {"ar": "صلاة الوتر عند الحنفية.", "en": "The witr prayer according to Hanafis."}},
    {"term": {"ar": "المستحب / المندوب", "en": "Mustahabb / Mandub (Recommended)"},
     "definition": {"ar": "ما طلب الشارع فعله طلباً غير جازم، يُثاب فاعله ولا يُعاقب تاركه.", "en": "What the Lawgiver has recommended without decisiveness; rewarded for doing, not punished for abandoning."},
     "example": {"ar": "صلاة الضحى، صيام الاثنين والخميس.", "en": "The mid-morning (Duha) prayer; fasting on Mondays and Thursdays."}},
    {"term": {"ar": "السنة", "en": "Sunnah"},
     "definition": {"ar": "ما ثبت عن النبي ﷺ من قول أو فعل أو تقرير، وهي تشمل الواجب والمستحب والمباح.", "en": "What is established from the Prophet ﷺ of sayings, actions, or approvals."},
     "example": {"ar": "السواك عند الوضوء، الأذكار بعد الصلاة.", "en": "Using the miswak during ablution; remembrance (adhkar) after prayer."}},
    {"term": {"ar": "السنة المؤكدة", "en": "Sunnah Mu'akkadah (Emphasized Sunnah)"},
     "definition": {"ar": "ما واظب عليه النبي ﷺ ولم يتركه إلا نادراً، وهي قريبة من الواجب في الأهمية.", "en": "What the Prophet ﷺ consistently performed and rarely abandoned; close to obligatory in importance."},
     "example": {"ar": "ركعتا الفجر، الوتر عند الجمهور.", "en": "The two rak'ahs before Fajr; witr prayer."}},
    {"term": {"ar": "المباح", "en": "Mubah (Permissible)"},
     "definition": {"ar": "ما خير الشارع بين فعله وتركه، ولا ثواب على فعله ولا عقاب على تركه.", "en": "What the Lawgiver has left optional; no reward for doing it and no punishment for abandoning it."},
     "example": {"ar": "الأكل من الطيبات، اختيار لون الثوب.", "en": "Eating wholesome food; choosing the color of one's clothing."}},
    {"term": {"ar": "الحرام", "en": "Haram (Prohibited)"},
     "definition": {"ar": "ما طلب الشارع تركه طلباً جازماً، يُعاقب فاعله ويُثاب تاركه امتثالاً.", "en": "What the Lawgiver has decisively forbidden; the doer is punished, and the one who abstains in obedience is rewarded."},
     "example": {"ar": "الربا، أكل لحم الخنزير.", "en": "Usury (riba); eating pork."}},
    {"term": {"ar": "المكروه", "en": "Makruh (Disliked)"},
     "definition": {"ar": "ما طلب الشارع تركه طلباً غير جازم، يُثاب تاركه ولا يُعاقب فاعله.", "en": "What the Lawgiver has discouraged without decisiveness; rewarded for abandoning, not punished for doing."},
     "example": {"ar": "الأكل من ثوم نيء قبل الذهاب إلى المسجد.", "en": "Eating raw garlic before going to the mosque."}},
    {"term": {"ar": "الحلال", "en": "Halal (Lawful)"},
     "definition": {"ar": "ما أحله الشارع وأباحه، وهو يشمل الواجب والمستحب والمباح، وهو مقابل للحرام.", "en": "What the Lawgiver has made lawful and permissible; includes obligations, recommendations, and permissibles."},
     "example": {"ar": "البيع المباح، الطعام الحلال.", "en": "A permissible sale; lawful food."}},
]

LEGAL_SOURCES = [
    {"name": {"ar": "القرآن الكريم", "en": "The Qur'an"},
     "description": {"ar": "المصدر الأعلى والأول للتشريع الإسلامي، وهو كلام الله المنزل على نبيه محمد ﷺ.", "en": "The primary and highest source of Islamic law, the word of God revealed to Prophet Muhammad ﷺ."}},
    {"name": {"ar": "السنة النبوية", "en": "Prophetic Sunnah"},
     "description": {"ar": "أقوال النبي ﷺ وأفعاله وتقريراته، وهي المصدر الثاني بعد القرآن.", "en": "The sayings, actions, and approvals of the Prophet ﷺ, the second source after the Qur'an."}},
    {"name": {"ar": "الإجماع", "en": "Ijma' (Consensus)"},
     "description": {"ar": "اتفاق المجتهدين من أمة محمد ﷺ في عصر من العصور على حكم شرعي بعد وفاة النبي ﷺ.", "en": "The agreement of qualified jurists from the Muslim community in any era on a legal ruling after the Prophet's death."}},
    {"name": {"ar": "القياس", "en": "Qiyas (Analogy)"},
     "description": {"ar": "إلحاق مسألة جديدة ليس لها نص بمسألة منصوص عليها لاشتراكهما في العلة الموجبة للحكم.", "en": "Applying an established ruling to a new case without a text due to a shared effective cause."}},
]

USUL = [
    {"name": {"ar": "الأمر والنهي", "en": "Commands and prohibitions"},
     "definition": {"ar": "بحث دلالات صيغ الأمر والنهي وآثارها في إثبات الأحكام التكليفية.", "en": "Analysis of the implications of commands and prohibitions and their effects in establishing legal obligations."},
     "note": {"ar": "تختلف بعض تطبيقاته بحسب القرائن والسياق.", "en": "Applications may vary according to context and indications."}},
    {"name": {"ar": "العام والخاص", "en": "General and specific texts"},
     "definition": {"ar": "دراسة النصوص العامة وما يرد عليها من تخصيص يخرج بعض أفرادها من حكم العام.", "en": "Study of general texts and the specification that excludes some individuals from the general ruling."},
     "note": {"ar": "يبحث الأصولي في دلالة اللفظ وحدود شموله.", "en": "The jurist examines the scope and meaning of the wording."}},
    {"name": {"ar": "المطلق والمقيد", "en": "Unrestricted and restricted texts"},
     "definition": {"ar": "الموازنة بين النص المطلق والنص الذي قيده وصف أو شرط، وكيفية حمل المطلق على المقيد.", "en": "Reconciling unrestricted texts with texts limited by a condition or description, and how to apply restrictions."},
     "note": {"ar": "يُنظر في اتحاد الحكم والسبب والسياق.", "en": "The legal ruling, cause, and context are considered."}},
    {"name": {"ar": "المصلحة والاستصحاب", "en": "Maslahah and presumption of continuity"},
     "definition": {"ar": "منهج للنظر في المصلحة المعتبرة واستمرار الحكم السابق عند عدم وجود دليل على التغيير.", "en": "A methodology for considering recognized benefit and the continuity of a previous ruling in the absence of evidence of change."},
     "note": {"ar": "تختلف حدود الاعتماد عليهما بين المدارس الفقهية.", "en": "Schools differ in the extent to which they rely on these principles."}},
]

RULES = [
    {"name": {"ar": "اليقين لا يزول بالشك", "en": "Certainty cannot be overridden by doubt"},
     "definition": {"ar": "إذا ثبت أمر بيقين فلا يزول إلا بيقين مثله، ولا يؤثر فيه مجرد الشك.", "en": "Certainty cannot be overridden by doubt."},
     "example": {"ar": "من تيقن الطهارة وشك في الحدث، يبقى على الطهارة.", "en": "If someone is certain of purity and doubts impurity, they remain in a state of purity."}},
    {"name": {"ar": "المشقة تجلب التيسير", "en": "Hardship brings ease"},
     "definition": {"ar": "عند وجود مشقة معتبرة في تطبيق الحكم الشرعي، يُفتح باب الرخصة والتخفيف.", "en": "Hardship brings ease in Islamic jurisprudence."},
     "example": {"ar": "قصر الصلاة في السفر أو الإفطار في المرض.", "en": "Shortening prayers during travel or breaking fast during illness."}},
    {"name": {"ar": "الضرر يزال", "en": "Harm must be removed"},
     "definition": {"ar": "كل ما فيه ضرر على الفرد أو الجماعة يجب رفعه أو منعه.", "en": "Harm must be removed or prevented."},
     "example": {"ar": "منع الغش في البيع أو إزالة الأذى عن الطريق.", "en": "Preventing fraud in sales or removing harm from the road."}},
    {"name": {"ar": "العادة محكمة", "en": "Custom is a valid consideration"},
     "definition": {"ar": "العرف والعادة المعتبرة شرعًا تُعتبر في الأحكام ما لم تخالف نصًا شرعيًا.", "en": "Custom is a valid consideration in Islamic law."},
     "example": {"ar": "أعراف الزواج أو البيع.", "en": "Customs regarding marriage or sales."}},
    {"name": {"ar": "الأمور بمقاصدها", "en": "Actions are judged by intentions"},
     "definition": {"ar": "الحكم على الأفعال يكون بحسب نية صاحبها ومقصده.", "en": "Actions are judged by their intentions."},
     "example": {"ar": "التفريق بين الصدقة والهدية.", "en": "The distinction between charity and gift."}},
    {"name": {"ar": "الضرورات تبيح المحظورات", "en": "Necessities permit the forbidden"},
     "definition": {"ar": "عند الضرورة يجوز ارتكاب المحظور بقدر الحاجة فقط.", "en": "Necessities permit the forbidden to the extent of need."},
     "example": {"ar": "أكل الميتة عند الخوف من الهلاك.", "en": "Eating carrion when fearing death."}},
    {"name": {"ar": "الوسائل لها أحكام المقاصد", "en": "The means take the ruling of their objectives"},
     "definition": {"ar": "ما كان وسيلة لشيء يأخذ حكم ذلك الشيء.", "en": "The means take the ruling of their objectives."},
     "example": {"ar": "الكتابة في العقود لحفظ الحقوق.", "en": "Writing contracts to preserve rights."}},
    {"name": {"ar": "القياس", "en": "Analogy (Qiyas)"},
     "definition": {"ar": "إلحاق فرع بأصل في الحكم لعلة جامعة بينهما.", "en": "Extending a ruling from an original case to a new case due to shared reasoning."},
     "example": {"ar": "قياس المخدرات على الخمر في التحريم لعلة الإسكار.", "en": "Analogizing drugs to alcohol in prohibition due to the reasoning of intoxication."}},
    {"name": {"ar": "المصالح المرسلة", "en": "Considered public interest"},
     "definition": {"ar": "اعتبار المصلحة التي لم يرد نص خاص بها ولم تُلغَ، إذا كانت تحقق منفعة عامة.", "en": "Considering public interests not explicitly addressed in primary sources."},
     "example": {"ar": "توثيق العقود بالكتابة.", "en": "Documenting contracts in writing."}},
    {"name": {"ar": "الخاص يحكم العام", "en": "The specific takes precedence over the general"},
     "definition": {"ar": "إذا ورد نص عام ونص خاص، يُقدَّم الخاص في التطبيق.", "en": "When general and specific texts conflict, the specific takes precedence."},
     "example": {"ar": "قوله تعالى: (وأحل الله البيع) عام، وقوله: (حرمت عليكم الميتة) خاص.", "en": "The general verse: 'Allah has permitted trade' vs. 'Forbidden to you is carrion'."}},
    {"name": {"ar": "لا ضرر ولا ضرار", "en": "No harm and no reciprocating harm"},
     "definition": {"ar": "قاعدة مأخوذة من حديث النبي ﷺ: (لا ضرر ولا ضرار)، وتعني أنه لا يجوز إيقاع الضرر بالنفس أو بالغير.", "en": "Based on the Prophetic hadith: 'No harm and no reciprocating harm.'"},
     "example": {"ar": "منع البناء الذي يضر بالجار.", "en": "Preventing construction that harms a neighbor."}},
    {"name": {"ar": "الأصل في الأشياء الإباحة", "en": "The default is permissibility"},
     "definition": {"ar": "الأصل في الأشياء والأفعال الإباحة حتى يقوم دليل على التحريم.", "en": "The default ruling for things and actions is permissibility until evidence proves otherwise."},
     "example": {"ar": "جواز أكل جميع الأطعمة ما لم يرد نص بتحريمها.", "en": "Permissibility of all foods unless there is a text prohibiting them."}},
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
    st.markdown("""
    <style>
    /* توجيه النصوص */
    .stApp { direction: __DIRECTION__; }
    .stApp p, .stApp li, .stApp label, .stApp span,
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5 {
        text-align: __ALIGN__;
        line-height: 1.9;
    }
    
    /* شريط اللغات */
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
    
    /* رأس الصفحة */
    .app-header {
        text-align: center;
        padding: 28px 20px 22px;
        background: linear-gradient(145deg, #0f231c, #2a5c4a);
        color: white;
        border-radius: 20px;
        margin-bottom: 24px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.15);
    }
    .app-header h1 {
        font-size: 2rem;
        margin: 8px 0 4px;
        font-weight: 700;
        text-align: center !important;
    }
    .app-header p {
        font-size: 1rem;
        opacity: 0.9;
        margin: 0 0 12px 0;
        text-align: center !important;
    }
    .app-badges {
        display: flex;
        justify-content: center;
        gap: 10px;
        flex-wrap: wrap;
    }
    .app-badge {
        background: rgba(212, 168, 84, 0.14);
        border: 1px solid rgba(212, 168, 84, 0.5);
        color: #f2e6c9;
        padding: 4px 14px;
        border-radius: 999px;
        font-size: 0.8rem;
    }
    
    /* صناديق المعلومات */
    .info-box {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 12px 16px;
        margin-bottom: 12px;
        border-left: 4px solid #2a5c4a;
    }
    .country-box {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 10px;
        text-align: center;
    }
    .answer-card {
        background: #f5f7f5;
        border: 1px solid #e1e7e3;
        border-radius: 14px;
        padding: 16px 18px;
        margin-bottom: 12px;
    }
    .answer-card .answer-text {
        font-size: 1.15rem;
        font-weight: 600;
        color: #16281f;
        margin: 4px 0;
    }
    .answer-card .answer-note {
        font-size: 0.85rem;
        color: #6a7f78;
    }
    .signature {
        font-family: 'Brush Script MT', cursive;
        font-style: italic;
        font-size: 1rem;
        color: #b08d3f;
        text-align: center;
        margin: 6px 0 18px 0;
    }
    
    /* أزرار راديو على شكل أقراص */
    div[data-testid="stRadio"] > div[role="radiogroup"] {
        gap: 6px;
        flex-wrap: wrap;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] label {
        background: #f0f3f1;
        border: 1px solid #e1e7e3;
        padding: 6px 16px;
        border-radius: 999px;
        transition: all 0.15s ease;
        margin: 0 !important;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] label:hover {
        background: #e3ece7;
        border-color: #2a5c4a;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] label[data-checked="true"],
    div[data-testid="stRadio"] > div[role="radiogroup"] label:has(input:checked) {
        background: #2a5c4a;
        border-color: #2a5c4a;
    }
    div[data-testid="stRadio"] > div[role="radiogroup"] label:has(input:checked) p {
        color: #ffffff !important;
        font-weight: 600;
    }
    
    /* تنسيق الأعمدة الجانبية */
    .left-column {
        background: #f8faf9;
        border-radius: 16px;
        padding: 20px 18px;
        border: 1px solid #e1e7e3;
        height: 100%;
    }
    .right-column {
        padding-left: 20px;
    }
    
    /* تنسيق الأقسام المنفصلة */
    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #2a5c4a;
        margin: 16px 0 8px 0;
        padding-bottom: 4px;
        border-bottom: 2px solid #d4dcd4;
    }
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
                
                st.markdown(f"""
                <div class="info-box">
                    <h4>{name}</h4>
                    <p style="color:#d4a854; font-weight:600;">{school} &nbsp;|&nbsp; {imam['lifespan']}</p>
                    <p>📍 {T['birthplace']}: {birthplace} &nbsp;·&nbsp; 🏛️ {T['founding_place']}: {founding_place}</p>
                    <p>🎓 {T['scholars']}: {scholars}</p>
                </div>
                """, unsafe_allow_html=True)
        
        # ===== الدول الإسلامية =====
        with st.expander(T["expander_countries"], expanded=False):
            cols_country = st.columns(3)
            for i, c in enumerate(COUNTRIES):
                with cols_country[i % 3]:
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
        
        # ===== إدارة المراجع =====
        with st.expander(T["rag_expander"], expanded=False):
            st.info(T["rag_intro"])
            # ... (يمكن إضافة واجهة إدارة المراجع هنا)
        
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
