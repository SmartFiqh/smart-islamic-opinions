# ui/language_bar.py
import streamlit as st
from utils.constants import LANGUAGES

def render_language_bar():
    """عرض شريط اللغات"""
    
    current_lang = st.session_state.get("lang", "ar")
    
    cols = st.columns([1] + [1] * len(LANGUAGES))
    
    with cols[0]:
        st.markdown("🌐 **اللغة**")
    
    for i, (code, data) in enumerate(LANGUAGES.items()):
        with cols[i + 1]:
            if st.button(
                f"{data['flag']} {data['name']}",
                key=f"lang_{code}",
                type="primary" if code == current_lang else "secondary"
            ):
                st.session_state.lang = code
                st.rerun()
    
    return st.session_state.lang
