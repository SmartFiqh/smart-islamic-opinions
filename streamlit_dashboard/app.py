"""
لوحة تحكم الجامع الذكي (Streamlit)
------------------------------------
تقرأ نفس بيانات Firestore التي يكتبها/يقرؤها تطبيق Flutter:
  - collection "issues"   -> المسائل الفقهية (تُعرض إحصائياتها هنا)
  - collection "comments" -> تعليقات المستخدمين (تُراجَع وتُعتمد من هنا)

بذلك يعمل التطبيقان (Flutter + Streamlit) على قاعدة بيانات واحدة
مشتركة بدل بيانات وهمية منفصلة في كل طرف.

تشغيل محلي:
    pip install -r requirements.txt
    streamlit run app.py

ملاحظة: إن لم يوجد ملف serviceAccountKey.json، تعمل اللوحة تلقائياً
بوضع "بيانات تجريبية" حتى لا تتعطل بالكامل.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="لوحة تحكم الجامع الذكي",
    page_icon="🕌",
    layout="wide",  # يبقى مقروءاً على الديسكتوب، وStreamlit يُكدّس الأعمدة تلقائياً على الجوال
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------
# الاتصال بـ Firebase (اختياري) — مع تراجع آمن لبيانات تجريبية عند الفشل
# -----------------------------------------------------------------------
@st.cache_resource
def get_firestore_client():
    """يحاول الاتصال بـ Firestore. يعيد None بهدوء إن تعذّر ذلك،
    بدل استخدام `except:` عارية التي كانت تُخفي أي خطأ حقيقي."""
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore

        if not firebase_admin._apps:
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except FileNotFoundError:
        return None
    except Exception as e:  # أي خطأ آخر (مفاتيح خاطئة، صلاحيات...) يُعرض بدل إخفائه
        st.session_state["firebase_error"] = str(e)
        return None


db = get_firestore_client()
is_connected = db is not None


# -----------------------------------------------------------------------
# بيانات تجريبية احتياطية (نفس شكل نموذج IssueModel/CommentModel في Flutter)
# -----------------------------------------------------------------------
MOCK_ISSUES = [
    {"id": "jama_prayer", "titleAr": "صلاة الجماعة", "category": "prayer", "views": 1250},
    {"id": "zakat_bank", "titleAr": "زكاة البنك", "category": "zakat", "views": 890},
    {"id": "arafah_fasting", "titleAr": "صيام عرفة", "category": "fasting", "views": 670},
    {"id": "bank_interest", "titleAr": "فوائد بنكية", "category": "transactions", "views": 2100},
    {"id": "niqab", "titleAr": "النقاب", "category": "other", "views": 560},
]

MOCK_COMMENTS = [
    {
        "id": "c1", "issueId": "jama_prayer", "userName": "مستخدم",
        "commentText": "شرح واضح جداً، جزاكم الله خيراً.",
        "rating": 5, "type": "appreciation", "isApproved": False,
        "sentiment": "إيجابي", "sentimentScore": 0.92,
        "timestamp": datetime.now().isoformat(),
    },
    {
        "id": "c2", "issueId": "bank_interest", "userName": "مستخدم",
        "commentText": "أقترح إضافة رأي المجمع الفقهي الإسلامي بالتفصيل.",
        "rating": 4, "type": "suggestion", "isApproved": False,
        "sentiment": "محايد", "sentimentScore": 0.55,
        "timestamp": datetime.now().isoformat(),
    },
]


@st.cache_data(ttl=60)
def load_issues():
    if not is_connected:
        return pd.DataFrame(MOCK_ISSUES)
    docs = db.collection("issues").stream()
    rows = [{"id": d.id, **d.to_dict()} for d in docs]
    if not rows:
        return pd.DataFrame(MOCK_ISSUES)
    df = pd.DataFrame(rows)
    if "views" not in df.columns:
        df["views"] = 0
    return df


def load_comments():
    if not is_connected:
        return pd.DataFrame(MOCK_COMMENTS)
    docs = db.collection("comments").order_by(
        "timestamp", direction="DESCENDING"
    ).limit(200).stream()
    rows = [{"id": d.id, **d.to_dict()} for d in docs]
    return pd.DataFrame(rows) if rows else pd.DataFrame(MOCK_COMMENTS)


def approve_comment(comment_id: str):
    if is_connected:
        db.collection("comments").document(comment_id).update({"isApproved": True})
    else:
        st.warning("⚠️ وضع تجريبي بدون اتصال — لن يُحفظ الاعتماد فعلياً.")


def delete_comment(comment_id: str):
    if is_connected:
        db.collection("comments").document(comment_id).delete()
    else:
        st.warning("⚠️ وضع تجريبي بدون اتصال — لن يُحذف فعلياً.")


# -----------------------------------------------------------------------
# الواجهة
# -----------------------------------------------------------------------
st.markdown("# 🕌 لوحة تحكم الجامع الذكي")

if is_connected:
    st.success("✅ متصل بـ Firebase — نفس قاعدة بيانات تطبيق Flutter")
else:
    msg = "⚠️ وضع المحاكاة (بيانات تجريبية) — لا يوجد اتصال حالي بـ Firebase."
    if st.session_state.get("firebase_error"):
        msg += f"\n\nتفاصيل الخطأ: `{st.session_state['firebase_error']}`"
    st.warning(msg)

issues_df = load_issues()
comments_df = load_comments()

tab_overview, tab_issues, tab_comments = st.tabs(["📊 نظرة عامة", "📚 المسائل", "💬 مراجعة التعليقات"])

# ---- تبويب 1: نظرة عامة ------------------------------------------------
with tab_overview:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📚 المسائل", len(issues_df))
    col2.metric("🕌 المذاهب", 9)
    total_views = int(issues_df["views"].sum()) if "views" in issues_df.columns else 0
    col3.metric("👁️ مشاهدات", f"{total_views:,}")
    pending = int((comments_df["isApproved"] == False).sum()) if "isApproved" in comments_df.columns else 0
    col4.metric("🕓 تعليقات بانتظار المراجعة", pending)

    st.subheader("📊 توزيع المشاهدات حسب المسألة")
    if "titleAr" in issues_df.columns and "views" in issues_df.columns:
        fig = px.bar(
            issues_df.sort_values("views", ascending=False),
            x="titleAr", y="views",
            labels={"titleAr": "المسألة", "views": "المشاهدات"},
            color="views", color_continuous_scale="Greens",
        )
        fig.update_layout(showlegend=False, xaxis_title=None)
        st.plotly_chart(fig, use_container_width=True)  # يتمدد تلقائياً على الديسكتوب ويتقلص على الجوال

    if "category" in issues_df.columns:
        st.subheader("📊 المسائل حسب التصنيف")
        # category قد تكون قائمة (List<String> من Flutter) أو نصاً بسيطاً في البيانات القديمة —
        # نطبّعها هنا قبل العد حتى لا يفشل value_counts() على قيم غير قابلة للـ hashing.
        def _first_category(val):
            if isinstance(val, list):
                return val[0] if val else "other"
            return val if isinstance(val, str) and val else "other"

        cat_series = issues_df["category"].apply(_first_category)
        cat_counts = cat_series.value_counts().reset_index()
        cat_counts.columns = ["التصنيف", "العدد"]
        fig2 = px.pie(cat_counts, names="التصنيف", values="العدد", hole=0.4)
        st.plotly_chart(fig2, use_container_width=True)

# ---- تبويب 2: المسائل --------------------------------------------------
with tab_issues:
    st.subheader("📚 كل المسائل المسجّلة")
    search_term = st.text_input("🔍 ابحث عن مسألة", "")
    display_df = issues_df
    if search_term and "titleAr" in issues_df.columns:
        display_df = issues_df[issues_df["titleAr"].str.contains(search_term, na=False)]
    st.dataframe(
        display_df[[c for c in ["id", "titleAr", "category", "views"] if c in display_df.columns]],
        use_container_width=True,
        hide_index=True,
    )

# ---- تبويب 3: مراجعة التعليقات -----------------------------------------
with tab_comments:
    st.subheader("💬 التعليقات والتقييمات الواردة من التطبيق")
    st.caption("هذه التعليقات مرسلة من تطبيق Flutter مباشرة (شاشة عرض المسألة) وتنتظر اعتمادك قبل النشر.")

    if comments_df.empty:
        st.info("لا توجد تعليقات بعد.")
    else:
        status_filter = st.radio(
            "عرض:", ["الكل", "بانتظار المراجعة", "معتمدة"], horizontal=True
        )
        filtered = comments_df
        if status_filter == "بانتظار المراجعة" and "isApproved" in comments_df.columns:
            filtered = comments_df[comments_df["isApproved"] == False]
        elif status_filter == "معتمدة" and "isApproved" in comments_df.columns:
            filtered = comments_df[comments_df["isApproved"] == True]

        for _, row in filtered.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f"**{row.get('userName', 'مستخدم')}** — {row.get('type', '')}")
                    st.write(row.get("commentText", ""))
                    stars = "⭐" * int(row.get("rating", 0) or 0)
                    sentiment = row.get("sentiment", "")
                    st.caption(f"{stars}  ·  المشاعر: {sentiment}  ·  المسألة: {row.get('issueId', '')}")
                with c2:
                    if not row.get("isApproved", False):
                        if st.button("✅ اعتماد", key=f"approve_{row['id']}"):
                            approve_comment(row["id"])
                            st.rerun()
                    else:
                        st.success("منشور")
                    if st.button("🗑️ حذف", key=f"delete_{row['id']}"):
                        delete_comment(row["id"])
                        st.rerun()

st.divider()
st.caption(
    "🕊️ هذه اللوحة مخصّصة لفريق العمل فقط (مراجعة وإدارة) — "
    "وليست موقع إفتاء، تماماً كتطبيق الجوال/الديسكتوب."
)
