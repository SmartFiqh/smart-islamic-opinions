// داخل result_screen.dart، في تبويب "موسع"، بعد جدول المذاهب:

// عرض نسبة الثقة
if (search.confidence > 0)
  Container(
    padding: const EdgeInsets.all(12),
    margin: const EdgeInsets.symmetric(vertical: 8),
    decoration: BoxDecoration(
      color: search.confidence >= 0.8 
          ? Colors.green.shade50 
          : Colors.orange.shade50,
      borderRadius: BorderRadius.circular(12),
      border: Border.all(
        color: search.confidence >= 0.8 
            ? Colors.green.shade300 
            : Colors.orange.shade300,
      ),
    ),
    child: Row(
      children: [
        Icon(
          search.confidence >= 0.8 
              ? Icons.check_circle 
              : Icons.info_outline,
          color: search.confidence >= 0.8 
              ? Colors.green 
              : Colors.orange,
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '${isRtl ? 'نسبة الثقة' : 'Confidence'}',
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
              Text(
                '${(search.confidence * 100).toStringAsFixed(0)}% - ${search.searchMessage}',
                style: TextStyle(
                  color: search.confidence >= 0.8 
                      ? Colors.green.shade700 
                      : Colors.orange.shade700,
                ),
              ),
            ],
          ),
        ),
      ],
    ),
  ),

// عرض التوصيات الذكية
if (search.recommendations.isNotEmpty)
  Padding(
    padding: const EdgeInsets.symmetric(vertical: 16),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          isRtl 
              ? '📌 قد تهمك هذه المسائل أيضاً' 
              : '📌 You might also be interested in',
          style: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 8),
        ...search.recommendations.map((issue) {
          return Card(
            margin: const EdgeInsets.symmetric(vertical: 4),
            child: ListTile(
              title: Text(issue.getTitle(lang.currentLocale.languageCode)),
              trailing: const Icon(Icons.arrow_forward),
              onTap: () {
                search.smartSearch(
                  issue.getTitle(lang.currentLocale.languageCode),
                  lang.currentLocale.languageCode,
                );
                Navigator.pushReplacement(
                  context,
                  MaterialPageRoute(builder: (_) => const ResultScreen()),
                );
              },
            ),
          );
        }),
      ],
    ),
  ),
