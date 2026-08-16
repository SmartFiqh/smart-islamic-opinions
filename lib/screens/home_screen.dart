import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/search_provider.dart';
import '../providers/filter_provider.dart';
import '../providers/language_provider.dart';
import '../models/issue_model.dart';
import '../core/responsive.dart';
import 'result_screen.dart';
import 'imams_screen.dart';
import 'geography_screen.dart';
import 'glossary_screen.dart';
import 'contact_screen.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final search = Provider.of<SearchProvider>(context);
    final filter = Provider.of<FilterProvider>(context);
    final lang = Provider.of<LanguageProvider>(context);
    final isRtl = lang.currentLocale.languageCode == 'ar' ||
        lang.currentLocale.languageCode == 'fa' ||
        lang.currentLocale.languageCode == 'ur';

    // على الديسكتوب: نعرض المسائل التجريبية في شبكة عمودين+ بدل قائمة طويلة
    final wide = isDesktop(context) || isTablet(context);
    final mockIssues = IssueModel.getMockIssues();

    return Scaffold(
      appBar: AppBar(
        title: Text(isRtl ? 'الرئيسية' : 'Home'),
        actions: [
          IconButton(
            onPressed: () => _showSettingsDialog(context),
            icon: const Icon(Icons.settings),
          ),
        ],
      ),
      drawer: Drawer(
        child: ListView(
          padding: EdgeInsets.zero,
          children: [
            DrawerHeader(
              decoration: const BoxDecoration(color: Color(0xFF1B5E20)),
              child: Text(
                isRtl ? 'القائمة' : 'Menu',
                style: const TextStyle(color: Colors.white, fontSize: 24),
              ),
            ),
            ListTile(
              leading: const Icon(Icons.history_edu),
              title: Text(isRtl ? '📜 الأئمة المؤسسون' : '📜 Founding Imams'),
              onTap: () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const ImamsScreen()),
              ),
            ),
            ListTile(
              leading: const Icon(Icons.map),
              title: Text(isRtl ? '🗺️ انتشار المذاهب' : '🗺️ Madhhab Geography'),
              onTap: () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const GeographyScreen()),
              ),
            ),
            ListTile(
              leading: const Icon(Icons.book),
              title: Text(isRtl ? '📚 قاموس المصطلحات' : '📚 Glossary'),
              onTap: () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const GlossaryScreen()),
              ),
            ),
            ListTile(
              leading: const Icon(Icons.contact_mail),
              title: Text(isRtl ? '📩 تواصل معنا' : '📩 Contact Us'),
              onTap: () => Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const ContactScreen()),
              ),
            ),
          ],
        ),
      ),
      body: ResponsiveCenter(
        maxWidth: 1000,
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            children: [
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      onChanged: (value) => search.updateQuery(value),
                      decoration: InputDecoration(
                        hintText: isRtl
                            ? 'ابحث عن مسألة... (مثال: صلاة الجماعة)'
                            : 'Search for an issue... (e.g., congregational prayer)',
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(30)),
                        prefixIcon: const Icon(Icons.search),
                      ),
                      onSubmitted: (value) async {
                        await search.search(value, lang.currentLocale.languageCode);
                        if (!context.mounted) return;
                        if (search.results.isNotEmpty) {
                          Navigator.push(
                            context,
                            MaterialPageRoute(builder: (_) => const ResultScreen()),
                          );
                        } else {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text(
                                isRtl
                                    ? '🤔 لا أعلم (عفواً). لم أعثر على إجابة. هل تريد طرح سؤالك على فريق البحث؟'
                                    : '🤔 I don\'t know. I couldn\'t find an answer. Want to ask our research team?',
                              ),
                              duration: const Duration(seconds: 5),
                              action: SnackBarAction(
                                label: isRtl ? '📩 تواصل' : '📩 Contact',
                                onPressed: () {
                                  Navigator.push(
                                    context,
                                    MaterialPageRoute(builder: (_) => const ContactScreen()),
                                  );
                                },
                              ),
                            ),
                          );
                        }
                      },
                    ),
                  ),
                  IconButton(onPressed: () {}, icon: const Icon(Icons.mic)),
                ],
              ),
              const SizedBox(height: 16),
              SizedBox(
                height: 50,
                child: ListView(
                  scrollDirection: Axis.horizontal,
                  children: [
                    _buildCategoryChip(isRtl ? '🧼 الطهارة' : '🧼 Purification'),
                    _buildCategoryChip(isRtl ? '🕌 الصلاة' : '🕌 Prayer'),
                    _buildCategoryChip(isRtl ? '💰 الزكاة' : '💰 Zakat'),
                    _buildCategoryChip(isRtl ? '🌙 الصوم' : '🌙 Fasting'),
                    _buildCategoryChip(isRtl ? '🕋 الحج' : '🕋 Hajj'),
                    _buildCategoryChip(isRtl ? '🏦 المعاملات' : '🏦 Transactions'),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              Expanded(
                child: SingleChildScrollView(
                  child: wide
                      ? ResponsiveGrid(
                          children: mockIssues
                              .map((issue) => _IssueCard(issue: issue, isRtl: isRtl, lang: lang.currentLocale.languageCode))
                              .toList(),
                        )
                      : Column(
                          children: mockIssues
                              .map((issue) => _IssueCard(issue: issue, isRtl: isRtl, lang: lang.currentLocale.languageCode))
                              .toList(),
                        ),
                ),
              ),
              Text(
                '${isRtl ? 'الفلتر الحالي:' : 'Current filter:'} ${filter.getCurrentGroupName(lang.currentLocale.languageCode)}',
                style: const TextStyle(color: Colors.grey),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildCategoryChip(String label) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 4.0),
      child: ActionChip(label: Text(label), onPressed: () {}),
    );
  }

  void _showSettingsDialog(BuildContext context) {
    // يمكنك تنفيذ مربع حوار لتغيير اللغة والفلتر بسرعة
  }
}

class _IssueCard extends StatelessWidget {
  final IssueModel issue;
  final bool isRtl;
  final String lang;

  const _IssueCard({required this.issue, required this.isRtl, required this.lang});

  @override
  Widget build(BuildContext context) {
    final search = Provider.of<SearchProvider>(context, listen: false);
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 6),
      child: ListTile(
        title: Text(issue.getTitle(lang)),
        subtitle: Text(isRtl ? 'اضغط لعرض آراء المذاهب' : 'Tap to view schools\' views'),
        trailing: const Icon(Icons.arrow_forward_ios),
        onTap: () {
          search.updateQuery(issue.getTitle(lang));
          search.search(issue.getTitle(lang), lang);
          Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const ResultScreen()),
          );
        },
      ),
    );
  }
}
