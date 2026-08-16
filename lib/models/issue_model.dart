import 'madhhab_model.dart';

class MadhabView {
  final String madhabId;
  final String ruling;
  final String detailTextAr, detailTextEn, detailTextFa, detailTextUr, detailTextId;
  final String evidenceAr, evidenceEn, evidenceFa, evidenceUr, evidenceId;

  MadhabView({
    required this.madhabId,
    required this.ruling,
    required this.detailTextAr,
    required this.detailTextEn,
    required this.detailTextFa,
    required this.detailTextUr,
    required this.detailTextId,
    required this.evidenceAr,
    required this.evidenceEn,
    required this.evidenceFa,
    required this.evidenceUr,
    required this.evidenceId,
  });

  String getDetailText(String lang) {
    switch (lang) {
      case 'en': return detailTextEn;
      case 'fa': return detailTextFa;
      case 'ur': return detailTextUr;
      case 'id': return detailTextId;
      default: return detailTextAr;
    }
  }

  String getEvidence(String lang) {
    switch (lang) {
      case 'en': return evidenceEn;
      case 'fa': return evidenceFa;
      case 'ur': return evidenceUr;
      case 'id': return evidenceId;
      default: return evidenceAr;
    }
  }

  // ---- إضافة: تحويل من/إلى Firestore (لا تغيّر أي شيء في الحقول أعلاه) ----
  Map<String, dynamic> toMap() => {
        'madhabId': madhabId,
        'ruling': ruling,
        'detailTextAr': detailTextAr,
        'detailTextEn': detailTextEn,
        'detailTextFa': detailTextFa,
        'detailTextUr': detailTextUr,
        'detailTextId': detailTextId,
        'evidenceAr': evidenceAr,
        'evidenceEn': evidenceEn,
        'evidenceFa': evidenceFa,
        'evidenceUr': evidenceUr,
        'evidenceId': evidenceId,
      };

  factory MadhabView.fromMap(Map<String, dynamic> map) => MadhabView(
        madhabId: map['madhabId'] ?? '',
        ruling: map['ruling'] ?? '',
        detailTextAr: map['detailTextAr'] ?? '',
        detailTextEn: map['detailTextEn'] ?? '',
        detailTextFa: map['detailTextFa'] ?? '',
        detailTextUr: map['detailTextUr'] ?? '',
        detailTextId: map['detailTextId'] ?? '',
        evidenceAr: map['evidenceAr'] ?? '-',
        evidenceEn: map['evidenceEn'] ?? '-',
        evidenceFa: map['evidenceFa'] ?? '-',
        evidenceUr: map['evidenceUr'] ?? '-',
        evidenceId: map['evidenceId'] ?? '-',
      );
}

class IssueModel {
  final String id;
  final String titleAr, titleEn, titleFa, titleUr, titleId;
  final String shortAnswerAr, shortAnswerEn, shortAnswerFa, shortAnswerUr, shortAnswerId;
  final String simpleAnswerAr, simpleAnswerEn, simpleAnswerFa, simpleAnswerUr, simpleAnswerId;
  final List<MadhabView> madhabViews;
  final List<String> category;
  final int views; // إضافة: يُستخدم في إحصائيات لوحة Streamlit، افتراضيه 0

  IssueModel({
    required this.id,
    required this.titleAr,
    required this.titleEn,
    required this.titleFa,
    required this.titleUr,
    required this.titleId,
    required this.shortAnswerAr,
    required this.shortAnswerEn,
    required this.shortAnswerFa,
    required this.shortAnswerUr,
    required this.shortAnswerId,
    required this.simpleAnswerAr,
    required this.simpleAnswerEn,
    required this.simpleAnswerFa,
    required this.simpleAnswerUr,
    required this.simpleAnswerId,
    required this.madhabViews,
    this.category = const [],
    this.views = 0,
  });

  String getTitle(String lang) {
    switch (lang) {
      case 'en': return titleEn;
      case 'fa': return titleFa;
      case 'ur': return titleUr;
      case 'id': return titleId;
      default: return titleAr;
    }
  }

