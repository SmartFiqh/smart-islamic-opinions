# ui/language_bar.py
"""شريط اللغات"""

import streamlit as st
from utils.constants import LANGS, LANG_FLAGS

def render_language_bar():
    """عرض شريط اللغات"""
    lang = st.session_state.get("lang", "ar")
    
    cols = st.columns([1] + [1] * len(LANGS))
    
    with cols[0]:
        st.markdown("**🌐 اللغة**")
    
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
    
    return lang
