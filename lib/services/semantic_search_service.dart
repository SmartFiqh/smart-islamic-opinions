import 'package:google_generative_ai/google_generative_ai.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import '../models/issue_model.dart';

class SemanticSearchService {
  static String? _apiKey;

  static Future<void> init() async {
    await dotenv.load(fileName: '.env');
    _apiKey = dotenv.env['GEMINI_API_KEY'];
  }

  /// بحث دلالي باستخدام الذكاء الاصطناعي مع نسبة ثقة
  static Future<SearchResult> semanticSearch(
    String userQuery,
    List<IssueModel> issues,
    String lang,
  ) async {
    if (_apiKey == null || _apiKey!.isEmpty) {
      return SearchResult(
        matchedIssue: null,
        confidence: 0.0,
        message: 'API key not configured',
      );
    }

    try {
      final model = GenerativeModel(
        model: 'gemini-1.5-flash',
        apiKey: _apiKey!,
      );

      // بناء قائمة المسائل مع معرفاتها
      final issuesList = issues.asMap().entries.map((entry) {
        final index = entry.key;
        final issue = entry.value;
        return '[$index] ${issue.getTitle(lang)}';
      }).join('\n');

      final prompt = '''
أنت محرك بحث دلالي ذكي لتطبيق فقهي اسمه "الجامع الذكي لآراء المذاهب الإسلامية".

قائمة المسائل المتوفرة (مع أرقامها):
$issuesList

سؤال المستخدم: "$userQuery"

مطلوب منك:
1. تحليل سؤال المستخدم وفهم المعنى الحقيقي للسؤال (وليس مجرد كلمات).
2. مقارنته مع قائمة المسائل المتوفرة.
3. تحديد درجة التطابق كنسبة مئوية (0-100).

قم بالرد بهذا التنسيق الدقيق:
{
  "matched_index": [رقم المسألة المتطابقة أو -1],
  "confidence": [نسبة التطابق 0-100],
  "reason": [سبب مختصر للاختيار]
}

قواعد مهمة:
- إذا كانت نسبة التطابق أقل من 50، اعتبرها غير متطابقة وضع matched_index = -1.
- لا تفتِ من عندك، فقط طابق بين السؤال والمسائل الموجودة.
- كن دقيقاً في تحليل المعنى، وليس فقط الكلمات.
- إذا كان السؤال عاماً جداً، اختر أقرب مسألة وقلل نسبة الثقة.
''';

      final response = await model.generateContent([Content.text(prompt)]);
      final resultText = response.text?.trim() ?? '';

      // استخراج JSON من الرد
      try {
        final jsonStart = resultText.indexOf('{');
        final jsonEnd = resultText.lastIndexOf('}') + 1;
        final jsonStr = resultText.substring(jsonStart, jsonEnd);
        final Map<String, dynamic> jsonData = Map.from(jsonDecode(jsonStr));

        final matchedIndex = jsonData['matched_index'] as int? ?? -1;
        final confidence = (jsonData['confidence'] as num?)?.toDouble() ?? 0.0;
        final reason = jsonData['reason'] as String? ?? '';

        if (matchedIndex >= 0 && matchedIndex < issues.length && confidence >= 50) {
          return SearchResult(
            matchedIssue: issues[matchedIndex],
            confidence: confidence / 100,
            message: reason,
          );
        } else {
          return SearchResult(
            matchedIssue: null,
            confidence: confidence / 100,
            message: reason.isNotEmpty ? reason : 'لم يتم العثور على تطابق كافٍ',
          );
        }
      } catch (e) {
        // محاولة استخراج النتيجة بطريقة بديلة
        return SearchResult(
          matchedIssue: null,
          confidence: 0.0,
          message: 'تعذر تحليل نتيجة البحث',
        );
      }
    } catch (e) {
      return SearchResult(
        matchedIssue: null,
        confidence: 0.0,
        message: 'خطأ في البحث: $e',
      );
    }
  }
}

// نتيجة البحث
class SearchResult {
  final IssueModel? matchedIssue;
  final double confidence; // 0.0 - 1.0
  final String message;

  SearchResult({
    this.matchedIssue,
    required this.confidence,
    required this.message,
  });

  bool get isMatch => matchedIssue != null && confidence >= 0.5;
  bool get isExactMatch => matchedIssue != null && confidence >= 0.8;
  bool get isPartialMatch => matchedIssue != null && confidence >= 0.5 && confidence < 0.8;
}
