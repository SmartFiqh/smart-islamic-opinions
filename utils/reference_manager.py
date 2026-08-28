# utils/reference_manager.py
"""إدارة المراجع (RAG)"""

import re
import json
import numpy as np
from typing import List, Dict

class ReferenceManager:
    def __init__(self, db, ai):
        self.db = db
        self.ai = ai
    
    def chunk_text(self, text: str, max_chars: int = 700, overlap: int = 100) -> List[str]:
        """تقسيم النص إلى مقاطع"""
        text = re.sub(r'\s+', ' ', text).strip()
        if not text:
            return []
        chunks = []
        start = 0
        while start < len(text):
            end = start + max_chars
            chunks.append(text[start:end].strip())
            start = end - overlap
        return [c for c in chunks if len(c) > 30]
    
    def add_document(self, title: str, madhab_tag: str, raw_text: str) -> int:
        """إضافة مستند مرجعي وفهرسته"""
        chunks = self.chunk_text(raw_text)
        if not chunks:
            return 0
        
        if not self.ai.available:
            return -1
        
        # توليد التضمينات
        embeddings = []
        for chunk in chunks:
            emb = self.ai.embed_text(chunk)
            if emb:
                embeddings.append(emb)
            else:
                return -1
        
        # تخزين المقاطع
        added = 0
        for chunk, embedding in zip(chunks, embeddings):
            if self.db.add_reference_chunk(title, madhab_tag, chunk, embedding):
                added += 1
        
        return added
    
    def retrieve_relevant_chunks(self, query: str, top_k: int = 5, 
                                 min_similarity: float = 0.55) -> List[Dict]:
        """استرجاع المقاطع ذات الصلة"""
        total = self.db.count_reference_chunks()
        if total == 0:
            return []
        
        if not self.ai.available:
            return []
        
        q_embedding = self.ai.embed_text(query)
        if not q_embedding:
            return []
        
        q_vec = np.array(q_embedding)
        chunks = self.db.get_reference_chunks()
        
        scored = []
        for chunk in chunks:
            try:
                vec = np.array(json.loads(chunk["embedding"]))
                denom = (np.linalg.norm(q_vec) * np.linalg.norm(vec))
                sim = float(np.dot(q_vec, vec) / denom) if denom else 0.0
                
                if sim >= min_similarity:
                    scored.append({
                        "title": chunk["source_title"],
                        "tag": chunk["madhab_tag"],
                        "chunk": chunk["chunk_text"],
                        "score": sim
                    })
            except:
                continue
        
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]
