# utils/search_service.py - تحسين البحث

def search(self, query: str, topic_filter: str, madhabs: List[str], 
           level: str, lang: str, T: Dict) -> List[SearchResult]:
    """البحث عن المسائل الفقهية مع تحسين المطابقة"""
    if not query:
        return []
    
    cache_key = f"{query}|{topic_filter}|{','.join(madhabs)}|{level}|{lang}"
    if cache_key in self._cache:
        return self._cache[cache_key]
    
    all_issues = self.db.load_issues(lang, topic_filter)
    if not all_issues:
        return []
    
    q = query.strip().lower()
    norm_q = normalize_arabic(q)
    
    # البحث باستخدام عدة طرق
    results = []
    for issue in all_issues:
        # تجميع النص للبحث
        pool = (issue["title"].lower() + " " +
               " ".join(issue["keywords"]).lower() + " " +
               issue["rulings"]["full"].lower() +
               " " + issue["rulings"]["short"].lower() +
               " " + issue["rulings"]["very_short"].lower())
        
        norm_pool = normalize_arabic(pool)
        
        # حساب درجة التطابق
        score = 0
        
        # 1. تطابق كامل للجملة
        if norm_q in norm_pool:
            score += 10
        
        # 2. تطابق الكلمات
        words = norm_q.split()
        for word in words:
            if len(word) > 2 and word in norm_pool:
                score += 3
        
        # 3. تطابق جزئي (بداية كلمة)
        for word in words:
            if len(word) > 3:
                for pool_word in norm_pool.split():
                    if pool_word.startswith(word) or word.startswith(pool_word):
                        score += 1
        
        if score > 0:
            results.append((score, issue))
    
    # ترتيب النتائج حسب درجة التطابق
    results.sort(key=lambda x: x[0], reverse=True)
    sorted_issues = [issue for _, issue in results[:10]]
    
    # بناء النتائج
    final_results = []
    from utils.constants import MADHHAB_NAMES, TOPICS
    
    for issue in sorted_issues:
        cards = []
        per_madhab = issue.get("rulings_by_madhab", {})
        if per_madhab:
            for m in madhabs:
                data = per_madhab.get(m)
                if data:
                    answer = data.get(level, data.get("full", ""))
                    if answer:
                        cards.append({
                            "label": MADHHAB_NAMES[m][lang],
                            "answer": answer,
                            "note": T["note_madhab"].format(MADHHAB_NAMES[m][lang]),
                        })
        
        if not cards:
            cards.append({
                "label": TOPICS[issue["topic"]][lang],
                "answer": issue["rulings"].get(level, issue["rulings"]["full"]),
                "note": T["note_general"],
            })
        
        final_results.append(SearchResult(
            title=issue["title"],
            topic=TOPICS[issue["topic"]][lang],
            cards=cards
        ))
    
    self._cache[cache_key] = final_results
    return final_results
