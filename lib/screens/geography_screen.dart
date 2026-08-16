import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/language_provider.dart';

class GeographyScreen extends StatelessWidget {
  const GeographyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final lang = Provider.of<LanguageProvider>(context);
    final isRtl = lang.currentLocale.languageCode == 'ar' ||
        lang.currentLocale.languageCode == 'fa' ||
        lang.currentLocale.languageCode == 'ur';

    final List<Map<String, String>> countries = [
      {'country': isRtl ? '🇸🇦 السعودية' : '🇸🇦 Saudi Arabia', 'madhab': isRtl ? 'الحنبلي' : 'Hanbali'},
      {'country': isRtl ? '🇪🇬 مصر' : '🇪🇬 Egypt', 'madhab': isRtl ? 'الشافعي (رسمياً)' : 'Shafi\'i (official)'},
      {'country': isRtl ? '🇲🇦 المغرب' : '🇲🇦 Morocco', 'madhab': isRtl ? 'المالكي' : 'Maliki'},
      {'country': isRtl ? '🇩🇿 الجزائر' : '🇩🇿 Algeria', 'madhab': isRtl ? 'المالكي' : 'Maliki'},
      {'country': isRtl ? '🇹🇳 تونس' : '🇹🇳 Tunisia', 'madhab': isRtl ? 'المالكي' : 'Maliki'},
      {'country': isRtl ? '🇱🇾 ليبيا' : '🇱🇾 Libya', 'madhab': isRtl ? 'المالكي' : 'Maliki'},
      {'country': isRtl ? '🇹🇷 تركيا' : '🇹🇷 Turkey', 'madhab': isRtl ? 'الحنفي' : 'Hanafi'},
      {'country': isRtl ? '🇵🇰 باكستان' : '🇵🇰 Pakistan', 'madhab': isRtl ? 'الحنفي' : 'Hanafi'},
      {'country': isRtl ? '🇮🇳 الهند' : '🇮🇳 India', 'madhab': isRtl ? 'الحنفي' : 'Hanafi'},
      {'country': isRtl ? '🇮🇩 إندونيسيا' : '🇮🇩 Indonesia', 'madhab': isRtl ? 'الشافعي' : 'Shafi\'i'},
      {'country': isRtl ? '🇲🇾 ماليزيا' : '🇲🇾 Malaysia', 'madhab': isRtl ? 'الشافعي' : 'Shafi\'i'},
      {'country': isRtl ? '🇮🇷 إيران' : '🇮🇷 Iran', 'madhab': isRtl ? 'الجعفري (الإثنا عشري)' : 'Ja\'fari (Twelver)'},
      {'country': isRtl ? '🇮🇶 العراق' : '🇮🇶 Iraq', 'madhab': isRtl ? 'الجعفري (الأغلبية)' : 'Ja\'fari (majority)'},
      {'country': isRtl ? '🇾🇪 اليمن' : '🇾🇪 Yemen', 'madhab': isRtl ? 'الزيدي (الشمال) / الشافعي (الجنوب)' : 'Zaidi (north) / Shafi\'i (south)'},
      {'country': isRtl ? '🇴🇲 عُمان' : '🇴🇲 Oman', 'madhab': isRtl ? 'الإباضي' : 'Ibadi'},
      {'country': isRtl ? '🇶🇦 قطر' : '🇶🇦 Qatar', 'madhab': isRtl ? 'الحنبلي' : 'Hanbali'},
      {'country': isRtl ? '🇰🇼 الكويت' : '🇰🇼 Kuwait', 'madhab': isRtl ? 'الحنفي / المالكي' : 'Hanafi / Maliki'},
      {'country': isRtl ? '🇯🇴 الأردن' : '🇯🇴 Jordan', 'madhab': isRtl ? 'الحنفي' : 'Hanafi'},
    ];

    return Scaffold(
      appBar: AppBar(
        title: Text(isRtl ? '🗺️ انتشار المذاهب حول العالم' : '🗺️ Madhhab Distribution Worldwide'),
      ),
      body: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: countries.length,
        itemBuilder: (ctx, index) {
          final data = countries[index];
          return Card(
            margin: const EdgeInsets.symmetric(vertical: 6),
            child: ListTile(
              leading: const Icon(Icons.place, color: Colors.blue),
              title: Text(data['country']!, style: const TextStyle(fontWeight: FontWeight.bold)),
              subtitle: Text('${isRtl ? 'المذهب السائد:' : 'Dominant school:'} ${data['madhab']}'),
              trailing: const Icon(Icons.arrow_forward_ios, size: 16),
            ),
          );
        },
      ),
    );
  }
}
