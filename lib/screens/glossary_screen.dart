import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/language_provider.dart';

class GlossaryScreen extends StatelessWidget {
  const GlossaryScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final lang = Provider.of<LanguageProvider>(context);
    final isRtl = lang.currentLocale.languageCode == 'ar' ||
        lang.currentLocale.languageCode == 'fa' ||
        lang.currentLocale.languageCode == 'ur';

    final List<Map<String, String>> terms = [
      {
        'term': isRtl ? 'الفرض (Fard)' : 'Fard (Obligatory)',
        'definition': isRtl
            ? 'ما طلب الشارع فعله طلباً جازماً، ويثاب فاعله ويعاقب تاركه. (مثل: الصلوات الخمس)'
            : 'What the Lawgiver demanded to be done decisively, the doer is rewarded and the abandoner is punished (e.g., the five prayers).',
      },
      {
        'term': isRtl ? 'فرض الكفاية' : 'Fard Kifayah (Collective Duty)',
        'definition': isRtl
            ? 'ما طلب الشارع فعله على عموم المكلفين، ويسقط عن الجميع بفعل البعض، ويأثم الكل إن تركوه (مثل: صلاة الجنازة).'
            : 'What the Lawgiver demanded from all obligated individuals, falls from all when some perform it, all sin if they all abandon it (e.g., funeral prayer).',
      },
      {
        'term': isRtl ? 'الواجب (Wajib)' : 'Wajib (Duty)',
        'definition': isRtl
            ? 'عند الحنفية: ما ثبت بدليل ظني (كصلاة الوتر). عند الجمهور: مرادف للفرض.'
            : 'According to Hanafis: what is proven by a speculative evidence (e.g., Witr prayer). According to the majority: synonymous with Fard.',
      },
      {
        'term': isRtl ? 'السنة المؤكدة' : 'Sunnah Mu\'akkadah (Emphasized Sunnah)',
        'definition': isRtl
            ? 'ما واظب النبي ﷺ على فعله في الغالب، وتركه أحياناً. تركها مكروه عند الحنفية (مثل: سنة الفجر).'
            : 'What the Prophet ﷺ consistently did mostly, but sometimes left. Abandoning it is disliked (Makruh) according to Hanafis (e.g., the Sunnah of Fajr).',
      },
      {
        'term': isRtl ? 'السنة (غير المؤكدة)' : 'Sunnah Ghayr Mu\'akkadah (Non-emphasized Sunnah)',
        'definition': isRtl
            ? 'ما فعله النبي ﷺ أحياناً وتركه أحياناً. تركها لا إثم فيه (مثل: سنة الظهر القبلية).'
            : 'What the Prophet ﷺ sometimes did and sometimes left. Abandoning it is not sinful (e.g., the Sunnah before Dhuhr).',
      },
      {
        'term': isRtl ? 'المستحب (مندوب)' : 'Mustahabb (Recommended)',
        'definition': isRtl
            ? 'ما رغب الشارع في فعله دون إلزام، ويثاب فاعله ولا يعاقب تاركه (مثل: صلاة الضحى).'
            : 'What the Lawgiver encouraged without obligation, the doer is rewarded and the abandoner is not punished (e.g., Duha prayer).',
      },
      {
        'term': isRtl ? 'المباح (Mubah)' : 'Mubah (Permissible)',
        'definition': isRtl
            ? 'ما خُيّر الشارع بين فعله وتركه، ولا ثواب على فعله بذاته ولا عقاب (مثل: أكل التفاح).'
            : 'What the Lawgiver allowed between doing and leaving, no reward for doing it per se and no punishment (e.g., eating apples).',
      },
      {
        'term': isRtl ? 'المكروه (Makruh)' : 'Makruh (Disliked)',
        'definition': isRtl
            ? 'ما طلب الشارع تركه طلباً غير جازم، ويثاب تاركه ولا يعاقب فاعله (مثل: الأكل بالشمال).'
            : 'What the Lawgiver demanded to be left without decisiveness, the abandoner is rewarded and the doer is not punished (e.g., eating with the left hand).',
      },
      {
        'term': isRtl ? 'الحرام (Haram)' : 'Haram (Forbidden)',
        'definition': isRtl
            ? 'ما طلب الشارع تركه طلباً جازماً، ويعاقب فاعله، ويثاب تاركه (مثل: شرب الخمر).'
            : 'What the Lawgiver demanded to be left decisively, the doer is punished, and the abandoner is rewarded (e.g., drinking alcohol).',
      },
      {
        'term': isRtl ? 'الخمس (عند الشيعة)' : 'Khums (Among Shia)',
        'definition': isRtl
            ? 'واجب مالي بنسبة 20% من أرباح المكاسب السنوية بعد خصم النفقات، يُصرف للإمام والأصناف الخاصة.'
            : 'A financial duty of 20% from annual profits after deducting expenses, spent on the Imam and specific categories.',
      },
    ];

    return Scaffold(
      appBar: AppBar(
        title: Text(isRtl ? '📚 قاموس المصطلحات الفقهية' : '📚 Fiqh Glossary'),
      ),
      body: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: terms.length,
        itemBuilder: (ctx, index) {
          final data = terms[index];
          return Card(
            margin: const EdgeInsets.symmetric(vertical: 6),
            child: ExpansionTile(
              leading: const Icon(Icons.info_outline, color: Colors.green),
              title: Text(
                data['term']!,
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
              children: [
                Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Text(
                    data['definition']!,
                    style: const TextStyle(fontSize: 16),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}
