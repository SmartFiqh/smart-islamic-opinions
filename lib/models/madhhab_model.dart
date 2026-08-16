import 'package:flutter/material.dart';

class Madhhab {
  final String id;
  final String nameAr;
  final String nameEn;
  final String nameFa;
  final String nameUr;
  final String nameId;
  final String group; // Sunni, Shia, Ibadi, Other
  final Color color;
  final IconData icon;

  const Madhhab({
    required this.id,
    required this.nameAr,
    required this.nameEn,
    required this.nameFa,
    required this.nameUr,
    required this.nameId,
    required this.group,
    required this.color,
    required this.icon,
  });

  static const List<Madhhab> all = [
    // مذاهب السنة (5)
    Madhhab(
      id: 'maliki',
      nameAr: 'المالكي',
      nameEn: 'Maliki',
      nameFa: 'مالکی',
      nameUr: 'مالکی',
      nameId: 'Maliki',
      group: 'Sunni',
      color: Color(0xFF1565C0),
      icon: Icons.agriculture,
    ),
    Madhhab(
      id: 'shafii',
      nameAr: 'الشافعي',
      nameEn: 'Shafii',
      nameFa: 'شافعی',
      nameUr: 'شافعی',
      nameId: 'Syafii',
      group: 'Sunni',
      color: Color(0xFFF57F17),
      icon: Icons.school,
    ),
    Madhhab(
      id: 'hanafi',
      nameAr: 'الحنفي',
      nameEn: 'Hanafi',
      nameFa: 'حنفی',
      nameUr: 'حنفی',
      nameId: 'Hanafi',
      group: 'Sunni',
      color: Color(0xFF2E7D32),
      icon: Icons.balance,
    ),
    Madhhab(
      id: 'hanbali',
      nameAr: 'الحنبلي',
      nameEn: 'Hanbali',
      nameFa: 'حنبالی',
      nameUr: 'حنبلی',
      nameId: 'Hanbali',
      group: 'Sunni',
      color: Color(0xFFC62828),
      icon: Icons.history_edu,
    ),
    Madhhab(
      id: 'dhahiri',
      nameAr: 'الظاهري',
      nameEn: 'Dhahiri',
      nameFa: 'ظاهری',
      nameUr: 'ظاہری',
      nameId: 'Dhahiri',
      group: 'Sunni',
      color: Color(0xFF6A1B9A),
      icon: Icons.text_fields,
    ),
    // مذاهب الشيعة (2)
    Madhhab(
      id: 'jafari',
      nameAr: 'الجعفري',
      nameEn: 'Jafari',
      nameFa: 'جعفری',
      nameUr: 'جعفری',
      nameId: 'Jafari',
      group: 'Shia',
      color: Color(0xFF00838F),
      icon: Icons.star,
    ),
    Madhhab(
      id: 'zaidi',
      nameAr: 'الزيدي',
      nameEn: 'Zaidi',
      nameFa: 'زیدی',
      nameUr: 'زیدی',
      nameId: 'Zaidi',
      group: 'Shia',
      color: Color(0xFFAD1457),
      icon: Icons.people,
    ),
    // الإباضي (1)
    Madhhab(
      id: 'ibadi',
      nameAr: 'الإباضي',
      nameEn: 'Ibadi',
      nameFa: 'اباضی',
      nameUr: 'اباضی',
      nameId: 'Ibadi',
      group: 'Ibadi',
      color: Color(0xFFE65100),
      icon: Icons.landscape,
    ),
    // آراء أخرى (1)
    Madhhab(
      id: 'other',
      nameAr: 'آراء أخرى',
      nameEn: 'Other Views',
      nameFa: 'دیگر آراء',
      nameUr: 'دیگر آراء',
      nameId: 'Pendapat Lain',
      group: 'Other',
      color: Color(0xFF607D8B),
      icon: Icons.group_work,
    ),
  ];

  static Madhhab getById(String id) => all.firstWhere((m) => m.id == id);

  String getName(String lang) {
    switch (lang) {
      case 'en':
        return nameEn;
      case 'fa':
        return nameFa;
      case 'ur':
        return nameUr;
      case 'id':
        return nameId;
      default:
        return nameAr;
    }
  }
}