  String getShortAnswer(String lang) {
    switch (lang) {
      case 'en': return shortAnswerEn;
      case 'fa': return shortAnswerFa;
      case 'ur': return shortAnswerUr;
      case 'id': return shortAnswerId;
      default: return shortAnswerAr;
    }
  }

  String getSimpleAnswer(String lang) {
    switch (lang) {
      case 'en': return simpleAnswerEn;
      case 'fa': return simpleAnswerFa;
      case 'ur': return simpleAnswerUr;
      case 'id': return simpleAnswerId;
      default: return simpleAnswerAr;
    }
  }

  // ---- إضافة: تحويل من/إلى Firestore (لا تغيّر أي شيء في الحقول أعلاه) ----
  Map<String, dynamic> toMap() => {
        'titleAr': titleAr, 'titleEn': titleEn, 'titleFa': titleFa, 'titleUr': titleUr, 'titleId': titleId,
        'shortAnswerAr': shortAnswerAr, 'shortAnswerEn': shortAnswerEn, 'shortAnswerFa': shortAnswerFa,
        'shortAnswerUr': shortAnswerUr, 'shortAnswerId': shortAnswerId,
        'simpleAnswerAr': simpleAnswerAr, 'simpleAnswerEn': simpleAnswerEn, 'simpleAnswerFa': simpleAnswerFa,
        'simpleAnswerUr': simpleAnswerUr, 'simpleAnswerId': simpleAnswerId,
        'category': category,
        'views': views,
        'madhabViews': madhabViews.map((v) => v.toMap()).toList(),
      };

  factory IssueModel.fromMap(String id, Map<String, dynamic> map) => IssueModel(
        id: id,
        titleAr: map['titleAr'] ?? '', titleEn: map['titleEn'] ?? '',
        titleFa: map['titleFa'] ?? '', titleUr: map['titleUr'] ?? '', titleId: map['titleId'] ?? '',
        shortAnswerAr: map['shortAnswerAr'] ?? '', shortAnswerEn: map['shortAnswerEn'] ?? '',
        shortAnswerFa: map['shortAnswerFa'] ?? '', shortAnswerUr: map['shortAnswerUr'] ?? '',
        shortAnswerId: map['shortAnswerId'] ?? '',
        simpleAnswerAr: map['simpleAnswerAr'] ?? '', simpleAnswerEn: map['simpleAnswerEn'] ?? '',
        simpleAnswerFa: map['simpleAnswerFa'] ?? '', simpleAnswerUr: map['simpleAnswerUr'] ?? '',
        simpleAnswerId: map['simpleAnswerId'] ?? '',
        category: List<String>.from(map['category'] ?? const []),
        views: map['views'] ?? 0,
        madhabViews: ((map['madhabViews'] as List?) ?? [])
            .map((v) => MadhabView.fromMap(Map<String, dynamic>.from(v)))
            .toList(),
      );

