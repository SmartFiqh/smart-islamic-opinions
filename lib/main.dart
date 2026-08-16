import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:provider/provider.dart';
import 'package:firebase_core/firebase_core.dart';
import 'providers/filter_provider.dart';
import 'providers/search_provider.dart';
import 'providers/language_provider.dart';
import 'screens/onboarding_screen.dart';
import 'core/theme/app_theme.dart';
import 'services/semantic_search_service.dart';
import 'services/summarization_service.dart';
import 'services/analytics_service.dart';

// دالة للحصول على اسم التطبيق حسب اللغة
String getAppTitle(String languageCode) {
  switch (languageCode) {
    case 'en':
      return 'The Smart Compendium of Islamic Madhhab Opinions';
    case 'ur':
      return 'اسلامی مذاہب کی آراء کا ذکی مجموعہ';
    case 'fa':
      return 'جامع هوشمند آراء مذاهب اسلامی';
    case 'id':
      return 'Kompendium Cerdas Pendapat Mazhab-Mazhab Islam';
    default:
      return 'الجامع الذكي لآراء المذاهب الإسلامية';
  }
}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Firebase و مفاتيح الذكاء الاصطناعي اختياريان: إن لم يُضبطا (لا يوجد
  // google-services.json / .env) يستمر التطبيق بالعمل على البيانات
  // التجريبية والبحث النصي فقط، بدل أن يتعطل بالكامل.
  //
  // للتشغيل الفعلي على الويب/الديسكتوب بالإضافة إلى الجوال، شغّل مرة
  // واحدة: `flutterfire configure` — سيولّد lib/firebase_options.dart
  // تلقائياً؛ عندها استبدل السطر أدناه بـ:
  //   await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);
  try {
    await Firebase.initializeApp();
  } catch (_) {
    debugPrint('⚠️ Firebase not configured — running with local mock data.');
  }

  try {
    await SemanticSearchService.init();
    await SummarizationService.init();
    await AnalyticsService.init();
  } catch (_) {
    debugPrint('⚠️ GEMINI_API_KEY not found — AI features disabled, text search still works.');
  }

  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => FilterProvider()),
        ChangeNotifierProvider(create: (_) => SearchProvider()),
        ChangeNotifierProvider(create: (_) => LanguageProvider()),
      ],
      child: Consumer<LanguageProvider>(
        builder: (context, langProvider, child) {
          return MaterialApp(
            title: getAppTitle(langProvider.currentLocale.languageCode),
            theme: AppTheme.lightTheme,
            debugShowCheckedModeBanner: false,
            locale: langProvider.currentLocale,
            supportedLocales: const [
              Locale('ar'),
              Locale('en'),
              Locale('fa'),
              Locale('ur'),
              Locale('id'),
            ],
            localizationsDelegates: const [
              GlobalMaterialLocalizations.delegate,
              GlobalWidgetsLocalizations.delegate,
              GlobalCupertinoLocalizations.delegate,
            ],
            // يعمل بنفس الشيفرة على الجوال (iOS/Android)، الويب، وسطح
            // المكتب (Windows/macOS/Linux) — الفروقات تُدار عبر
            // core/responsive.dart داخل كل شاشة.
            home: const OnboardingScreen(),
          );
        },
      ),
    );
  }
}
