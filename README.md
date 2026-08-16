lib/
├── main.dart                   # نقطة الدخول إلى التطبيق
├── core/                       # الأساسيات العامة
│   └── theme/                  # إعدادات الثيمات والألوان
├── models/                     # نماذج البيانات (المذاهب، المسائل، التعليقات)
├── providers/                  # إدارة حالة التطبيق (Riverpod / Provider)
├── screens/                    # شاشات التطبيق
│   ├── onboarding_screen.dart  # شاشة الترحيب واللغة
│   ├── home_screen.dart        # الشاشة الرئيسية والبحث
│   ├── result_screen.dart      # عرض الردود الثلاثة + التقييم والتعليقات
│   ├── contact_screen.dart     # نموذج التواصل غير المباشر (بريد إلكتروني)
│   ├── imams_screen.dart       # شاشة الأئمة المؤسسين
│   ├── geography_screen.dart   # شاشة الخريطة الجغرافية
│   └── glossary_screen.dart    # شاشة قاموس المصطلحات
└── ...
