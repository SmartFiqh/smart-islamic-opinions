import 'madhhab_model.dart';

class MadhabView {
  final String madhabId;
  final String ruling;
  final String detailTextAr;
  final String detailTextEn;
  final String detailTextFa;
  final String detailTextUr;
  final String detailTextId;
  final String evidenceAr;
  final String evidenceEn;
  final String evidenceFa;
  final String evidenceUr;
  final String evidenceId;

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
      case 'en':
        return detailTextEn;
      case 'fa':
        return detailTextFa;
      case 'ur':
        return detailTextUr;
      case 'id':
        return detailTextId;
      default:
        return detailTextAr;
    }
  }

  String getEvidence(String lang) {
    switch (lang) {
      case 'en':
        return evidenceEn;
      case 'fa':
        return evidenceFa;
      case 'ur':
        return evidenceUr;
      case 'id':
        return evidenceId;
      default:
        return evidenceAr;
    }
  }
}

class IssueModel {
  final String id;
  final String titleAr;
  final String titleEn;
  final String titleFa;
  final String titleUr;
  final String titleId;
  final String shortAnswerAr;
  final String shortAnswerEn;
  final String shortAnswerFa;
  final String shortAnswerUr;
  final String shortAnswerId;
  final String simpleAnswerAr;
  final String simpleAnswerEn;
  final String simpleAnswerFa;
  final String simpleAnswerUr;
  final String simpleAnswerId;
  final List<MadhabView> madhabViews;
  final List<String> category;

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
  });

  String getTitle(String lang) {
    switch (lang) {
      case 'en':
        return titleEn;
      case 'fa':
        return titleFa;
      case 'ur':
        return titleUr;
      case 'id':
        return titleId;
      default:
        return titleAr;
    }
  }

  String getShortAnswer(String lang) {
    switch (lang) {
      case 'en':
        return shortAnswerEn;
      case 'fa':
        return shortAnswerFa;
      case 'ur':
        return shortAnswerUr;
      case 'id':
        return shortAnswerId;
      default:
        return shortAnswerAr;
    }
  }

  String getSimpleAnswer(String lang) {
    switch (lang) {
      case 'en':
        return simpleAnswerEn;
      case 'fa':
        return simpleAnswerFa;
      case 'ur':
        return simpleAnswerUr;
      case 'id':
        return simpleAnswerId;
      default:
        return simpleAnswerAr;
    }
  }

  // بيانات وهمية - مسألة: حكم صلاة الجماعة
  static IssueModel getMockIssue() {
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
      simpleAnswerEn: 'It is obligatory according to the majority of jurists. Individual duty for Hanbalis and Dhahiriyya, confirmed duty for Hanafis, collective duty for Malikis and Shafi\'is, recommended for Ja\'faris and Zaidis, and Sunnah for Ibadis.',
      simpleAnswerFa: 'به اتفاق جمهور فقها واجب است. فرض عین برای حنبلی‌ها و ظاهریه، واجب مؤکد برای حنفی‌ها، فرض کفایه برای مالکی‌ها و شافعی‌ها، مستحب برای جعفری‌ها و زیدی‌ها، و سنت برای اباضیه.',
      simpleAnswerUr: 'جمہور فقہاء کے نزدیک واجب ہے۔ حنابلہ اور ظاہریہ کے نزدیک فرض عین، احناف کے نزدیک واجب مؤکد، مالکیہ اور شافعیہ کے نزدیک فرض کفایہ، جعفریہ اور زیدیہ کے نزدیک مستحب، اور اباضیہ کے نزدیک سنت ہے۔',
      simpleAnswerId: 'Wajib menurut mayoritas ulama. Fardu ain menurut Hanbali dan Dhahiri, wajib muakkad menurut Hanafi, fardu kifayah menurut Maliki dan Syafii, mustahab menurut Ja\'fari dan Zaidi, dan sunnah menurut Ibadi.',
      madhabViews: [
        MadhabView(
          madhabId: 'maliki',
          ruling: 'فرض كفاية',
          detailTextAr: 'على أهل الحي. في حق الفرد سنة مؤكدة.',
          detailTextEn: 'Collective duty upon the neighborhood. For the individual, it is an emphasized Sunnah.',
          detailTextFa: 'بر اهل محله فرض کفایه است. برای فرد، سنت مؤکده است.',
          detailTextUr: 'محلہ والوں پر فرض کفایہ ہے۔ فرد کے حق میں سنت مؤکدہ ہے۔',
          detailTextId: 'Fardu kifayah bagi penduduk lingkungan. Bagi individu, sunnah muakkadah.',
          evidenceAr: 'الموطأ',
          evidenceEn: 'Al-Muwatta',
          evidenceFa: 'الموطأ',
          evidenceUr: 'الموطأ',
          evidenceId: 'Al-Muwatta',
        ),
        MadhabView(
          madhabId: 'shafii',
          ruling: 'سنة مؤكدة',
          detailTextAr: 'فرض كفاية على المجتمع، وسنة للفرد.',
          detailTextEn: 'Collective duty for the community, Sunnah for the individual.',
          detailTextFa: 'فرض کفایه برای جامعه، و سنت برای فرد.',
          detailTextUr: 'معاشرے پر فرض کفایہ، اور فرد کے لیے سنت۔',
          detailTextId: 'Fardu kifayah bagi masyarakat, dan sunnah bagi individu.',
          evidenceAr: 'الأم',
          evidenceEn: 'Al-Umm',
          evidenceFa: 'الأم',
          evidenceUr: 'الأم',
          evidenceId: 'Al-Umm',
        ),
        MadhabView(
          madhabId: 'hanafi',
          ruling: 'واجب',
          detailTextAr: 'على كل رجل حر بالغ عاقل. تاركها بلا عذر فاسق.',
          detailTextEn: 'Obligatory upon every free, adult, sane man. One who abandons it without excuse is a transgressor.',
          detailTextFa: 'بر هر مرد آزاد بالغ عاقل واجب است. ترک کننده آن بدون عذر، فاسق است.',
          detailTextUr: 'ہر آزاد، بالغ، عاقل مرد پر واجب ہے۔ بغیر عذر اسے چھوڑنے والا فاسق ہے۔',
          detailTextId: 'Wajib bagi setiap laki-laki merdeka, baligh, dan berakal. Yang meninggalkannya tanpa uzur adalah fasik.',
          evidenceAr: 'الهداية',
          evidenceEn: 'Al-Hidayah',
          evidenceFa: 'الهداية',
          evidenceUr: 'الهداية',
          evidenceId: 'Al-Hidayah',
        ),
        MadhabView(
          madhabId: 'hanbali',
          ruling: 'فرض عين',
          detailTextAr: 'على كل رجل قادر، لا يجوز تركها إلا لعذر.',
          detailTextEn: 'Individual duty upon every capable man; it is not permissible to abandon it except for an excuse.',
          detailTextFa: 'بر هر مرد توانا فرض عین است؛ ترک آن جز با عذر جایز نیست.',
          detailTextUr: 'ہر قابل مرد پر فرض عین ہے؛ عذر کے بغیر اسے چھوڑنا جائز نہیں۔',
          detailTextId: 'Fardu ain bagi setiap laki-laki yang mampu; tidak boleh ditinggalkan kecuali ada uzur.',
          evidenceAr: 'المغني',
          evidenceEn: 'Al-Mughni',
          evidenceFa: 'المغني',
          evidenceUr: 'المغني',
          evidenceId: 'Al-Mughni',
        ),
        MadhabView(
          madhabId: 'dhahiri',
          ruling: 'فرض عين',
          detailTextAr: 'ظاهر الأمر النبوي يقتضي الوجوب.',
          detailTextEn: 'The apparent meaning of the prophetic command necessitates obligation.',
          detailTextFa: 'ظاهر امر نبوی اقتضای وجوب دارد.',
          detailTextUr: 'نبی ﷺ کے حکم کا ظاہری مفہوم وجوب کا تقاضا کرتا ہے۔',
          detailTextId: 'Makna lahiriah perintah Nabi menghendaki kewajiban.',
          evidenceAr: 'المحلى',
          evidenceEn: 'Al-Muhalla',
          evidenceFa: 'المحلى',
          evidenceUr: 'المحلى',
          evidenceId: 'Al-Muhalla',
        ),
        MadhabView(
          madhabId: 'jafari',
          ruling: 'مستحب مؤكد',
          detailTextAr: 'في زمن الغيبة الكبرى ليست واجبة عيناً.',
          detailTextEn: 'In the time of the major occultation, it is not an individual duty.',
          detailTextFa: 'در زمان غیبت کبری واجب عینی نیست.',
          detailTextUr: 'غیبت کبریٰ کے زمانے میں فرض عین نہیں ہے۔',
          detailTextId: 'Pada masa gaib kubra, tidak wajib ain.',
          evidenceAr: 'الرسالة العملية',
          evidenceEn: 'Ar-Risalah al-‘Amaliyyah',
          evidenceFa: 'الرسالة العملية',
          evidenceUr: 'الرسالة العملية',
          evidenceId: 'Ar-Risalah al-‘Amaliyyah',
        ),
        MadhabView(
          madhabId: 'zaidi',
          ruling: 'فرض كفاية',
          detailTextAr: 'يقترب من رأي السنة في تأكيد الجماعة.',
          detailTextEn: 'Close to the Sunni view in emphasizing congregation.',
          detailTextFa: 'نزدیک به نظر اهل سنت در تأکید بر جماعت است.',
          detailTextUr: 'جماعت پر زور دینے میں اہل سنت کے قریب ہے۔',
          detailTextId: 'Dekat dengan pandangan Sunni dalam menekankan jamaah.',
          evidenceAr: 'المجموع الفقهي',
          evidenceEn: 'Al-Majmu‘ al-Fiqhi',
          evidenceFa: 'المجموع الفقهي',
          evidenceUr: 'المجموع الفقهي',
          evidenceId: 'Al-Majmu‘ al-Fiqhi',
        ),
        MadhabView(
          madhabId: 'ibadi',
          ruling: 'سنة مؤكدة',
          detailTextAr: 'من أعلام الدين، ولا تترك باستمرار.',
          detailTextEn: 'One of the symbols of the religion; it should not be abandoned continuously.',
          detailTextFa: 'از شعائر دین است و نباید به طور پیوسته ترک شود.',
          detailTextUr: 'دین کی علامات میں سے ہے اور اسے مسلسل نہیں چھوڑنا چاہیے۔',
          detailTextId: 'Termasuk syiar agama; tidak boleh ditinggalkan terus-menerus.',
          evidenceAr: 'الجامع',
          evidenceEn: 'Al-Jami‘',
          evidenceFa: 'الجامع',
          evidenceUr: 'الجامع',
          evidenceId: 'Al-Jami‘',
        ),
        MadhabView(
          madhabId: 'other',
          ruling: 'يختلف حسب المجمع',
          detailTextAr: 'تؤكد المجامع الفقهية على أهميتها مع مراعاة الظروف.',
          detailTextEn: 'Islamic jurisprudence councils emphasize its importance while taking circumstances into account.',
          detailTextFa: 'مجامع فقهی بر اهمیت آن با توجه به شرایط تأکید دارند.',
          detailTextUr: 'فقہی مجامع حالات کو مدنظر رکھتے ہوئے اس کی اہمیت پر زور دیتے ہیں۔',
          detailTextId: 'Dewan fiqh menekankan pentingnya dengan mempertimbangkan kondisi.',
          evidenceAr: 'مجمع الفقه الإسلامي',
          evidenceEn: 'Islamic Fiqh Council',
          evidenceFa: 'مجمع الفقه الإسلامي',
          evidenceUr: 'مجمع الفقه الإسلامي',
          evidenceId: 'Majma\' Fiqh Islami',
        ),
      ],
    );
  }

  static List<IssueModel> getMockIssues() {
    return [getMockIssue()];
  }
}
