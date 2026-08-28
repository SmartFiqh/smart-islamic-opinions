# ui/info_sections.py
"""الأقسام التعليمية"""

import streamlit as st
import json
from pathlib import Path
from utils.constants import MADHHAB_NAMES

def load_json_data(filename):
    """تحميل بيانات من ملف JSON"""
    path = Path(__file__).resolve().parent.parent / "data" / filename
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def text_for(value, lang, default=""):
    """استخراج النص حسب اللغة"""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return str(value.get(lang, value.get("ar", default)))
    return default

def render_info_sections(T):
    """عرض الأقسام التعليمية"""
    
    lang = st.session_state.lang
    
    # ===== الأئمة المؤسسون =====
    with st.expander(T["expander_imams"], expanded=False):
        imams = load_json_data("imams.json")
        for imam in imams:
            name = text_for(imam["name"], lang)
            school = text_for(MADHHAB_NAMES[imam["school"]], lang)
            birthplace = text_for(imam["birthplace"], lang)
            founding_place = text_for(imam["founding_place"], lang)
            scholars = text_for(imam["scholars"], lang)
            summary = text_for(imam.get("summary", ""), lang)
            
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
        countries = load_json_data("countries.json")
        cols_country = st.columns(3)
        for i, c in enumerate(countries):
            with cols_country[i % 3]:
                name = text_for(c["name"], lang)
                madhab = text_for(MADHHAB_NAMES[c["madhab"][0] if isinstance(c["madhab"], list) else c["madhab"]], lang) if "madhab" in c else ""
                is_diverse = c.get("diverse", False)
                diverse_mark = " 🌐" if is_diverse else ""
                
                st.markdown(f"""
                <div class="country-box">
                    <strong>{c['flag']} {name}</strong><br>
                    <span style="color:#d4a854;">{T['official_madhab']}: {madhab}{diverse_mark}</span><br>
                    <span style="font-size:0.8rem; color:#6a7f78;">👥 {T['population']}: {c.get('population', '')}</span>
                </div>
                """, unsafe_allow_html=True)
    
    # ===== المصطلحات الفقهية =====
    with st.expander(T["expander_glossary"], expanded=False):
        glossary = load_json_data("glossary.json")
        cols_gloss = st.columns(2)
        for i, term in enumerate(glossary):
            with cols_gloss[i % 2]:
                term_name = text_for(term["term"], lang)
                term_def = text_for(term["definition"], lang)
                term_ex = text_for(term.get("example", ""), lang)
                
                st.markdown(f"""
                <div class="info-box">
                    <h4>{term_name}</h4>
                    <p>{term_def}</p>
                    {f'<p>🔹 <strong>{T["rules_example"]}:</strong> {term_ex}</p>' if term_ex else ''}
                </div>
                """, unsafe_allow_html=True)
    
    # ===== مصادر التشريع =====
    with st.expander(T["legal_sources"], expanded=False):
        sources = load_json_data("legal_sources.json")
        for source in sources:
            name = text_for(source["name"], lang)
            desc = text_for(source["description"], lang)
            st.markdown(f"""
            <div class="info-box">
                <h4>{name}</h4>
                <p>{desc}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # ===== أصول الاستدلال الفقهي =====
    with st.expander(T["usul"], expanded=False):
        usul = load_json_data("usul.json")
        for item in usul:
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
    with st.expander(T["rules_title"], expanded=False):
        rules = load_json_data("rules.json")
        for i, rule in enumerate(rules):
            rule_name = text_for(rule["name"], lang)
            rule_def = text_for(rule["definition"], lang)
            rule_ex = text_for(rule["example"], lang)
            
            if i > 0:
                st.markdown("---")
            
            st.markdown(f"**📌 {rule_name}**")
            st.markdown(f"""
            <div class="info-box">
                <p><strong>{T['rules_definition']}:</strong> {rule_def}</p>
                <p><strong>{T['rules_example']}:</strong> {rule_ex}</p>
            </div>
            """, unsafe_allow_html=True)
