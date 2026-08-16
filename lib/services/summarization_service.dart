import 'package:google_generative_ai/google_generative_ai.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

class SummarizationService {
  static String? _apiKey;

  static Future<void> init() async {
    await dotenv.load(fileName: '.env');
    _apiKey = dotenv.env['GEMINI_API_KEY'];
  }

  /// تلخيص النص إلى 3 مستويات: مختصر جداً، مبسط، موسع
  static Future<SummaryResult> summarizeText(String fullText, String lang) async {
    if (_apiKey == null || _apiKey!.isEmpty) {
      return SummaryResult(
        short: 'لم يتوفر التلخيص',
        simple: fullText,
        detailed: fullText,
      );
    }

    try {
      final model = GenerativeModel(
        model: 'gemini-1.5-flash',
        apiKey: _apiKey!,
      );

      final langInstruction = lang == 'ar' 
          ? 'باللغة العربية الفصحى الواضحة' 
          : 'in clear, simple English';

      final prompt = '''
قم بتلخيص النص الفقهي التالي إلى ثلاثة مستويات مختلفة:

النص الأصلي:
"$fullText"

المطلوب:
1. ملخص مختصر جداً (جملة واحدة فقط، لا تزيد عن 15 كلمة)
2. ملخص مبسط (3-4 أسطر، بأسلوب سهل للعامة)
3. النص التفصيلي مع الأهم (نفس النص الأصلي مع تنقيح خفيف)

أخرج النتيجة بهذا التنسيق:
==SHORT==
[الملخص المختصر جداً]
==SIMPLE==
[الملخص المبسط]
==DETAILED==
[النص التفصيلي]

قم بالكتابة $langInstruction
''';

      final response = await model.generateContent([Content.text(prompt)]);
      final result = response.text?.trim() ?? '';

      // استخراج الأجزاء
      String short = '';
      String simple = '';
      String detailed = '';

      final shortMatch = RegExp(r'==SHORT==\s*([\s\S]*?)(?====SIMPLE==|$)').firstMatch(result);
      if (shortMatch != null) short = shortMatch.group(1)?.trim() ?? '';

      final simpleMatch = RegExp(r'==SIMPLE==\s*([\s\S]*?)(?==DETAILED==|$)').firstMatch(result);
      if (simpleMatch != null) simple = simpleMatch.group(1)?.trim() ?? '';

      final detailedMatch = RegExp(r'==DETAILED==\s*([\s\S]*?)$').firstMatch(result);
      if (detailedMatch != null) detailed = detailedMatch.group(1)?.trim() ?? '';

      return SummaryResult(
        short: short.isNotEmpty ? short : 'لا يوجد ملخص مختصر',
        simple: simple.isNotEmpty ? simple : fullText,
        detailed: detailed.isNotEmpty ? detailed : fullText,
      );
    } catch (e) {
      return SummaryResult(
        short: 'خطأ في التلخيص',
        simple: fullText,
        detailed: fullText,
      );
    }
  }
}

class SummaryResult {
  final String short;
  final String simple;
  final String detailed;

  SummaryResult({
    required this.short,
    required this.simple,
    required this.detailed,
  });
}
