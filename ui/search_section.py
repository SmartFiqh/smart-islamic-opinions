# ui/search_section.py
"""قسم البحث"""

import streamlit as st
from utils.constants import GROUPS, TOPICS, LEVELS, MADHHAB_NAMES

def render_search_section(T, db, ai, search):
    """عرض قسم البحث"""
    
    # الخطوة 1: اختيار المذهب
    st.markdown(f"### {T['s1_title']}")
    
    group_code = st.radio(
        T["group_q"],
        list(GROUPS.keys()),
        format_func=lambda g: GROUPS[g][st.session_state.lang],
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
            default=st.session_state.get("selected_madhabs", [sub_codes[0]]),
            format_func=lambda c: MADHHAB_NAMES[c][st.session_state.lang],
            key="madhab_multiselect",
        )
    else:
        selected_madhabs = sub_codes
        st.caption(f"**{MADHHAB_NAMES[sub_codes[0]][st.session_state.lang]}**")
    
    st.session_state.selected_madhabs = selected_madhabs
    
    st.divider()
    
    # الخطوة 2: اختيار الموضوع
    st.markdown(f"### {T['s2_title']}")
    topic = st.radio(
        T["topic_q"],
        list(TOPICS.keys()),
        format_func=lambda t: TOPICS[t][st.session_state.lang],
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
        format_func=lambda lv: LEVELS[lv][st.session_state.lang],
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
        # سيتم تنفيذ البحث لاحقاً
        st.info("🔍 جاري البحث...")
        st.caption(T["answer_placeholder"])
    elif search_clicked:
        st.info(T["no_question_warning"])
    else:
        st.caption(T["answer_placeholder"])
    
    # حالة الذكاء الاصطناعي
    st.divider()
    if ai.available:
        st.success(T["ai_badge"])
    else:
        st.warning(T["ai_unavailable"])
