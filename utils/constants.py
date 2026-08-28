# utils/constants.py
"""ثوابت التطبيق - المذاهب، اللغات، الموضوعات"""

# اللغات المدعومة
LANGUAGES = {
    "ar": {"name": "العربية", "flag": "🇸🇦", "direction": "rtl"},
    "en": {"name": "English", "flag": "🇬🇧", "direction": "ltr"},
    "fr": {"name": "Français", "flag": "🇫🇷", "direction": "ltr"},
    "fa": {"name": "فارسی", "flag": "🇮🇷", "direction": "rtl"},
    "ms": {"name": "Melayu", "flag": "🇲🇾", "direction": "ltr"},
    "ur": {"name": "اردو", "flag": "🇵🇰", "direction": "rtl"},
}

# المذاهب الفقهية
MADHHABS = {
    "maliki": {"name_ar": "مالكي", "name_en": "Maliki", "group": "sunni"},
    "shafii": {"name_ar": "شافعي", "name_en": "Shafi'i", "group": "sunni"},
    "hanafi": {"name_ar": "حنفي", "name_en": "Hanafi", "group": "sunni"},
    "hanbali": {"name_ar": "حنبلي", "name_en": "Hanbali", "group": "sunni"},
    "zahiri": {"name_ar": "ظاهري", "name_en": "Zahiri", "group": "sunni"},
    "jafari": {"name_ar": "جعفري", "name_en": "Ja'fari", "group": "shia"},
    "zaidi": {"name_ar": "زيدي", "name_en": "Zaidi", "group": "shia"},
    "ibadi": {"name_ar": "إباضي", "name_en": "Ibadi", "group": "ibadi"},
}

# مجموعات المذاهب
MADHAB_GROUPS = {
    "sunni": ["maliki", "shafii", "hanafi", "hanbali", "zahiri"],
    "shia": ["jafari", "zaidi"],
    "ibadi": ["ibadi"],
}

# الموضوعات الفقهية
TOPICS = {
    "ibadat": {"ar": "العبادات", "en": "Worship"},
    "muamalat": {"ar": "المعاملات", "en": "Transactions"},
    "family": {"ar": "الأسرة", "en": "Family"},
    "other": {"ar": "مواضيع أخرى", "en": "Other Topics"},
}
