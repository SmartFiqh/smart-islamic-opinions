class CommentModel {
  final String id;
  final String issueId;
  final String userName;
  final String commentText;
  final double rating;
  final String type;
  final DateTime timestamp;
  final bool isApproved;

  CommentModel({
    required this.id,
    required this.issueId,
    required this.userName,
    required this.commentText,
    required this.rating,
    required this.type,
    required this.timestamp,
    this.isApproved = false,
  });
}
