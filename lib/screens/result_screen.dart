import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/issue_model.dart';
import '../models/comment_model.dart';
import '../providers/filter_provider.dart';
import '../providers/language_provider.dart';
import '../providers/search_provider.dart';

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
              Text(
                isRtl
                    ? '🤔 لا أعلم (عفواً). لم أعثر على إجابة. حاول إعادة الصياغة.'
                    : '🤔 I don\'t know. I couldn\'t find an answer.',
                style: const TextStyle(fontSize: 18),
                textAlign: TextAlign.center,
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
                  // تبويب 3: موسع (جدول المذاهب + التقييم والتعليق)
                  ListView(
                    padding: const EdgeInsets.all(8.0),
                    children: [
                      // عرض آراء المذاهب المُصفاة
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

                      // ==== مساحة التقييم والتعليقات (غير المباشرة) ====
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
                                    ? 'اكتب تعليقك العلمي هنا... (سيتم مراجعته قبل النشر)'
                                    : 'Write your scientific comment here... (Will be reviewed before publishing)',
                                border: OutlineInputBorder(
                                  borderRadius: BorderRadius.circular(12),
                                ),
                              ),
                            ),
                            const SizedBox(height: 12),
                            SizedBox(
                              width: double.infinity,
                              child: ElevatedButton(
                                onPressed: () {
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
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    SnackBar(
                                      content: Text(
                                        isRtl
                                            ? '✅ شكراً! سيتم مراجعة تعليقك ونشره بعد الموافقة عليه.'
                                            : '✅ Thank you! Your comment will be reviewed and published after approval.',
                                      ),
                                      duration: const Duration(seconds: 3),
                                    ),
                                  );
                                },
                                child: Text(isRtl ? 'إرسال التعليق' : 'Submit Comment'),
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
                                    ? '🕊️ هذه مساحة للتغذية الراجعة العلمية فقط. يُمنع التعصب أو التجريح بالمذاهب. جميع التعليقات تخضع للمراجعة المسبقة.'
                                    : '🕊️ This is a space for scientific feedback only. Sectarian intolerance or defamation is prohibited. All comments are subject to pre-moderation.',
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
