# الجامع الذكي — Flutter app + Streamlit dashboard

## ما تم إصلاحه

### 1. أخطاء كانت تمنع تجميع تطبيق Flutter بالكامل
| المشكلة | الإصلاح |
|---|---|
| `lib/models/issue_model.dart` كان **مفقوداً كلياً** رغم استخدامه في كل الشاشات | أُنشئ من جديد (`IssueModel`, `MadhabView`) مع 5 مسائل تجريبية كاملة و`toMap`/`fromMap` للتوافق مع Firestore |
| `firestore_service.dart` كان يعرّف كلاس `AIService` بينما `search_provider.dart` يستدعي `FirestoreService().getAllIssues()` (كلاس غير موجود) | أُعيد كتابته كـ `FirestoreService` حقيقية: `getAllIssues`, `addComment`, `incrementViewCount`, `seedMockIssuesIfEmpty` |
| `SearchProvider` لا يملك `updateQuery()` ولا `search()` رغم أن `home_screen.dart` يستدعيهما | أُضيفا كطبقة رقيقة فوق `smartSearch()` الموجودة |
| لا أحد يستدعي `Firebase.initializeApp()` أو `.init()` لخدمات Gemini | أُضيفت في `main.dart` مع `try/catch` بحيث لا يتعطل التطبيق إن لم تُضبط المفاتيح بعد — يعمل تلقائياً بالبيانات التجريبية والبحث النصي |
| تعليقات المستخدم (`CommentModel`) تُبنى ثم **تضيع** فور إظهار الـ SnackBar | أُضيفت `submitComment()` في `SearchProvider` تحفظها فعلياً في مجموعة `comments` بـ Firestore |
| `pubspec.yaml`: `generate: true` بلا `l10n.yaml`/ARB، و`google-services.json`/`GoogleService-Info.plist` مُدرجة خطأً كـ Flutter assets | أُزيلا؛ راجع التعليقات داخل `pubspec.yaml` |

### 2. العمل على الديسكتوب والجوال معاً
- أُضيف `lib/core/responsive.dart`: يحتوي `ResponsiveCenter` (يوسّط المحتوى بعرض أقصى مريح على الشاشات الواسعة، ويملأ الشاشة كاملة على الجوال) و`ResponsiveGrid` (شبكة تتحول تلقائياً من عمود واحد على الجوال إلى عدة أعمدة على الديسكتوب).
- طُبّق هذا في `home_screen.dart` و`result_screen.dart` — وهو نمط يمكن تكراره بسهولة في أي شاشة أخرى.
- Flutter نفسه يبني من نفس الشيفرة لكل من: Android, iOS, Web, Windows, macOS, Linux — لا حاجة لمشروعين منفصلين.
- لوحة Streamlit مبنية أصلاً على الويب فتعمل من أي متصفح — سطح مكتب أو جوال — وتتكيف تلقائياً (الأعمدة تتكدس عمودياً على الشاشات الضيقة).

### 3. ربط Flutter وStreamlit ببعضهما فعلياً
سابقاً كل تطبيق كان يستخدم بيانات وهمية منفصلة تماماً. الآن كلاهما يقرأ/يكتب من **نفس** مشروع Firebase:
- تطبيق Flutter يكتب تعليقات المستخدمين في `comments`، ويقرأ المسائل من `issues`.
- لوحة Streamlit تقرأ `issues` و`comments` مباشرة، وتسمح لفريق العمل باعتماد/حذف التعليقات الواردة من التطبيق.
- عند تعذّر الاتصال بـ Firebase في أي منهما، يتحول كل تطبيق تلقائياً لوضع بيانات تجريبية بدل التعطل (بدون `except:` عارية تخفي الأخطاء الحقيقية كما كانت في `app (1).py`).

## التشغيل

### Flutter (جوال + ديسكتوب + ويب)
```bash
flutter pub get
flutterfire configure   # مرة واحدة فقط — يربط المشروع بـ Firebase وينشئ firebase_options.dart
flutter run -d chrome    # أو -d windows / -d macos / -d linux / جهاز جوال متصل
```
ضع مفتاح Gemini في ملف `.env` بالجذر:
```
GEMINI_API_KEY=your_key_here
```

### Streamlit (لوحة التحكم — تعمل من أي متصفح، ديسكتوب أو جوال)
```bash
cd streamlit_dashboard
pip install -r requirements.txt
# ضع serviceAccountKey.json (مفتاح خدمة Firebase) في هذا المجلد للاتصال الفعلي،
# وإلا ستعمل اللوحة تلقائياً بوضع بيانات تجريبية
streamlit run app.py
```

## هيكل المشروع
```
lib/
  core/
    responsive.dart        # مساعد التوافق ديسكتوب/جوال
    theme/app_theme.dart
  models/
    issue_model.dart        # (جديد) — كان مفقوداً
    madhhab_model.dart
    comment_model.dart       # (مُحدَّث) toMap/fromMap
  providers/
    search_provider.dart     # (مُصلَح) updateQuery/search/submitComment
    filter_provider.dart
    language_provider.dart
  services/
    firestore_service.dart   # (مُصلَح بالكامل) كان كلاس خاطئ
    semantic_search_service.dart
    summarization_service.dart
    analytics_service.dart
  screens/
    home_screen.dart         # (مُحدَّث) تخطيط متجاوب
    result_screen.dart       # (مُحدَّث) حفظ التعليقات فعلياً + تخطيط متجاوب
    onboarding_screen.dart
    imams_screen.dart
    glossary_screen.dart
    geography_screen.dart
    contact_screen.dart
  main.dart                  # (مُصلَح) يهيّئ Firebase وخدمات الذكاء الاصطناعي فعلياً
streamlit_dashboard/
  app.py                     # (أُعيدت كتابته) اتصال حقيقي + مراجعة تعليقات
  requirements.txt
pubspec.yaml                 # (مُصلَح)
index.html
```
