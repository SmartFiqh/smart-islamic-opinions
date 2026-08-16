import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_core/firebase_core.dart';
import '../models/issue_model.dart';
import '../models/comment_model.dart';

class FirestoreService {
  static final FirestoreService _instance = FirestoreService._internal();
  factory FirestoreService() => _instance;
  FirestoreService._internal();

  late FirebaseFirestore _firestore;

  Future<void> init() async {
    await Firebase.initializeApp();
    _firestore = FirebaseFirestore.instance;
  }

  Future<List<IssueModel>> getAllIssues() async {
    try {
      final snapshot = await _firestore.collection('issues').get();
      return snapshot.docs.map((doc) {
        final data = doc.data();
        return _issueFromMap(data, doc.id);
      }).toList();
    } catch (e) {
      return [];
    }
  }

  Future<void> addIssue(IssueModel issue) async {
    await _firestore.collection('issues').doc(issue.id).set({
      'title_ar': issue.titleAr,
      'title_en': issue.titleEn,
      'title_fa': issue.titleFa,
      'title_ur': issue.titleUr,
      'title_id': issue.titleId,
      'short_answer_ar': issue.shortAnswerAr,
      'short_answer_en': issue.shortAnswerEn,
      'short_answer_fa': issue.shortAnswerFa,
      'short_answer_ur': issue.shortAnswerUr,
      'short_answer_id': issue.shortAnswerId,
      'simple_answer_ar': issue.simpleAnswerAr,
      'simple_answer_en': issue.simpleAnswerEn,
      'simple_answer_fa': issue.simpleAnswerFa,
      'simple_answer_ur': issue.simpleAnswerUr,
      'simple_answer_id': issue.simpleAnswerId,
      'madhab_views': issue.madhabViews.map((v) => {
        'madhab_id': v.madhabId,
        'ruling': v.ruling,
        'detail_text_ar': v.detailTextAr,
        'detail_text_en': v.detailTextEn,
        'detail_text_fa': v.detailTextFa,
        'detail_text_ur': v.detailTextUr,
        'detail_text_id': v.detailTextId,
        'evidence_ar': v.evidenceAr,
        'evidence_en': v.evidenceEn,
        'evidence_fa': v.evidenceFa,
        'evidence_ur': v.evidenceUr,
        'evidence_id': v.evidenceId,
      }).toList(),
      'category': issue.category,
      'created_at': FieldValue.serverTimestamp(),
    });
  }

  Future<List<CommentModel>> getCommentsForIssue(String issueId) async {
    try {
      final snapshot = await _firestore
          .collection('comments')
          .where('issue_id', isEqualTo: issueId)
          .where('is_approved', isEqualTo: true)
          .orderBy('timestamp', descending: true)
          .get();
      
      return snapshot.docs.map((doc) {
        final data = doc.data();
        return CommentModel(
          id: doc.id,
          issueId: data['issue_id'],
          userName: data['user_name'],
          commentText: data['comment_text'],
          rating: (data['rating'] as num).toDouble(),
          type: data['type'] ?? 'other',
          timestamp: (data['timestamp'] as Timestamp).toDate(),
          isApproved: data['is_approved'] ?? false,
        );
      }).toList();
    } catch (e) {
      return [];
    }
  }

  Future<void> addComment(CommentModel comment) async {
    await _firestore.collection('comments').add({
      'issue_id': comment.issueId,
      'user_name': comment.userName,
      'comment_text': comment.commentText,
      'rating': comment.rating,
      'type': comment.type,
      'timestamp': FieldValue.serverTimestamp(),
      'is_approved': false,
    });
  }

  IssueModel _issueFromMap(Map<String, dynamic> data, String id) {
    final views = (data['madhab_views'] as List? ?? []).map((v) {
      return MadhabView(
        madhabId: v['madhab_id'] ?? '',
        ruling: v['ruling'] ?? '',
        detailTextAr: v['detail_text_ar'] ?? '',
        detailTextEn: v['detail_text_en'] ?? '',
        detailTextFa: v['detail_text_fa'] ?? '',
        detailTextUr: v['detail_text_ur'] ?? '',
        detailTextId: v['detail_text_id'] ?? '',
        evidenceAr: v['evidence_ar'] ?? '',
        evidenceEn: v['evidence_en'] ?? '',
        evidenceFa: v['evidence_fa'] ?? '',
        evidenceUr: v['evidence_ur'] ?? '',
        evidenceId: v['evidence_id'] ?? '',
      );
    }).toList();

    return IssueModel(
      id: id,
      titleAr: data['title_ar'] ?? '',
      titleEn: data['title_en'] ?? '',
      titleFa: data['title_fa'] ?? '',
      titleUr: data['title_ur'] ?? '',
      titleId: data['title_id'] ?? '',
      shortAnswerAr: data['short_answer_ar'] ?? '',
      shortAnswerEn: data['short_answer_en'] ?? '',
      shortAnswerFa: data['short_answer_fa'] ?? '',
      shortAnswerUr: data['short_answer_ur'] ?? '',
      shortAnswerId: data['short_answer_id'] ?? '',
      simpleAnswerAr: data['simple_answer_ar'] ?? '',
      simpleAnswerEn: data['simple_answer_en'] ?? '',
      simpleAnswerFa: data['simple_answer_fa'] ?? '',
      simpleAnswerUr: data['simple_answer_ur'] ?? '',
      simpleAnswerId: data['simple_answer_id'] ?? '',
      madhabViews: views,
      category: List<String>.from(data['category'] ?? []),
    );
  }
}
