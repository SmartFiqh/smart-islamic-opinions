import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:provider/provider.dart';
import 'providers/filter_provider.dart';
import 'providers/search_provider.dart';
import 'providers/language_provider.dart';
import 'screens/onboarding_screen.dart';
import 'core/theme/app_theme.dart';

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

void main() {
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
            home: const OnboardingScreen(),
          );
        },
      ),
    );
  }
}
