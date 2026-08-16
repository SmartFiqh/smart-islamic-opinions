import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/filter_provider.dart';
import '../providers/language_provider.dart';
import 'home_screen.dart';

class OnboardingScreen extends StatelessWidget {
  const OnboardingScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final filter = Provider.of<FilterProvider>(context);
    final lang = Provider.of<LanguageProvider>(context);
    final isRtl = lang.currentLocale.languageCode == 'ar' ||
        lang.currentLocale.languageCode == 'fa' ||
        lang.currentLocale.languageCode == 'ur';

    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.menu_book, size: 80, color: Color(0xFF1B5E20)),
              const SizedBox(height: 20),
              Text(
                isRtl ? 'الجامع الذكي لآراء المذاهب الإسلامية' : 'Smart Compendium of Islamic Madhhab Opinions',
                style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 10),
              Text(
                isRtl
                    ? 'منصة عرض واستعراض آراء المذاهب والفتاوى المعاصرة'
                    : 'A platform to view and review opinions of schools and contemporary fatwas',
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 16, color: Colors.grey),
              ),
              const SizedBox(height: 40),
              DropdownButtonFormField<String>(
                value: lang.currentLocale.languageCode,
                items: const [
                  DropdownMenuItem(value: 'ar', child: Text('العربية')),
                  DropdownMenuItem(value: 'en', child: Text('English')),
                  DropdownMenuItem(value: 'fa', child: Text('فارسی')),
                  DropdownMenuItem(value: 'ur', child: Text('اُردُو')),
                  DropdownMenuItem(value: 'id', child: Text('Bahasa Indonesia')),
                ],
                onChanged: (value) => lang.setLanguage(value!),
                decoration: InputDecoration(
                  labelText: isRtl ? 'اختر اللغة' : 'Select Language',
                ),
              ),
              const SizedBox(height: 20),
              DropdownButtonFormField<String>(
                value: filter.selectedGroup,
                items: [
                  DropdownMenuItem(
                    value: 'all',
                    child: Text(isRtl ? '🌐 جميع المذاهب (9)' : '🌐 All Schools (9)'),
                  ),
                  DropdownMenuItem(
                    value: 'Sunni',
                    child: Text(isRtl ? '☀️ مذاهب السنة (5)' : '☀️ Sunni Schools (5)'),
                  ),
                  DropdownMenuItem(
                    value: 'Shia',
                    child: Text(isRtl ? '🌙 مذاهب الشيعة (2)' : '🌙 Shia Schools (2)'),
                  ),
                  DropdownMenuItem(
                    value: 'Ibadi',
                    child: Text(isRtl ? '🏔️ المذهب الإباضي' : '🏔️ Ibadi School'),
                  ),
                  DropdownMenuItem(
                    value: 'Other',
                    child: Text(isRtl ? '📚 آراء أخرى' : '📚 Other Views'),
                  ),
                ],
                onChanged: (value) => filter.setGroup(value!),
                decoration: InputDecoration(
                  labelText: isRtl ? 'فلتر المذاهب الرئيسي' : 'Main Madhhab Filter',
                ),
              ),
              const SizedBox(height: 40),
              ElevatedButton(
                onPressed: () => Navigator.pushReplacement(
                  context,
                  MaterialPageRoute(builder: (_) => const HomeScreen()),
                ),
                child: Text(isRtl ? 'ابدأ' : 'Start'),
              ),
              const SizedBox(height: 16),
              Text(
                isRtl
                    ? '🕊️ هذه منصة عرض وليست موقع إفتاء'
                    : '🕊️ This is a display platform, not a fatwa site',
                style: const TextStyle(fontSize: 12, color: Colors.grey),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
