# ui/language_bar.py
"""شريط اللغات"""

import streamlit as st
from utils.constants import LANGS, LANG_FLAGS

def render_language_bar():
    """عرض شريط اللغات"""
    
    # تأكد من وجود lang في session_state
    if "lang" not in st.session_state:
        st.session_state.lang = "ar"
    
    lang = st.session_state.lang
    
    cols = st.columns([1] + [1] * len(LANGS))
    
    with cols[0]:
        st.markdown("**🌐 اللغة**")
    
    for i, (name, code) in enumerate(LANGS.items()):
        with cols[i + 1]:
            # استخدام on_click بدلاً من rerun المباشر
            if st.button(
                f"{LANG_FLAGS.get(code, '')} {name}",
                key=f"lang_{code}",
                use_container_width=True,
                type="primary" if code == lang else "secondary",
            ):
                st.session_state.lang = code
                st.rerun()
    
    return lang
