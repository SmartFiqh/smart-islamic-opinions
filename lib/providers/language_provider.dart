import 'package:flutter/material.dart';

class LanguageProvider extends ChangeNotifier {
  Locale _currentLocale = const Locale('ar');

  Locale get currentLocale => _currentLocale;

  void setLanguage(String languageCode) {
    _currentLocale = Locale(languageCode);
    notifyListeners();
  }

  String getCurrentLanguageName() {
    switch (_currentLocale.languageCode) {
      case 'en':
        return 'English';
      case 'fa':
        return 'فارسی';
      case 'ur':
        return 'اُردُو';
      case 'id':
        return 'Bahasa Indonesia';
      default:
        return 'العربية';
    }
  }
}
