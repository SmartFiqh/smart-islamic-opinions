import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart'; // يجب إضافتها في pubspec.yaml: url_launcher: ^6.2.0
import '../providers/language_provider.dart';

class ContactScreen extends StatefulWidget {
  const ContactScreen({super.key});

  @override
  State<ContactScreen> createState() => _ContactScreenState();
}

class _ContactScreenState extends State<ContactScreen> {
  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _questionController = TextEditingController();
  String _selectedType = 'suggestion';

  @override
  Widget build(BuildContext context) {
    final lang = Provider.of<LanguageProvider>(context);
    final isRtl = lang.currentLocale.languageCode == 'ar' ||
        lang.currentLocale.languageCode == 'fa' ||
        lang.currentLocale.languageCode == 'ur';

    return Scaffold(
      appBar: AppBar(
        title: Text(isRtl ? '📩 تواصل معنا' : '📩 Contact Us'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // إشعار مهم بعدم الإفتاء الفوري
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.amber.shade50,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.amber.shade200),
              ),
              child: Row(
                children: [
                  Icon(Icons.info_outline, color: Colors.amber.shade800),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      isRtl
                          ? '🕊️ هذا نموذج تواصل غير مباشر. سيتم دراسة استفسارك من قبل فريق البحث، والرد عليك عبر البريد الإلكتروني خلال 3-5 أيام عمل (هذه ليست دردشة فورية).'
                          : '🕊️ This is an indirect contact form. Your inquiry will be studied by the research team and replied to via email within 3-5 business days (this is not instant chat).',
                      style: TextStyle(fontSize: 13, color: Colors.amber.shade800),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // حقل الاسم
            TextField(
              controller: _nameController,
              decoration: InputDecoration(
                labelText: isRtl ? 'الاسم الكامل' : 'Full Name',
                prefixIcon: const Icon(Icons.person),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
            const SizedBox(height: 16),

            // حقل البريد الإلكتروني
            TextField(
              controller: _emailController,
              keyboardType: TextInputType.emailAddress,
              decoration: InputDecoration(
                labelText: isRtl ? 'البريد الإلكتروني (للرد)' : 'Email (for reply)',
                prefixIcon: const Icon(Icons.email),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                hintText: 'example@domain.com',
              ),
            ),
            const SizedBox(height: 16),

            // نوع الاستفسار
            DropdownButtonFormField<String>(
              value: _selectedType,
              items: [
                DropdownMenuItem(
                  value: 'suggestion',
                  child: Text(isRtl ? '➕ اقتراح مسألة جديدة' : '➕ Suggest new issue'),
                ),
                DropdownMenuItem(
                  value: 'question',
                  child: Text(isRtl ? '❓ استفسار عن مسألة موجودة' : '❓ Question about existing issue'),
                ),
                DropdownMenuItem(
                  value: 'correction',
                  child: Text(isRtl ? '📚 تصحيح مصدر أو معلومة' : '📚 Correction of source or info'),
                ),
                DropdownMenuItem(
                  value: 'technical',
                  child: Text(isRtl ? '⚙️ مشكلة تقنية' : '⚙️ Technical issue'),
                ),
                DropdownMenuItem(
                  value: 'other',
                  child: Text(isRtl ? '📝 أخرى' : '📝 Other'),
                ),
              ],
              onChanged: (value) => setState(() => _selectedType = value!),
              decoration: InputDecoration(
                labelText: isRtl ? 'نوع الاستفسار' : 'Inquiry type',
                prefixIcon: const Icon(Icons.category),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
            const SizedBox(height: 16),

            // حقل السؤال الطويل
            TextField(
              controller: _questionController,
              maxLines: 6,
              decoration: InputDecoration(
                labelText: isRtl ? 'تفاصيل سؤالك أو اقتراحك' : 'Your question or suggestion details',
                prefixIcon: const Icon(Icons.edit),
                alignLabelWithHint: true,
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                hintText: isRtl
                    ? 'اكتب سؤالك هنا... (كلما كان أكثر تفصيلاً، كانت إجابتنا أدق)'
                    : 'Write your question here... (The more detailed, the more accurate our reply)',
              ),
            ),
            const SizedBox(height: 24),

            // زر الإرسال
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () async {
                  // التحقق من الحقول
                  if (_nameController.text.trim().isEmpty ||
                      _emailController.text.trim().isEmpty ||
                      _questionController.text.trim().isEmpty) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text(isRtl
                            ? '⚠️ الرجاء ملء جميع الحقول الأساسية'
                            : '⚠️ Please fill in all required fields'),
                        backgroundColor: Colors.red,
                      ),
                    );
                    return;
                  }

                  // بناء نص البريد الإلكتروني
                  final subject = 'استفسار من التطبيق: $_selectedType';
                  final body = '''
الاسم: ${_nameController.text.trim()}
البريد الإلكتروني: ${_emailController.text.trim()}
نوع الاستفسار: $_selectedType

السؤال / الاقتراح:
${_questionController.text.trim()}

--- 
تم الإرسال من تطبيق "الجامع الذكي لآراء المذاهب الإسلامية"
''';

                  // فتح البريد الإلكتروني (Gmail أو أي تطبيق بريد)
                  final Uri emailUri = Uri(
                    scheme: 'mailto',
                    path: 'info@aljame3alzhaki.com',
                    queryParameters: {
                      'subject': subject,
                      'body': body,
                    },
                  );

                  try {
                    if (await canLaunchUrl(emailUri)) {
                      await launchUrl(emailUri);
                      // إفراغ الحقول بعد الإرسال
                      _nameController.clear();
                      _emailController.clear();
                      _questionController.clear();
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: Text(isRtl
                              ? '✅ تم فتح تطبيق البريد الإلكتروني. الرجاء الضغط على إرسال لإكمال العملية.'
                              : '✅ Email app opened. Please press send to complete.'),
                          duration: const Duration(seconds: 4),
                        ),
                      );
                    } else {
                      // في حال لم يكن هناك تطبيق بريد
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: Text(isRtl
                              ? '⚠️ لا يوجد تطبيق بريد إلكتروني مثبت. الرجاء إرسال بريد يدوياً إلى info@aljame3alzhaki.com'
                              : '⚠️ No email app installed. Please manually send to info@aljame3alzhaki.com'),
                          backgroundColor: Colors.orange,
                        ),
                      );
                    }
                  } catch (e) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text('Error: $e'),
                        backgroundColor: Colors.red,
                      ),
                    );
                  }
                },
                icon: const Icon(Icons.send),
                label: Text(isRtl ? 'إرسال الاستفسار' : 'Send Inquiry'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF1B5E20),
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
              ),
            ),
            const SizedBox(height: 16),
            Center(
              child: Text(
                isRtl
                    ? '📧 سيتم الرد على بريدك الإلكتروني خلال 3-5 أيام عمل'
                    : '📧 We will reply to your email within 3-5 business days',
                style: const TextStyle(fontSize: 12, color: Colors.grey),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
