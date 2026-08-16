import 'package:flutter/material.dart';
import '../models/issue_model.dart';

class SearchProvider extends ChangeNotifier {
  String _query = '';
  List<IssueModel> _results = [];
  bool _isLoading = false;
  bool _hasNoResults = false;

  String get query => _query;
  List<IssueModel> get results => _results;
  bool get isLoading => _isLoading;
  bool get hasNoResults => _hasNoResults;

  void updateQuery(String value) {
    _query = value;
    notifyListeners();
  }

  Future<void> search(String query, String lang) async {
    _isLoading = true;
    _hasNoResults = false;
    notifyListeners();

    await Future.delayed(const Duration(milliseconds: 400));

    final mockIssues = IssueModel.getMockIssues();
    final lowerQuery = query.toLowerCase();

    final found = mockIssues.where((issue) {
      final title = issue.getTitle(lang).toLowerCase();
      return title.contains(lowerQuery);
    }).toList();

    if (found.isNotEmpty) {
      _results = found;
    } else {
      _results = [];
      _hasNoResults = true;
    }

    _isLoading = false;
    notifyListeners();
  }

  void clearResults() {
    _results = [];
    _hasNoResults = false;
    notifyListeners();
  }
}
