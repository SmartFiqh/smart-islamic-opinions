import 'package:flutter/material.dart';
import '../models/madhhab_model.dart';

class FilterProvider extends ChangeNotifier {
  String _selectedGroup = 'all'; // all, Sunni, Shia, Ibadi, Other
  String? _selectedMadhabId;

  String get selectedGroup => _selectedGroup;
  String? get selectedMadhabId => _selectedMadhabId;

  void setGroup(String group) {
    _selectedGroup = group;
    _selectedMadhabId = null;
    notifyListeners();
  }

  void setMadhab(String madhabId) {
    _selectedMadhabId = madhabId;
    _selectedGroup = 'custom';
    notifyListeners();
  }

  List<Madhhab> getFilteredMadhabs() {
    if (_selectedMadhabId != null) {
      return [Madhhab.getById(_selectedMadhabId!)];
    }
    switch (_selectedGroup) {
      case 'all':
        return Madhhab.all;
      case 'Sunni':
        return Madhhab.all.where((m) => m.group == 'Sunni').toList();
      case 'Shia':
        return Madhhab.all.where((m) => m.group == 'Shia').toList();
      case 'Ibadi':
        return Madhhab.all.where((m) => m.group == 'Ibadi').toList();
      case 'Other':
        return Madhhab.all.where((m) => m.group == 'Other').toList();
      default:
        return Madhhab.all;
    }
  }

  String getCurrentGroupName(String lang) {
    switch (_selectedGroup) {
      case 'all':
        return lang == 'ar' ? 'جميع المذاهب' : 'All Schools';
      case 'Sunni':
        return lang == 'ar' ? 'مذاهب السنة' : 'Sunni Schools';
      case 'Shia':
        return lang == 'ar' ? 'مذاهب الشيعة' : 'Shia Schools';
      case 'Ibadi':
        return lang == 'ar' ? 'المذهب الإباضي' : 'Ibadi School';
      case 'Other':
        return lang == 'ar' ? 'آراء أخرى' : 'Other Views';
      default:
        return lang == 'ar' ? 'مخصص' : 'Custom';
    }
  }
}
