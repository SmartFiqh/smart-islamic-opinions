# utils/text_utils.py
"""أدوات معالجة النصوص"""

import re

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