  // مسألة 1: صلاة الجماعة
  static IssueModel getPrayerIssue() {
    return IssueModel(
      id: '1',
      titleAr: 'حكم صلاة الجماعة في المسجد للرجال',
      titleEn: 'Ruling on Congregational Prayer in the Mosque for Men',
      titleFa: 'حکم نماز جماعت در مسجد برای مردان',
      titleUr: 'مردوں کے لیے مسجد میں جماعت کی نماز کا حکم',
      titleId: 'Hukum Shalat Berjamaah di Masjid bagi Laki-laki',
      shortAnswerAr: 'من أعظم الشعائر. تتفاوت درجتها بين (فرض عين)، (فرض كفاية)، و (سنة مؤكدة).',
      shortAnswerEn: 'One of the greatest rituals. Its obligation varies between (individual duty), (collective duty), and (emphasized Sunnah).',
      shortAnswerFa: 'از بزرگترین شعائر. درجه آن بین (فرض عین)، (فرض کفایه) و (سنت مؤکده) متفاوت است.',
      shortAnswerUr: 'عظیم ترین شعائر میں سے۔ اس کا درجہ (فرض عین)، (فرض کفایہ) اور (سنت مؤکدہ) کے درمیان مختلف ہے۔',
      shortAnswerId: 'Salah satu ritual terbesar. Derajatnya bervariasi antara (fardu ain), (fardu kifayah), dan (sunnah muakkadah).',
      simpleAnswerAr: 'تجب عند جمهور الفقهاء. فرض عين عند الحنابلة والظاهرية، واجب مؤكد عند الحنفية، فرض كفاية عند المالكية والشافعية، ومستحبة عند الجعفرية والزيدية، وسنة عند الإباضية.',
      simpleAnswerEn: 'It is obligatory according to the majority of jurists.',
      simpleAnswerFa: 'به اتفاق جمهور فقها واجب است.',
      simpleAnswerUr: 'جمہور فقہاء کے نزدیک واجب ہے۔',
      simpleAnswerId: 'Wajib menurut mayoritas ulama.',
      category: const ['prayer'],
      madhabViews: [
        MadhabView(madhabId: 'maliki', ruling: 'فرض كفاية', detailTextAr: 'على أهل الحي. في حق الفرد سنة مؤكدة.', detailTextEn: 'Collective duty upon the neighborhood.', detailTextFa: 'بر اهل محله فرض کفایه است.', detailTextUr: 'محلہ والوں پر فرض کفایہ ہے۔', detailTextId: 'Fardu kifayah bagi penduduk lingkungan.', evidenceAr: 'الموطأ', evidenceEn: 'Al-Muwatta', evidenceFa: 'الموطأ', evidenceUr: 'الموطأ', evidenceId: 'Al-Muwatta'),
        MadhabView(madhabId: 'shafii', ruling: 'سنة مؤكدة', detailTextAr: 'فرض كفاية على المجتمع، وسنة للفرد.', detailTextEn: 'Collective duty for the community.', detailTextFa: 'فرض کفایه برای جامعه، و سنت برای فرد.', detailTextUr: 'معاشرے پر فرض کفایہ، اور فرد کے لیے سنت۔', detailTextId: 'Fardu kifayah bagi masyarakat, dan sunnah bagi individu.', evidenceAr: 'الأم', evidenceEn: 'Al-Umm', evidenceFa: 'الأم', evidenceUr: 'الأم', evidenceId: 'Al-Umm'),
        MadhabView(madhabId: 'hanafi', ruling: 'واجب', detailTextAr: 'على كل رجل حر بالغ عاقل. تاركها بلا عذر فاسق.', detailTextEn: 'Obligatory upon every free, adult, sane man.', detailTextFa: 'بر هر مرد آزاد بالغ عاقل واجب است.', detailTextUr: 'ہر آزاد، بالغ، عاقل مرد پر واجب ہے۔', detailTextId: 'Wajib bagi setiap laki-laki merdeka, baligh, dan berakal.', evidenceAr: 'الهداية', evidenceEn: 'Al-Hidayah', evidenceFa: 'الهداية', evidenceUr: 'الهداية', evidenceId: 'Al-Hidayah'),
        MadhabView(madhabId: 'hanbali', ruling: 'فرض عين', detailTextAr: 'على كل رجل قادر، لا يجوز تركها إلا لعذر.', detailTextEn: 'Individual duty upon every capable man.', detailTextFa: 'بر هر مرد توانا فرض عین است.', detailTextUr: 'ہر قابل مرد پر فرض عین ہے۔', detailTextId: 'Fardu ain bagi setiap laki-laki yang mampu.', evidenceAr: 'المغني', evidenceEn: 'Al-Mughni', evidenceFa: 'المغني', evidenceUr: 'المغني', evidenceId: 'Al-Mughni'),
        MadhabView(madhabId: 'dhahiri', ruling: 'فرض عين', detailTextAr: 'ظاهر الأمر النبوي يقتضي الوجوب.', detailTextEn: 'The apparent meaning of the prophetic command necessitates obligation.', detailTextFa: 'ظاهر امر نبوی اقتضای وجوب دارد.', detailTextUr: 'نبی ﷺ کے حکم کا ظاہری مفہوم وجوب کا تقاضا کرتا ہے۔', detailTextId: 'Makna lahiriah perintah Nabi menghendaki kewajiban.', evidenceAr: 'المحلى', evidenceEn: 'Al-Muhalla', evidenceFa: 'المحلى', evidenceUr: 'المحلى', evidenceId: 'Al-Muhalla'),
        MadhabView(madhabId: 'jafari', ruling: 'مستحب مؤكد', detailTextAr: 'في زمن الغيبة الكبرى ليست واجبة عيناً.', detailTextEn: 'In the time of the major occultation, it is not an individual duty.', detailTextFa: 'در زمان غیبت کبری واجب عینی نیست.', detailTextUr: 'غیبت کبریٰ کے زمانے میں فرض عین نہیں ہے۔', detailTextId: 'Pada masa gaib kubra, tidak wajib ain.', evidenceAr: 'الرسالة العملية', evidenceEn: 'Ar-Risalah al-‘Amaliyyah', evidenceFa: 'الرسالة العملية', evidenceUr: 'الرسالة العملية', evidenceId: 'Ar-Risalah al-‘Amaliyyah'),
        MadhabView(madhabId: 'zaidi', ruling: 'فرض كفاية', detailTextAr: 'يقترب من رأي السنة في تأكيد الجماعة.', detailTextEn: 'Close to the Sunni view in emphasizing congregation.', detailTextFa: 'نزدیک به نظر اهل سنت در تأکید بر جماعت است.', detailTextUr: 'جماعت پر زور دینے میں اہل سنت کے قریب ہے۔', detailTextId: 'Dekat dengan pandangan Sunni dalam menekankan jamaah.', evidenceAr: 'المجموع الفقهي', evidenceEn: 'Al-Majmu‘ al-Fiqhi', evidenceFa: 'المجموع الفقهي', evidenceUr: 'المجموع الفقهي', evidenceId: 'Al-Majmu‘ al-Fiqhi'),
        MadhabView(madhabId: 'ibadi', ruling: 'سنة مؤكدة', detailTextAr: 'من أعلام الدين، ولا تترك باستمرار.', detailTextEn: 'One of the symbols of the religion.', detailTextFa: 'از شعائر دین است.', detailTextUr: 'دین کی علامات میں سے ہے۔', detailTextId: 'Termasuk syiar agama.', evidenceAr: 'الجامع', evidenceEn: 'Al-Jami‘', evidenceFa: 'الجامع', evidenceUr: 'الجامع', evidenceId: 'Al-Jami‘'),
        MadhabView(madhabId: 'other', ruling: 'يختلف حسب المجمع', detailTextAr: 'تؤكد المجامع الفقهية على أهميتها مع مراعاة الظروف.', detailTextEn: 'Islamic jurisprudence councils emphasize its importance.', detailTextFa: 'مجامع فقهی بر اهمیت آن تأکید دارند.', detailTextUr: 'فقہی مجامع اس کی اہمیت پر زور دیتے ہیں۔', detailTextId: 'Dewan fiqh menekankan pentingnya.', evidenceAr: 'مجمع الفقه الإسلامي', evidenceEn: 'Islamic Fiqh Council', evidenceFa: 'مجمع الفقه الإسلامي', evidenceUr: 'مجمع الفقه الإسلامي', evidenceId: 'Majma\' Fiqh Islami'),
      ],
    );
  }

  static List<IssueModel> getMockIssues() {
    return [getPrayerIssue()];
  }

  // إضافة: دالة مساعدة يستدعيها home_screen.dart بأمان بغض النظر عن عدد المسائل المتوفرة
  static IssueModel getMockIssue([int index = 0]) {
    final all = getMockIssues();
    return all[index % all.length];
  }
}
