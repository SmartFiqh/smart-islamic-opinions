import 'package:google_generative_ai/google_generative_ai.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

class AnalyticsService {
  static String? _apiKey;

  static Future<void> init() async {
    await dotenv.load(fileName: '.env');
    _apiKey = dotenv.env['GEMINI_API_KEY'];
  }

  /// تحليل مشاعر التعليق (إيجابي، محايد، سلبي)
  static Future<SentimentResult> analyzeSentiment(String commentText, String lang) async {
    if (_apiKey == null || _apiKey!.isEmpty) {
      return SentimentResult(sentiment: 'محايد', score: 0.5, keywords: []);
    }

    try {
      final model = GenerativeModel(
        model: 'gemini-1.5-flash',
        apiKey: _apiKey!,
      );

      final prompt = '''
حلل المشاعر في التعليق التالي وحدد:
1. المشاعر العامة (إيجابي / محايد / سلبي)
2. درجة المشاعر من 0 إلى 1 (0 سلبي جداً، 0.5 محايد، 1 إيجابي جداً)
3. الكلمات المفتاحية الرئيسية (لا تزيد عن 5)

التعليق: "$commentText"

أخرج النتيجة بهذا التنسيق:
SENTIMENT: [إيجابي/محايد/سلبي]
SCORE: [رقم من 0 إلى 1]
KEYWORDS: [كلمة1، كلمة2، كلمة3]
''';

      final response = await model.generateContent([Content.text(prompt)]);
      final result = response.text?.trim() ?? '';

      // استخراج البيانات
      String sentiment = 'محايد';
      double score = 0.5;
      List<String> keywords = [];

      final sentimentMatch = RegExp(r'SENTIMENT:\s*(.+)').firstMatch(result);
      if (sentimentMatch != null) {
        final raw = sentimentMatch.group(1)?.trim() ?? '';
        if (raw.contains('إيجابي') || raw.contains('Positive')) sentiment = 'إيجابي';
        else if (raw.contains('سلبي') || raw.contains('Negative')) sentiment = 'سلبي';
        else sentiment = 'محايد';
      }

      final scoreMatch = RegExp(r'SCORE:\s*([\d.]+)').firstMatch(result);
      if (scoreMatch != null) {
        score = double.tryParse(scoreMatch.group(1) ?? '0.5') ?? 0.5;
      }

      final keywordsMatch = RegExp(r'KEYWORDS:\s*(.+)').firstMatch(result);
      if (keywordsMatch != null) {
        keywords = keywordsMatch.group(1)
            ?.split(',')
            .map((k) => k.trim())
            .where((k) => k.isNotEmpty)
            .toList() ?? [];
      }

      return SentimentResult(
        sentiment: sentiment,
        score: score.clamp(0.0, 1.0),
        keywords: keywords,
      );
    } catch (e) {
      return SentimentResult(sentiment: 'محايد', score: 0.5, keywords: []);
    }
  }

  /// توليد توصيات ذكية بناءً على سجل المستخدم
  static Future<List<IssueModel>> getSmartRecommendations(
    List<IssueModel> allIssues,
    List<String> userHistory, // عناوين المسائل التي شاهدها المستخدم
    String lang,
  ) async {
    if (_apiKey == null || _apiKey!.isEmpty) {
      // إذا لم يكن هناك API، أرجع أول 3 مسائل كتوصية
      return allIssues.take(3).toList();
    }

    try {
      final model = GenerativeModel(
        model: 'gemini-1.5-flash',
        apiKey: _apiKey!,
      );

      final issuesList = allIssues.map((i) => i.getTitle(lang)).join('\n');
      final historyList = userHistory.join(', ');

      final prompt = '''
بناءً على تاريخ مشاهدات المستخدم (المسائل التي شاهدها)، اقترح له 3 مسائل جديدة قد تهمه.

تاريخ المشاهدات: $historyList

قائمة جميع المسائل المتوفرة:
$issuesList

المطلوب:
- اختر 3 مسائل لم يشاهدها المستخدم بعد.
- رتبها حسب الأكثر صلة باهتماماته.
- أعد فقط عناوين المسائل الثلاثة، كل عنوان في سطر منفصل.
''';

      final response = await model.generateContent([Content.text(prompt)]);
      final result = response.text?.trim() ?? '';

      final recommendedTitles = result
          .split('\n')
          .map((line) => line.trim())
          .where((line) => line.isNotEmpty)
          .toList();

      // إيجاد المسائل المطابقة للعناوين الموصى بها
      final recommendations = <IssueModel>[];
      for (final title in recommendedTitles) {
        final found = allIssues.firstWhere(
          (issue) => issue.getTitle(lang) == title,
          orElse: () => allIssues.first,
        );
        if (!recommendations.contains(found)) {
          recommendations.add(found);
        }
      }

      return recommendations.take(3).toList();
    } catch (e) {
      // في حالة الخطأ، أرجع أول 3 مسائل
      return allIssues.take(3).toList();
    }
  }
}

class SentimentResult {
  final String sentiment; // إيجابي، محايد، سلبي
  final double score; // 0-1
  final List<String> keywords;

  SentimentResult({
    required this.sentiment,
    required this.score,
    required this.keywords,
  });
}
