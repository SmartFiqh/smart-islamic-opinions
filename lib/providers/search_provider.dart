import 'package:flutter/material.dart';
import '../models/issue_model.dart';
import '../services/firestore_service.dart';
import '../services/ai_service.dart';

class SearchProvider extends ChangeNotifier {
  String _query = '';
  List<IssueModel> _results = [];
  List<IssueModel> _allIssues = [];
  bool _isLoading = false;
  bool _hasNoResults = false;
  bool _usingAI = false;
  bool _isLoaded = false;

  String get query => _query;
  List<IssueModel> get results => _results;
  bool get isLoading => _isLoading;
  bool get hasNoResults => _hasNoResults;
  bool get usingAI => _usingAI;

  Future<void> loadAllIssues() async {
    if (_isLoaded) return;
    
    _isLoading = true;
    notifyListeners();
    
    try {
      _allIssues = await FirestoreService().getAllIssues();
      _isLoaded = true;
    } catch (e) {
      _allIssues = IssueModel.getMockIssues();
    }
    
    _isLoading = false;
    notifyListeners();
  }

  Future<void> search(String query, String lang) async {
    if (!_isLoaded) {
      await loadAllIssues();
    }

    _isLoading = true;
    _hasNoResults = false;
    _usingAI = false;
    _query = query;
    notifyListeners();

    await Future.delayed(const Duration(milliseconds: 400));

    final lowerQuery = query.toLowerCase();

    // بحث نصي أولاً
    final textResults = _allIssues.where((issue) {
      return issue.getTitle(lang).toLowerCase().contains(lowerQuery);
    }).toList();

    if (textResults.isNotEmpty) {
      _results = textResults;
      _isLoading = false;
      notifyListeners();
      return;
    }

    // بحث بالذكاء الاصطناعي
    _usingAI = true;
    try {
      final issueTitles = _allIssues.map((i) => i.getTitle(lang)).toList();
      final aiResult = await AIService.findBestMatch(query, issueTitles);

      if (aiResult.contains('UNKNOWN')) {
        _results = [];
        _hasNoResults = true;
      } else if (aiResult.contains('SIMILAR')) {
        final titleMatch = aiResult.replaceFirst('SIMILAR', '').trim();
        _results = _allIssues.where((i) => i.getTitle(lang) == titleMatch).toList();
        if (_results.isEmpty) _hasNoResults = true;
      } else {
        _results = _allIssues.where((i) => i.getTitle(lang) == aiResult).toList();
        if (_results.isEmpty) _hasNoResults = true;
      }
    } catch (e) {
      _results = [];
      _hasNoResults = true;
    }

    _isLoading = false;
    notifyListeners();
  }

  void clearResults() {
    _results = [];
    _hasNoResults = false;
    _usingAI = false;
    notifyListeners();
  }
}
