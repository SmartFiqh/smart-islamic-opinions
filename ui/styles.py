# ui/styles.py
"""التنسيقات CSS للتطبيق"""

import streamlit as st

def apply_css():
    """تطبيق التنسيقات CSS"""
    st.markdown("""
    <style>
    /* توجيه النصوص */
    .stApp p, .stApp li, .stApp label, .stApp span,
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5 {
        line-height: 1.9;
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
    </style>
    """, unsafe_allow_html=True)
