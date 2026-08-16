import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/issue_model.dart';
import '../models/comment_model.dart';
import '../providers/filter_provider.dart';
import '../providers/language_provider.dart';
import '../providers/search_provider.dart';
import 'contact_screen.dart';

class ResultScreen extends StatefulWidget {
  const ResultScreen({super.key});

  @override
  State<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends State<ResultScreen> {
  final TextEditingController _commentController = TextEditingController();
  double _rating = 0;
  String _commentType = 'suggestion';

  @override
  Widget build(BuildContext context) {
    final search = Provider.of<SearchProvider>(context);
    final filter = Provider.of<FilterProvider>(context);
    final lang = Provider.of<LanguageProvider>(context);
    final isRtl = lang.currentLocale.languageCode == 'ar' ||
        lang.currentLocale.languageCode == 'fa' ||
        lang.currentLocale.languageCode == 'ur';

    if (search.results.isEmpty) {
      return Scaffold(
        appBar: AppBar(title: Text(isRtl ? 'لا توجد نتائج' : 'No Results')),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                search.usingAI ? Icons.psychology : Icons.search_off,
                size: 64,
                color: Colors.grey,
              ),
              const SizedBox(height: 16),
              Text(
                search.searchMessage.isNotEmpty 
                    ? search.searchMessage
                    : isRtl
                        ? '🤔 لم أعثر على إجابة. حاول إعادة الصياغة.'
                        : '🤔 I couldn\'t find an answer. Try rephrasing.',
                style: const TextStyle(fontSize: 18),
                textAlign: TextAlign.center,
              ),
              if (search.confidence > 0 && search.confidence < 0.5)
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: LinearProgressIndicator(
                    value: search.confidence,
                    backgroundColor: Colors.grey.shade300,
                    color: Colors.orange,
                  ),
                ),
              const SizedBox(height: 20),
              ElevatedButton.icon(
                onPressed: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const ContactScreen()),
                  );
                },
                icon: const Icon(Icons.contact_mail),
                label: Text(isRtl ? '📩 تواصل مع فريق البحث' : '📩 Contact Research Team'),
              ),
            ],
          ),
        ),
      );
    }

    final issue = search.results.first;
    final filteredMadhabs = filter.getFilteredMadhabs();

    return Scaffold(
      appBar: AppBar(
        title: Text(issue.getTitle(lang.currentLocale.languageCode)),
      ),
      body: DefaultTabController(
        length: 3,
        child: Column(
          children: [
            // عرض نسبة الثقة (شريط صغير أعلى التبويبات)
            if (search.confidence > 0)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                color: search.confidence >= 0.8 
                    ? Colors.green.shade100 
                    : Colors.orange.shade100,
                child: Row(
                  children: [
                    Icon(
                      search.confidence >= 0.8 
                          ? Icons.verified 
                          : Icons.info_outline,
                      size: 16,
                      color: search.confidence >= 0.8 
                          ? Colors.green 
                          : Colors.orange,
                    ),
                    const SizedBox(width: 6),
                    Text(
                      '${isRtl ? 'الدقة' : 'Accuracy'}: ${(search.confidence * 100).toStringAsFixed(0)}%',
                      style: TextStyle(
                        fontSize: 12,
                        color: search.confidence >= 0.8 
                            ? Colors.green.shade700 
                            : Colors.orange.shade700,
                      ),
                    ),
                    const Spacer(),
                    Text(
                      search.usingAI 
                          ? (isRtl ? '🤖 بحث ذكي' : '🤖 AI Search') 
                          : (isRtl ? '📖 بحث نصي' : '📖 Text Search'),
                      style: const TextStyle(fontSize: 11, color: Colors.grey),
                    ),
                  ],
                ),
              ),
            // التبويبات
            TabBar(
              tabs: [
                Tab(
                  text: isRtl ? '⚡ مختصر جداً' : '⚡ Very Short',
                  icon: const Icon(Icons.lightbulb_outline),
                ),
                Tab(
                  text: isRtl ? '📖 مبسط' : '📖 Simple',
                  icon: const Icon(Icons.short_text),
                ),
                Tab(
                  text: isRtl ? '📚 موسع' : '📚 Detailed',
                  icon: const Icon(Icons.list_alt),
                ),
              ],
            ),
            Expanded(
              child: TabBarView(
                children: [
                  // تبويب 1: مختصر جداً
                  Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Text(
                          issue.getShortAnswer(lang.currentLocale.languageCode),
                          style: const TextStyle(fontSize: 18),
                        ),
                      ),
                    ),
                  ),
                  // تبويب 2: مبسط
                  Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Text(
                          issue.getSimpleAnswer(lang.currentLocale.languageCode),
                          style: const TextStyle(fontSize: 16),
                        ),
                      ),
                    ),
                  ),
                  // تبويب 3: موسع + ذكاء
                  ListView(
                    padding: const EdgeInsets.all(8.0),
                    children: [
                      // جدول المذاهب
                      ...filteredMadhabs.map((madhab) {
                        final view = issue.madhabViews.firstWhere(
                          (v) => v.madhabId == madhab.id,
                          orElse: () => MadhabView(
                            madhabId: madhab.id,
                            ruling: isRtl ? 'غير متوفر' : 'Not available',
                            detailTextAr: 'لا يوجد رأي مسجل.',
                            detailTextEn: 'No recorded opinion.',
                            detailTextFa: 'نظری ثبت نشده است.',
                            detailTextUr: 'کوئی رائے درج نہیں ہے۔',
                            detailTextId: 'Tidak ada pendapat yang tercatat.',
                            evidenceAr: '-',
                            evidenceEn: '-',
                            evidenceFa: '-',
                            evidenceUr: '-',
                            evidenceId: '-',
                          ),
                        );

                        return Card(
                          margin: const EdgeInsets.symmetric(vertical: 6.0),
                          color: madhab.color.withOpacity(0.1),
                          child: ListTile(
                            title: Text(
                              madhab.getName(lang.currentLocale.languageCode),
                              style: TextStyle(
                                color: madhab.color,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            subtitle: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const SizedBox(height: 4),
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 8,
                                    vertical: 2,
                                  ),
                                  decoration: BoxDecoration(
                                    color: madhab.color,
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                  child: Text(
                                    view.ruling,
                                    style: const TextStyle(
                                      color: Colors.white,
                                      fontSize: 12,
                                    ),
                                  ),
                                ),
                                const SizedBox(height: 6),
                                Text(view.getDetailText(lang.currentLocale.languageCode)),
                                Text(
                                  '📖 ${view.getEvidence(lang.currentLocale.languageCode)}',
                                  style: const TextStyle(
                                    fontSize: 12,
                                    color: Colors.grey,
                                  ),
                                ),
                              ],
                            ),
                            leading: CircleAvatar(
                              backgroundColor: madhab.color,
                              child: Icon(madhab.icon, color: Colors.white),
                            ),
                          ),
                        );
                      }).toList(),

                      const Divider(height: 30, color: Colors.amber),

                      // ===== التوصيات الذكية =====
                      if (search.recommendations.isNotEmpty)
                        Padding(
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Row(
                                children: [
                                  Icon(Icons.recommend, color: Colors.green.shade700),
                                  const SizedBox(width: 8),
                                  Text(
                                    isRtl 
                                        ? '📌 قد تهمك هذه المسائل أيضاً' 
                                        : '📌 You might also be interested in',
                                    style: const TextStyle(
                                      fontSize: 16,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 8),
                              ...search.recommendations.take(3).map((recommendation) {
                                return Card(
                                  margin: const EdgeInsets.symmetric(vertical: 4),
                                  child: ListTile(
                                    leading: const Icon(Icons.trending_up, color: Colors.blue),
                                    title: Text(
                                      recommendation.getTitle(lang.currentLocale.languageCode),
                                      style: const TextStyle(fontSize: 14),
                                    ),
                                    trailing: const Icon(Icons.arrow_forward, size: 16),
                                    onTap: () {
                                      search.smartSearch(
                                        recommendation.getTitle(lang.currentLocale.languageCode),
                                        lang.currentLocale.languageCode,
                                      );
                                      Navigator.pushReplacement(
                                        context,
                                        MaterialPageRoute(builder: (_) => const ResultScreen()),
                                      );
                                    },
                                  ),
                                );
                              }),
                            ],
                          ),
                        ),

                      const Divider(height: 30, color: Colors.amber),

                      // ===== التقييم والتعليقات الذكية =====
                      Padding(
                        padding: const EdgeInsets.all(12.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              isRtl ? '⭐ قيم فائدة هذه الصفحة' : '⭐ Rate the usefulness of this page',
                              style: const TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            Row(
                              children: List.generate(5, (index) {
                                return IconButton(
                                  onPressed: () {
                                    setState(() {
                                      _rating = (index + 1).toDouble();
                                    });
                                    ScaffoldMessenger.of(context).showSnackBar(
                                      SnackBar(
                                        content: Text(
                                          isRtl
                                              ? 'شكراً لتقييمك (${_rating} نجوم)'
                                              : 'Thank you for your rating (${_rating} stars)',
                                        ),
                                      ),
                                    );
                                  },
                                  icon: Icon(
                                    index < _rating ? Icons.star : Icons.star_border,
                                    color: Colors.amber,
                                    size: 30,
                                  ),
                                );
                              }),
                            ),
                            const SizedBox(height: 16),

                            Text(
                              isRtl ? '📝 أضف تعليقك أو اقتراحك' : '📝 Add your comment or suggestion',
                              style: const TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const SizedBox(height: 8),
                            DropdownButtonFormField<String>(
                              value: _commentType,
                              items: [
                                DropdownMenuItem(
                                  value: 'suggestion',
                                  child: Text(isRtl ? '➕ اقتراح مسألة جديدة' : '➕ Suggest new issue'),
                                ),
                                DropdownMenuItem(
                                  value: 'correction',
                                  child: Text(isRtl ? '📚 ملاحظة على المصدر' : '📚 Source note'),
                                ),
                                DropdownMenuItem(
                                  value: 'appreciation',
                                  child: Text(isRtl ? '💡 شكر أو تعليق عام' : '💡 Appreciation or general comment'),
                                ),
                                DropdownMenuItem(
                                  value: 'other',
                                  child: Text(isRtl ? '📝 أخرى' : '📝 Other'),
                                ),
                              ],
                              onChanged: (value) => setState(() => _commentType = value!),
                              decoration: InputDecoration(
                                labelText: isRtl ? 'نوع التعليق' : 'Comment type',
                              ),
                            ),
                            const SizedBox(height: 8),
                            TextField(
                              controller: _commentController,
                              maxLines: 3,
                              decoration: InputDecoration(
                                hintText: isRtl
                                    ? 'اكتب تعليقك العلمي هنا... (سيتم تحليل مشاعره ذكياً)'
                                    : 'Write your scientific comment here... (Sentiment will be analyzed)',
                                border: OutlineInputBorder(
                                  borderRadius: BorderRadius.circular(12),
                                ),
                              ),
                            ),
                            const SizedBox(height: 12),
                            SizedBox(
                              width: double.infinity,
                              child: ElevatedButton(
                                onPressed: () async {
                                  if (_commentController.text.trim().isEmpty) {
                                    ScaffoldMessenger.of(context).showSnackBar(
                                      SnackBar(
                                        content: Text(
                                          isRtl
                                              ? '⚠️ الرجاء كتابة تعليقك قبل الإرسال'
                                              : '⚠️ Please write your comment before submitting',
                                        ),
                                      ),
                                    );
                                    return;
                                  }

                                  // تحليل المشاعر باستخدام الذكاء الاصطناعي
                                  final sentiment = await search.analyzeComment(
                                    _commentController.text.trim(),
                                    lang.currentLocale.languageCode,
                                  );

                                  final comment = CommentModel(
                                    id: DateTime.now().millisecondsSinceEpoch.toString(),
                                    issueId: issue.id,
                                    userName: 'مستخدم',
                                    commentText: _commentController.text.trim(),
                                    rating: _rating,
                                    type: _commentType,
                                    timestamp: DateTime.now(),
                                    isApproved: false,
                                  );

                                  setState(() {
                                    _commentController.clear();
                                    _rating = 0;
                                  });

                                  // عرض نتيجة تحليل المشاعر مع رسالة مميزة
                                  String moodIcon = '😊';
                                  if (sentiment.sentiment.contains('إيجابي') || sentiment.sentiment.contains('Positive')) {
                                    moodIcon = '😊';
                                  } else if (sentiment.sentiment.contains('سلبي') || sentiment.sentiment.contains('Negative')) {
                                    moodIcon = '😔';
                                  } else {
                                    moodIcon = '😐';
                                  }

                                  ScaffoldMessenger.of(context).showSnackBar(
                                    SnackBar(
                                      content: Column(
                                        mainAxisSize: MainAxisSize.min,
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          Text(
                                            isRtl
                                                ? '✅ تم إرسال تعليقك!'
                                                : '✅ Your comment has been submitted!',
                                          ),
                                          Text(
                                            '$moodIcon ${isRtl ? "تحليل المشاعر: $moodIcon" : "Sentiment: $moodIcon"} ${sentiment.sentiment} (${(sentiment.score * 100).toStringAsFixed(0)}%)',
                                            style: const TextStyle(fontSize: 12),
                                          ),
                                        ],
                                      ),
                                      duration: const Duration(seconds: 4),
                                    ),
                                  );
                                },
                                child: Text(isRtl ? 'إرسال التعليق (مع تحليل ذكي)' : 'Submit Comment (Smart Analysis)'),
                              ),
                            ),
                            const SizedBox(height: 8),
                            Container(
                              padding: const EdgeInsets.all(8),
                              decoration: BoxDecoration(
                                color: Colors.grey.shade100,
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Text(
                                isRtl
                                    ? '🕊️ هذه مساحة للتغذية الراجعة العلمية. سيتم تحليل تعليقك ذكياً لفهم المشاعر العامة.'
                                    : '🕊️ This is a space for scientific feedback. Your comment will be analyzed intelligently.',
                                style: const TextStyle(fontSize: 12, color: Colors.grey),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
