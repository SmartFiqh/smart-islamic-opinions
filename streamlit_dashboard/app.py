import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import os

# ==================== إعدادات الصفحة ====================
st.set_page_config(
    page_title="لوحة تحكم الجامع الذكي",
    page_icon="🕌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== عنوان الصفحة ====================
st.markdown("""
# 🕌 لوحة تحكم الجامع الذكي لآراء المذاهب الإسلامية
### Smart Compendium of Islamic Madhhab Opinions - Admin Dashboard
""")

# ==================== بيانات وهمية (محاكاة) ====================
# في النسخة الحقيقية، ستجلب هذه البيانات من Firebase أو Supabase

@st.cache_data
def load_data():
    """تحميل البيانات المحاكاة"""
    
    # بيانات المذاهب
    madhhabs = [
        {"id": "hanafi", "name": "الحنفي", "group": "Sunni", "color": "#2E7D32"},
        {"id": "maliki", "name": "المالكي", "group": "Sunni", "color": "#1565C0"},
        {"id": "shafii", "name": "الشافعي", "group": "Sunni", "color": "#F57F17"},
        {"id": "hanbali", "name": "الحنبلي", "group": "Sunni", "color": "#C62828"},
        {"id": "dhahiri", "name": "الظاهري", "group": "Sunni", "color": "#6A1B9A"},
        {"id": "jafari", "name": "الجعفري", "group": "Shia", "color": "#00838F"},
        {"id": "zaidi", "name": "الزيدي", "group": "Shia", "color": "#AD1457"},
        {"id": "ibadi", "name": "الإباضي", "group": "Ibadi", "color": "#E65100"},
        {"id": "other", "name": "آراء أخرى", "group": "Other", "color": "#607D8B"},
    ]
    
    # بيانات المسائل
    issues = [
        {"id": 1, "title": "حكم صلاة الجماعة", "category": "العبادات", "views": 1250, "rating": 4.8},
        {"id": 2, "title": "حكم زكاة المال عبر البنك", "category": "المعاملات", "views": 890, "rating": 4.5},
        {"id": 3, "title": "صيام يوم عرفة للحاج", "category": "العبادات", "views": 670, "rating": 4.7},
        {"id": 4, "title": "حكم الفوائد البنكية", "category": "المعاملات", "views": 2100, "rating": 4.9},
        {"id": 5, "title": "حكم النقاب للمرأة", "category": "الأحوال الشخصية", "views": 560, "rating": 4.2},
    ]
    
    # بيانات التعليقات
    comments = [
        {"issue_id": 1, "user": "باحث", "text": "مفيد جداً", "rating": 5, "date": "2026-08-01"},
        {"issue_id": 2, "user": "طالب علم", "text": "يحتاج توثيق أكثر", "rating": 4, "date": "2026-08-02"},
        {"issue_id": 1, "user": "مختص", "text": "إضافة رائعة للمذهب المالكي", "rating": 5, "date": "2026-08-03"},
    ]
    
    return madhhabs, issues, comments

madhhabs, issues, comments = load_data()

# ==================== الشريط الجانبي ====================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/000000/mosque.png", width=80)
    st.title("🔍 لوحة التحكم")
    
    st.markdown("---")
    
    # اختيار القسم
    section = st.radio(
        "📂 اختر القسم:",
        ["📊 نظرة عامة", "📚 المسائل", "🗣️ التعليقات", "📈 الإحصائيات", "⚙️ الإعدادات"]
    )
    
    st.markdown("---")
    
    # معلومات إضافية
    st.caption(f"🕒 آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    st.caption("📱 تطبيق Flutter متصل ✓")
    st.caption("🤖 Gemini API: غير مفعل")

# ==================== المحتوى حسب القسم ====================

# ---------- القسم 1: نظرة عامة ----------
if section == "📊 نظرة عامة":
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📚 عدد المسائل", len(issues), delta="+2")
    with col2:
        st.metric("🕌 عدد المذاهب", len(madhhabs))
    with col3:
        total_views = sum(i["views"] for i in issues)
        st.metric("👁️ مشاهدات", f"{total_views:,}", delta="+12%")
    with col4:
        avg_rating = sum(i["rating"] for i in issues) / len(issues)
        st.metric("⭐ متوسط التقييم", f"{avg_rating:.2f}")
    
    st.markdown("---")
    
    # رسم بياني: عدد المشاهدات حسب المذهب
    st.subheader("📊 توزيع المشاهدات حسب المذهب")
    
    # إنشاء بيانات وهمية للمشاهدات حسب المذهب
    views_by_madhhab = {m["name"]: 0 for m in madhhabs}
    for issue in issues:
        # توزيع عشوائي للمشاهدات على المذاهب (للمحاكاة)
        import random
        for m in madhhabs:
            views_by_madhhab[m["name"]] += random.randint(10, 100)
    
    fig = px.bar(
        x=list(views_by_madhhab.keys()),
        y=list(views_by_madhhab.values()),
        title="عدد المشاهدات حسب المذهب",
        labels={"x": "المذهب", "y": "عدد المشاهدات"},
        color=list(views_by_madhhab.keys()),
        color_discrete_sequence=[m["color"] for m in madhhabs],
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # رسم بياني: تقييم المسائل
    st.subheader("⭐ تقييم المسائل")
    
    fig2 = px.bar(
        x=[i["title"] for i in issues],
        y=[i["rating"] for i in issues],
        title="تقييم المسائل",
        labels={"x": "المسألة", "y": "التقييم"},
        color=[i["rating"] for i in issues],
        color_continuous_scale="Greens",
        text=[i["rating"] for i in issues],
    )
    fig2.update_traces(textposition="outside")
    st.plotly_chart(fig2, use_container_width=True)

# ---------- القسم 2: المسائل ----------
elif section == "📚 المسائل":
    st.subheader("📚 قائمة المسائل الفقهية")
    
    # جدول المسائل
    df_issues = pd.DataFrame(issues)
    st.dataframe(
        df_issues,
        column_config={
            "id": "الرقم",
            "title": "المسألة",
            "category": "التصنيف",
            "views": "المشاهدات",
            "rating": "التقييم",
        },
        use_container_width=True,
        hide_index=True,
    )
    
    # إضافة مسألة جديدة (محاكاة)
    with st.expander("➕ إضافة مسألة جديدة"):
        col1, col2 = st.columns(2)
        with col1:
            new_title = st.text_input("عنوان المسألة")
            new_category = st.selectbox("التصنيف", ["العبادات", "المعاملات", "الأحوال الشخصية", "أخرى"])
        with col2:
            new_views = st.number_input("المشاهدات الأولية", min_value=0, value=0)
            new_rating = st.slider("التقييم", 0.0, 5.0, 3.0)
        
        if st.button("إضافة المسألة"):
            st.success("✅ تم إضافة المسألة بنجاح (محاكاة)")

# ---------- القسم 3: التعليقات ----------
elif section == "🗣️ التعليقات":
    st.subheader("🗣️ التعليقات والاقتراحات")
    
    df_comments = pd.DataFrame(comments)
    st.dataframe(
        df_comments,
        column_config={
            "issue_id": "رقم المسألة",
            "user": "المستخدم",
            "text": "التعليق",
            "rating": "التقييم",
            "date": "التاريخ",
        },
        use_container_width=True,
        hide_index=True,
    )
    
    # حالة الموافقة على التعليقات
    st.subheader("📋 تعليقات في انتظار المراجعة")
    
    pending_comments = [
        {"user": "طالب علم", "text": "هل يمكن إضافة رأي المذهب الزيدي في هذه المسألة؟", "date": "2026-08-05"},
        {"user": "باحثة", "text": "أقترح إضافة مسألة حول العملات الرقمية", "date": "2026-08-06"},
    ]
    
    for comment in pending_comments:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"**{comment['user']}**: {comment['text']}")
            st.caption(f"📅 {comment['date']}")
        with col2:
            if st.button("✅ قبول", key=f"accept_{comment['user']}"):
                st.success("تم قبول التعليق")
        with col3:
            if st.button("❌ رفض", key=f"reject_{comment['user']}"):
                st.error("تم رفض التعليق")

# ---------- القسم 4: الإحصائيات ----------
elif section == "📈 الإحصائيات":
    st.subheader("📈 تحليلات وإحصائيات متقدمة")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # توزيع المسائل حسب التصنيف
        categories = {}
        for issue in issues:
            categories[issue["category"]] = categories.get(issue["category"], 0) + 1
        
        fig3 = px.pie(
            values=list(categories.values()),
            names=list(categories.keys()),
            title="توزيع المسائل حسب التصنيف",
            color_discrete_sequence=px.colors.qualitative.Set3,
        )
        st.plotly_chart(fig3, use_container_width=True)
    
    with col2:
        # توزيع المذاهب
        groups = {}
        for m in madhhabs:
            groups[m["group"]] = groups.get(m["group"], 0) + 1
        
        fig4 = px.pie(
            values=list(groups.values()),
            names=list(groups.keys()),
            title="توزيع المذاهب حسب المجموعة",
            color_discrete_sequence=["#4CAF50", "#2196F3", "#FF9800", "#9E9E9E"],
        )
        st.plotly_chart(fig4, use_container_width=True)
    
    # تقرير تصدير
    st.subheader("📤 تصدير التقارير")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📄 تصدير PDF"):
            st.info("سيتم تصدير التقرير بصيغة PDF (محاكاة)")
    with col2:
        if st.button("📊 تصدير CSV"):
            st.info("سيتم تصدير البيانات بصيغة CSV (محاكاة)")
    with col3:
        if st.button("📈 تصدير Excel"):
            st.info("سيتم تصدير البيانات بصيغة Excel (محاكاة)")

# ---------- القسم 5: الإعدادات ----------
elif section == "⚙️ الإعدادات":
    st.subheader("⚙️ إعدادات النظام")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔌 الاتصال بقاعدة البيانات")
        db_type = st.selectbox("نوع قاعدة البيانات", ["Firebase", "Supabase", "JSON Local"])
        if db_type == "Firebase":
            firebase_url = st.text_input("Firebase URL", value="https://your-project.firebaseio.com")
            firebase_key = st.text_input("API Key", type="password")
        elif db_type == "Supabase":
            supabase_url = st.text_input("Supabase URL")
            supabase_key = st.text_input("Anon Key", type="password")
    
    with col2:
        st.markdown("### 🤖 إعدادات الذكاء الاصطناعي")
        ai_provider = st.selectbox("مزود الذكاء الاصطناعي", ["Gemini", "OpenAI", "متعطل"])
        if ai_provider != "متعطل":
            ai_key = st.text_input("مفتاح API", type="password")
            ai_model = st.selectbox("النموذج", ["gemini-1.5-flash", "gpt-3.5-turbo", "gpt-4"])
    
    st.markdown("---")
    
    if st.button("💾 حفظ الإعدادات", type="primary"):
        st.success("✅ تم حفظ الإعدادات بنجاح")
        st.balloons()
