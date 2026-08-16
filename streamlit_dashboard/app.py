import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

st.set_page_config(page_title="لوحة تحكم الجامع الذكي", page_icon="🕌", layout="wide")

# تهيئة Firebase
try:
    if not firebase_admin._apps:
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    st.success("✅ متصل بـ Firebase")
except:
    st.warning("⚠️ وضع المحاكاة")

st.markdown("# 🕌 لوحة تحكم الجامع الذكي")

col1, col2, col3, col4 = st.columns(4)
col1.metric("📚 المسائل", "5")
col2.metric("🕌 المذاهب", "9")
col3.metric("👁️ مشاهدات", "5,470")
col4.metric("⭐ التقييم", "4.7")

st.subheader("📊 توزيع المسائل")
st.bar_chart(pd.DataFrame({"القيمة": [1250, 890, 670, 2100, 560]}, index=["صلاة الجماعة", "زكاة البنك", "عرفة", "فوائد بنكية", "النقاب"]))
