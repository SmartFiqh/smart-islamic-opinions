class CommentModel {
  final String id;
  final String issueId;
  final String userName;
  final String commentText;
  final double rating;
  final String type;
  final DateTime timestamp;
  final bool isApproved;
  final String sentiment; // نتيجة تحليل المشاعر، تُحفظ للمراجعة في لوحة التحكم
  final double sentimentScore;

  CommentModel({
    required this.id,
    required this.issueId,
    required this.userName,
    required this.commentText,
    required this.rating,
    required this.type,
    required this.timestamp,
    this.isApproved = false,
    this.sentiment = '',
    this.sentimentScore = 0.5,
  });

  Map<String, dynamic> toMap() => {
        'issueId': issueId,
        'userName': userName,
        'commentText': commentText,
        'rating': rating,
        'type': type,
        'timestamp': timestamp.toIso8601String(),
        'isApproved': isApproved,
        'sentiment': sentiment,
        'sentimentScore': sentimentScore,
      };

  factory CommentModel.fromMap(String id, Map<String, dynamic> map) => CommentModel(
        id: id,
        issueId: map['issueId'] ?? '',
        userName: map['userName'] ?? '',
        commentText: map['commentText'] ?? '',
        rating: (map['rating'] as num?)?.toDouble() ?? 0.0,
        type: map['type'] ?? 'other',
        timestamp: DateTime.tryParse(map['timestamp'] ?? '') ?? DateTime.now(),
        isApproved: map['isApproved'] ?? false,
        sentiment: map['sentiment'] ?? '',
        sentimentScore: (map['sentimentScore'] as num?)?.toDouble() ?? 0.5,
      );
}
