import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/language_provider.dart';

class ImamsScreen extends StatelessWidget {
  const ImamsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final lang = Provider.of<LanguageProvider>(context);
    final isRtl = lang.currentLocale.languageCode == 'ar' ||
        lang.currentLocale.languageCode == 'fa' ||
        lang.currentLocale.languageCode == 'ur';

    // بيانات الأئمة باللغات الأربع (ملخص)
    final List<Map<String, dynamic>> imams = [
      {
        'name': isRtl ? 'الإمام أبو حنيفة النعمان (80-150هـ)' : 'Imam Abu Hanifa (80-150 AH)',
        'title': isRtl ? 'المذهب الحنفي' : 'Hanafi School',
        'bio': isRtl
            ? 'إمام أهل الرأي والقياس، أسس مدرسة الكوفة التي اعتمدت على توسيع القياس ومراعاة الاستحسان.'
            : 'Imam of the people of opinion and analogy, founded the Kufa school which relied on expanding analogy and considering juristic preference.',
        'students': isRtl
            ? 'أبو يوسف، محمد بن الحسن الشيباني، زفر بن الهذيل.'
            : 'Abu Yusuf, Muhammad ibn al-Hasan al-Shaybani, Zufar ibn al-Hudhayl.',
      },
      {
        'name': isRtl ? 'الإمام مالك بن أنس (93-179هـ)' : 'Imam Malik ibn Anas (93-179 AH)',
        'title': isRtl ? 'المذهب المالكي' : 'Maliki School',
        'bio': isRtl
            ? 'إمام دار الهجرة بالمدينة، صاحب الموطأ، اعتمد على "عمل أهل المدينة" كأحد مصادر التشريع.'
            : 'Imam of the House of Hijra in Medina, author of Al-Muwatta, relied on the "practice of the people of Medina" as one of the sources of legislation.',
        'students': isRtl
            ? 'ابن القاسم، أشهب، ابن وهب، سحنون.'
            : 'Ibn al-Qasim, Ashhab, Ibn Wahb, Sahnun.',
      },
      {
        'name': isRtl ? 'الإمام الشافعي (150-204هـ)' : 'Imam Al-Shafi\'i (150-204 AH)',
        'title': isRtl ? 'المذهب الشافعي' : 'Shafi\'i School',
        'bio': isRtl
            ? 'مؤسس علم أصول الفقه، جمع بين مدرسة الحجاز (الحديث) ومدرسة العراق (الرأي).'
            : 'Founder of the science of jurisprudence, combined the Hejaz school (Hadith) and the Iraq school (opinion).',
        'students': isRtl
            ? 'المزني، البويطي، الربيع بن سليمان.'
            : 'Al-Muzani, Al-Buwayti, Al-Rabi\' ibn Sulayman.',
      },
      {
        'name': isRtl ? 'الإمام أحمد بن حنبل (164-241هـ)' : 'Imam Ahmad ibn Hanbal (164-241 AH)',
        'title': isRtl ? 'المذهب الحنبلي' : 'Hanbali School',
        'bio': isRtl
            ? 'إمام أهل الحديث، صاحب المسند، تميز بالتمسك بالنص والآثار، وصبر على المحنة.'
            : 'Imam of the people of Hadith, author of Al-Musnad, distinguished by adherence to the text and traditions, and patient in tribulation.',
        'students': isRtl
            ? 'أبو بكر الخلال، ابن قدامة المقدسي، القاضي أبو يعلى.'
            : 'Abu Bakr al-Khallal, Ibn Qudamah al-Maqdisi, Al-Qadi Abu Ya\'la.',
      },
      {
        'name': isRtl ? 'الإمام داود الظاهري (202-270هـ)' : 'Imam Dawud al-Dhahiri (202-270 AH)',
        'title': isRtl ? 'المذهب الظاهري' : 'Dhahiri School',
        'bio': isRtl
            ? 'إمام أهل الظاهر، يعتمد على النصوص بظاهرها، ويرفض القياس والاستحسان.'
            : 'Imam of the literalists, relies on the apparent meaning of texts, and rejects analogy and juristic preference.',
        'students': isRtl
            ? 'ابن حزم الأندلسي (أشهر من نشره ودوّنه في "المحلى").'
            : 'Ibn Hazm al-Andalusi (the most famous who spread and codified it in "Al-Muhalla").',
      },
      {
        'name': isRtl ? 'الإمام جعفر الصادق (80-148هـ)' : 'Imam Ja\'far al-Sadiq (80-148 AH)',
        'title': isRtl ? 'المذهب الجعفري' : 'Ja\'fari School',
        'bio': isRtl
            ? 'المؤسس الفعلي للمذهب الجعفري (الإثنا عشري)، من نسل النبي ﷺ، وضع أسس الفقه الإمامي.'
            : 'The actual founder of the Ja\'fari (Twelver) school, descendant of the Prophet ﷺ, laid the foundations of Imami jurisprudence.',
        'students': isRtl
            ? 'الشيخ المفيد، الشريف المرتضى، الشيخ الطوسي.'
            : 'Al-Shaykh al-Mufid, Al-Sharif al-Murtada, Al-Shaykh al-Tusi.',
      },
      {
        'name': isRtl ? 'الإمام زيد بن علي (80-122هـ)' : 'Imam Zayd ibn Ali (80-122 AH)',
        'title': isRtl ? 'المذهب الزيدي' : 'Zaidi School',
        'bio': isRtl
            ? 'مؤسس المذهب الزيدي، من نسل الحسين، قريب من مذهب المعتزلة في الأصول ومن أهل السنة في الفروع.'
            : 'Founder of the Zaidi school, descendant of Al-Husayn, close to the Mu\'tazila in principles and to Ahl al-Sunnah in branches.',
        'students': isRtl
            ? 'أبو خالد الواسطي، الناصر الأطروش، الهادي يحيى بن الحسين.'
            : 'Abu Khalid al-Wasiti, Al-Nasir al-Utrush, Al-Hadi Yahya ibn al-Husayn.',
      },
      {
        'name': isRtl ? 'الإمام جابر بن زيد (القرن الأول-93هـ)' : 'Imam Jabir ibn Zayd (1st century - 93 AH)',
        'title': isRtl ? 'المذهب الإباضي' : 'Ibadi School',
        'bio': isRtl
            ? 'إمام عُمان واليمن، المرجع الفقهي الأول للإباضية، تلميذ ابن عباس.'
            : 'Imam of Oman and Yemen, the primary jurisprudential reference for the Ibadis, a student of Ibn Abbas.',
        'students': isRtl
            ? 'أبو سعيد الكدمي، أبو نزار الخروصي، نور الدين السالمي.'
            : 'Abu Sa\'id al-Kadmi, Abu Nizar al-Kharusi, Nur al-Din al-Salimi.',
      },
    ];

    return Scaffold(
      appBar: AppBar(
        title: Text(isRtl ? '📜 الأئمة المؤسسون' : '📜 Founding Imams'),
      ),
      body: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: imams.length,
        itemBuilder: (ctx, index) {
          final data = imams[index];
          return Card(
            margin: const EdgeInsets.symmetric(vertical: 8),
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    data['name'],
                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 4),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: Colors.green.shade100,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      data['title'],
                      style: TextStyle(color: Colors.green.shade800),
                    ),
                  ),
                  const SizedBox(height: 10),
                  Text(data['bio']),
                  const SizedBox(height: 10),
                  Text(
                    isRtl ? '🎓 أشهر الشيوخ والتلاميذ:' : '🎓 Notable teachers and students:',
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                  Text(data['students']),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}
