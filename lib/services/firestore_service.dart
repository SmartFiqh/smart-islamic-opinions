import 'package:google_generative_ai/google_generative_ai.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

class AIService {
  static String? _apiKey;

  static Future<void> init() async {
    await dotenv.load(fileName: '.env');
    _apiKey = dotenv.env['GEMINI_API_KEY'];
  }

  static Future<String> findBestMatch(String userQuery, List<String> issueTitles) async {
    if (_apiKey == null || _apiKey!.isEmpty) {
      return 'UNKNOWN';
    }

    try {
      final model = GenerativeModel(
        model: 'gemini-1.5-flash',
        apiKey: _apiKey!,
      );

      final prompt = '''
أنت مساعد فقهي دقيق. دورك هو مقارنة سؤال المستخدم بقائمة المسائل المتوفرة لدينا.

قائمة المسائل المتوفرة:
${issueTitles.join('\n')}

سؤال المستخدم: "$userQuery"

مطلوب:
1. إذا كان السؤال يطابق إحدى المسائل بنسبة عالية، أعد فقط عنوان المسئلة المطابقة.
2. إذا لم يطابق أي مسئلة، أعد كلمة "UNKNOWN" فقط.

لا تفتِ من عندك، فقط صنف السؤال.
''';

      final response = await model.generateContent([Content.text(prompt)]);
      return response.text?.trim() ?? 'UNKNOWN';
    } catch (e) {
      return 'UNKNOWN';
    }
  }
}
