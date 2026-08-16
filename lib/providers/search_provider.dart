import 'package:flutter/material.dart';
import '../models/issue_model.dart';
import '../models/comment_model.dart';
import '../services/firestore_service.dart';
import '../services/semantic_search_service.dart';
import '../services/summarization_service.dart';
import '../services/analytics_service.dart';

class SearchProvider extends ChangeNotifier {
  String _query = '';
  List<IssueModel> _results = [];
  List<IssueModel> _allIssues = [];
  List<IssueModel> _recommendations = [];
  bool _isLoading = false;
  bool _hasNoResults = false;
  bool _usingAI = false;
  bool _isLoaded = false;
  double _confidence = 0.0;
  String _searchMessage = '';
  List<String> _userHistory = [];

  // Getters
  String get query => _query;
  List<IssueModel> get results => _results;
  List<IssueModel> get recommendations => _recommendations;
  bool get isLoading => _isLoading;
  bool get hasNoResults => _hasNoResults;
  bool get usingAI => _usingAI;
  double get confidence => _confidence;
  String get searchMessage => _searchMessage;

  Future<void> loadAllIssues() async {
    if (_isLoaded) return;

    _isLoading = true;
    notifyListeners();

    try {
      _allIssues = await FirestoreService().getAllIssues();
      if (_allIssues.isEmpty) {
        _allIssues = IssueModel.getMockIssues();
      }
      _isLoaded = true;
    } catch (e) {
      // لا يوجد اتصال بـ Firebase أو لم يُعدّ بعد -> استخدم بيانات تجريبية
      _allIssues = IssueModel.getMockIssues();
      _isLoaded = true;
    }

    _isLoading = false;
    notifyListeners();
  }

  /// يُحدّث نص البحث فقط (يُستخدم أثناء الكتابة قبل الضغط على "بحث")
  void updateQuery(String value) {
    _query = value;
    notifyListeners();
  }

  /// نقطة الدخول المستخدمة من شاشة الرئيسية — تُشير إلى smartSearch
  Future<void> search(String query, String lang) => smartSearch(query, lang);

  // ✅ البحث الذكي المتقدم
  Future<void> smartSearch(String query, String lang) async {
    if (!_isLoaded) {
      await loadAllIssues();
    }

    _isLoading = true;
    _hasNoResults = false;
    _usingAI = false;
    _query = query;
    _confidence = 0.0;
    _searchMessage = '';
    notifyListeners();

    await Future.delayed(const Duration(milliseconds: 300));

    // 1. البحث النصي السريع (للمطابقات التامة)
    final lowerQuery = query.toLowerCase();
    final textResults = _allIssues.where((issue) {
      return issue.getTitle(lang).toLowerCase().contains(lowerQuery);
    }).toList();

    if (textResults.isNotEmpty) {
      _results = textResults;
      _confidence = 0.95;
      _searchMessage = 'تم العثور على ${textResults.length} نتيجة';
      _isLoading = false;
      notifyListeners();
      return;
    }

    // 2. البحث الدلالي بالذكاء الاصطناعي
    _usingAI = true;
    try {
      final result = await SemanticSearchService.semanticSearch(
        query,
        _allIssues,
        lang,
      );

      _confidence = result.confidence;
      _searchMessage = result.message;

      if (result.isMatch && result.matchedIssue != null) {
        _results = [result.matchedIssue!];
        _hasNoResults = false;

        // إضافة للمستخدم التاريخ
        _userHistory.add(result.matchedIssue!.getTitle(lang));
        if (_userHistory.length > 20) {
          _userHistory.removeAt(0);
        }

        // جلب توصيات ذكية
        _recommendations = await AnalyticsService.getSmartRecommendations(
          _allIssues,
          _userHistory,
          lang,
        );
      } else {
        _results = [];
        _hasNoResults = true;
        if (_confidence < 0.5) {
          _searchMessage = 'لم أعثر على تطابق كافٍ. حاول إعادة صياغة السؤال.';
        }
      }
    } catch (e) {
      _results = [];
      _hasNoResults = true;
      _searchMessage = 'حدث خطأ أثناء البحث: $e';
    }

    _isLoading = false;
    notifyListeners();
  }

  // ✅ تلخيص ذكي لنص المسألة
  Future<SummaryResult> smartSummarize(String text, String lang) async {
    return await SummarizationService.summarizeText(text, lang);
  }

  // ✅ تحليل مشاعر التعليق
  Future<SentimentResult> analyzeComment(String comment, String lang) async {
    return await AnalyticsService.analyzeSentiment(comment, lang);
  }

  /// يحفظ تعليق/تقييم المستخدم فعلياً في Firestore (بدلاً من ضياعه بعد الإرسال)
  Future<void> submitComment(CommentModel comment) async {
    try {
      await FirestoreService().addComment(comment);
    } catch (e) {
      // في وضع عدم الاتصال، نتجاهل بصمت — الواجهة تُظهر رسالة نجاح محلياً فقط
    }
  }

  void clearResults() {
    _results = [];
    _hasNoResults = false;
    _usingAI = false;
    _confidence = 0.0;
    _searchMessage = '';
    notifyListeners();
  }

  void addToHistory(String title) {
    _userHistory.add(title);
    if (_userHistory.length > 20) {
      _userHistory.removeAt(0);
    }
  }
}
