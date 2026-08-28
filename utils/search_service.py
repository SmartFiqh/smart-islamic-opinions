# utils/search_service.py
"""خدمة البحث"""

from typing import List, Dict
from dataclasses import dataclass
from utils.text_utils import normalize_arabic

@dataclass
class SearchResult:
    title: str
    topic: str
    cards: List[Dict[str, str]]

class SearchService:
    def __init__(self, db, ai):
        self.db = db
        self.ai = ai
        self._cache = {}
    
    def search(self, query: str, topic_filter: str, madhabs: List[str], 
               level: str, lang: str, T: Dict) -> List[SearchResult]:
        """البحث عن المسائل الفقهية"""
        if not query:
            return []
        
        cache_key = f"{query}|{topic_filter}|{','.join(madhabs)}|{level}|{lang}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # تحميل المسائل من قاعدة البيانات
        all_issues = self.db.load_issues(lang, topic_filter)
        if not all_issues:
            return []
        
        q = query.strip().lower()
        norm_q = normalize_arabic(q)
        
        # البحث النصي مع التطبيع
        results = []
        for issue in all_issues:
            pool = (issue["title"].lower() + " " +
                   " ".join(issue["keywords"]).lower() + " " +
                   issue["rulings"]["full"].lower())
            
            norm_pool = normalize_arabic(pool)
            
            # فحص التطابق
            if norm_q in norm_pool:
                results.append(issue)
            else:
                # فحص الكلمات
                words = norm_q.split()
                if any(w in norm_pool for w in words if len(w) > 2):
                    results.append(issue)
        
        # بناء النتائج
        final_results = []
        from utils.constants import MADHHAB_NAMES, TOPICS
        
        for issue in results:
            cards = []
            per_madhab = issue.get("rulings_by_madhab", {})
            if per_madhab:
                for m in madhabs:
                    data = per_madhab.get(m)
                    if data:
                        cards.append({
                            "label": MADHHAB_NAMES[m][lang],
                            "answer": data.get(level, data.get("full", "")),
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
