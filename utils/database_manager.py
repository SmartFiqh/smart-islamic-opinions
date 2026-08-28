# utils/database_manager.py
"""إدارة قاعدة البيانات"""

import sqlite3
import json
import csv
import io
import os
from pathlib import Path
from typing import List, Dict, Optional

DB_PATH = "database/fiqh.db"

class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._ensure_directory()
        self._init_db()
        self._seed_data()  # إضافة بيانات أولية
    
    def _ensure_directory(self):
        """تأكد من وجود مجلد database"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(exist_ok=True)
    
    def _get_connection(self):
        """الحصول على اتصال بقاعدة البيانات"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        """تهيئة قاعدة البيانات"""
        with self._get_connection() as conn:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS issues (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT,
                    title_ar TEXT, title_en TEXT, title_fr TEXT, 
                    title_fa TEXT, title_ms TEXT, title_ur TEXT,
                    keywords_ar TEXT, keywords_en TEXT, keywords_fr TEXT, 
                    keywords_fa TEXT, keywords_ms TEXT, keywords_ur TEXT,
                    ruling_vs_ar TEXT, ruling_s_ar TEXT, ruling_f_ar TEXT,
                    ruling_vs_en TEXT, ruling_s_en TEXT, ruling_f_en TEXT,
                    ruling_vs_fr TEXT, ruling_s_fr TEXT, ruling_f_fr TEXT,
                    ruling_vs_fa TEXT, ruling_s_fa TEXT, ruling_f_fa TEXT,
                    ruling_vs_ms TEXT, ruling_s_ms TEXT, ruling_f_ms TEXT,
                    ruling_vs_ur TEXT, ruling_s_ur TEXT, ruling_f_ur TEXT,
                    rulings_by_madhab_ar JSON, rulings_by_madhab_en JSON, 
                    rulings_by_madhab_fr JSON, rulings_by_madhab_fa JSON, 
                    rulings_by_madhab_ms JSON, rulings_by_madhab_ur JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            c.execute('''
                CREATE TABLE IF NOT EXISTS reference_chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_title TEXT,
                    madhab_tag TEXT,
                    chunk_text TEXT,
                    embedding JSON,
                    added_at TEXT,
                    chunk_hash TEXT UNIQUE
                )
            ''')
            
            c.execute('CREATE INDEX IF NOT EXISTS idx_issues_topic ON issues(topic)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_chunks_source ON reference_chunks(source_title)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_chunks_madhab ON reference_chunks(madhab_tag)')
            
            conn.commit()
    
    def _seed_data(self):
        """إضافة بيانات أولية إلى قاعدة البيانات"""
        with self._get_connection() as conn:
            c = conn.cursor()
            
            # التحقق من وجود بيانات
            c.execute("SELECT COUNT(*) FROM issues")
            if c.fetchone()[0] > 0:
                return
            
            # بيانات أولية
            issues = [
                {
                    "topic": "ibadat",
                    "title_ar": "الطهارة",
                    "title_en": "Purity (Taharah)",
                    "title_fr": "La pureté (Taharah)",
                    "title_fa": "طهارت",
                    "title_ms": "Kesucian (Taharah)",
                    "title_ur": "طہارت",
                    "keywords_ar": "طهارة,وضوء,غسل,نجاسة,تيمم",
                    "keywords_en": "purity,ablution,ritual bath,impurity,dry ablution",
                    "keywords_fr": "pureté,ablution,bain rituel,impureté,ablution sèche",
                    "keywords_fa": "طهارت,وضو,غسل,نجاست,تیمم",
                    "keywords_ms": "kesucian,wuduk,mandi,najis,tayammum",
                    "keywords_ur": "طہارت,وضو,غسل,نجاست,تیمم",
                    "ruling_vs_ar": "شرط صحة الصلاة",
                    "ruling_s_ar": "الطهارة شرط لصحة الصلاة عند جميع المذاهب",
                    "ruling_f_ar": "الطهارة من الحدث الأكبر والأصغر شرط أساسي لصحة الصلاة، ويجب على المسلم أن يتطهر بالماء أو التيمم عند تعذره.",
                    "ruling_vs_en": "Condition for prayer validity",
                    "ruling_s_en": "Purity is a condition for the validity of prayer in all schools",
                    "ruling_f_en": "Purity from major and minor impurities is a fundamental condition for the validity of prayer.",
                    "ruling_vs_fr": "Condition pour la validité de la prière",
                    "ruling_s_fr": "La pureté est une condition pour la validité de la prière",
                    "ruling_f_fr": "La pureté des impuretés majeures et mineures est une condition fondamentale pour la validité de la prière.",
                    "ruling_vs_fa": "شرط صحت نماز",
                    "ruling_s_fa": "طهارت شرط صحت نماز است",
                    "ruling_f_fa": "طهارت از حدث اکبر و اصغر شرط اساسی صحت نماز است.",
                    "ruling_vs_ms": "Syarat sah solat",
                    "ruling_s_ms": "Kesucian adalah syarat sah solat",
                    "ruling_f_ms": "Kesucian dari hadas besar dan kecil adalah syarat asas untuk sahnya solat.",
                    "ruling_vs_ur": "نماز کی صحت کے لیے شرط",
                    "ruling_s_ur": "طہارت نماز کی صحت کے لیے شرط ہے",
                    "ruling_f_ur": "طہارت نماز کی صحت کے لیے بنیادی شرط ہے۔",
                    "rulings_by_madhab_ar": json.dumps({
                        "maliki": {"very_short": "شرط", "short": "شرط لصحة الصلاة", "full": "الطهارة شرط لصحة الصلاة عند المالكية، وتجب إزالة النجاسة."},
                        "shafii": {"very_short": "شرط", "short": "شرط لصحة الصلاة", "full": "الطهارة شرط لصحة الصلاة عند الشافعية، ويجب الوضوء والغسل."},
                        "hanafi": {"very_short": "شرط", "short": "شرط لصحة الصلاة", "full": "الطهارة شرط لصحة الصلاة عند الحنفية، ويجب إزالة النجاسة والحدث."},
                        "hanbali": {"very_short": "شرط", "short": "شرط لصحة الصلاة", "full": "الطهارة شرط لصحة الصلاة عند الحنابلة، وتجب إزالة النجاسة."},
                        "jafari": {"very_short": "شرط", "short": "شرط لصحة الصلاة", "full": "الطهارة شرط لصحة الصلاة عند الجعفرية، ويجب الوضوء والغسل."},
                        "ibadi": {"very_short": "شرط", "short": "شرط لصحة الصلاة", "full": "الطهارة شرط لصحة الصلاة عند الإباضية."}
                    }),
                    "rulings_by_madhab_en": "{}",
                    "rulings_by_madhab_fr": "{}",
                    "rulings_by_madhab_fa": "{}",
                    "rulings_by_madhab_ms": "{}",
                    "rulings_by_madhab_ur": "{}"
                },
                {
                    "topic": "ibadat",
                    "title_ar": "صلاة الجماعة",
                    "title_en": "Congregational Prayer",
                    "title_fr": "Prière en congrégation",
                    "title_fa": "نماز جماعت",
                    "title_ms": "Solat Berjemaah",
                    "title_ur": "نماز باجماعت",
                    "keywords_ar": "جماعة,مسجد,رجال,صلاة,فرض,سنة,واجب",
                    "keywords_en": "congregation,mosque,men,prayer,obligatory,sunnah",
                    "keywords_fr": "congrégation,mosquée,hommes,prière,obligatoire,sunna",
                    "keywords_fa": "جماعت,مسجد,مردان,نماز,فرض,سنت,واجب",
                    "keywords_ms": "jemaah,masjid,lelaki,solat,fardu,sunnah,wajib",
                    "keywords_ur": "جماعت,مسجد,مرد,نماز,فرض,سنت,واجب",
                    "ruling_vs_ar": "سنة مؤكدة",
                    "ruling_s_ar": "سنة مؤكدة عند الجمهور، واجبة عند الحنفية",
                    "ruling_f_ar": "تجب صلاة الجماعة في المسجد على الرجال عند جمهور الفقهاء؛ فهي فرض عين عند الحنابلة، واجب مؤكد عند الحنفية، فرض كفاية عند المالكية والشافعية، ومستحبة تأكيداً عند الجعفرية.",
                    "ruling_vs_en": "Emphasized Sunnah",
                    "ruling_s_en": "Emphasized sunnah for most jurists, obligatory for the Hanafis",
                    "ruling_f_en": "Congregational prayer in the mosque is required of men according to the majority of jurists.",
                    "ruling_vs_fr": "Sunna fortement recommandée",
                    "ruling_s_fr": "Sunna fortement recommandée pour la majorité, obligatoire pour les hanafites",
                    "ruling_f_fr": "La prière en congrégation à la mosquée est requise des hommes selon la majorité des juristes.",
                    "ruling_vs_fa": "سنت مؤکد",
                    "ruling_s_fa": "سنت مؤکد نزد جمهور، واجب نزد حنفیان",
                    "ruling_f_fa": "نماز جماعت در مسجد بر مردان واجب است به اتفاق جمهور فقها.",
                    "ruling_vs_ms": "Sunnah muakkadah",
                    "ruling_s_ms": "Sunnah muakkadah bagi majoriti, wajib bagi Hanafi",
                    "ruling_f_ms": "Solat berjemaah di masjid diwajibkan ke atas lelaki menurut majoriti ulama.",
                    "ruling_vs_ur": "سنت مؤکدہ",
                    "ruling_s_ur": "سنت مؤکدہ نزد جمہور، واجب نزد احناف",
                    "ruling_f_ur": "مسجد میں نماز باجماعت مردوں پر جمہور فقہاء کے نزدیک واجب ہے.",
                    "rulings_by_madhab_ar": json.dumps({
                        "maliki": {"very_short": "فرض كفاية", "short": "فرض كفاية على أهل الحي، سنة مؤكدة للفرد", "full": "فرض كفاية على أهل الحي؛ وفي حق الفرد الواحد سنة مؤكدة لا يُكره تركها إلا لمن واظب عليه."},
                        "shafii": {"very_short": "سنة مؤكدة", "short": "فرض كفاية على المجتمع، سنة مؤكدة للفرد", "full": "فرض كفاية على المجتمع ككل، وسنة مؤكدة في حق الفرد؛ وهو الأصح في المذهب."},
                        "hanafi": {"very_short": "واجب", "short": "واجبة على كل رجل حر بالغ عاقل", "full": "واجبة وجوباً غير ملزم على كل رجل حر بالغ عاقل قادر؛ وتركها بلا عذر مكروه تحريماً عند المتأخرين."},
                        "hanbali": {"very_short": "فرض عين", "short": "فرض عين على كل رجل قادر", "full": "فرض عين على كل رجل مكلف قادر؛ لا يجوز تركها إلا لعذر شرعي معتبر."},
                        "zahiri": {"very_short": "فرض عين", "short": "فرض عين؛ ظاهر الأمر النبوي يقتضي الوجوب", "full": "فرض عين أخذاً بظاهر الأمر النبوي بالمحافظة عليها، دون تأويل يصرفه عن الوجوب."},
                        "jafari": {"very_short": "مستحب مؤكد", "short": "مستحبة استحباباً مؤكداً في زمن الغيبة", "full": "مستحبة استحباباً مؤكداً وليست واجبة عيناً في زمن الغيبة الكبرى، وثوابها عظيم."},
                        "zaidi": {"very_short": "فرض كفاية", "short": "قريب من رأي أهل السنة في تأكيدها", "full": "فرض كفاية، ويقترب الرأي الزيدي من الرأي السني في التأكيد على المحافظة عليها جماعة."},
                        "ibadi": {"very_short": "سنة مؤكدة", "short": "من أعلام الدين ولا تُترك باستمرار", "full": "من أعلام الدين الظاهرة، سنة مؤكدة لا ينبغي تركها باستمرار وإن لم تكن شرطاً لصحة الصلاة."}
                    }),
                    "rulings_by_madhab_en": "{}",
                    "rulings_by_madhab_fr": "{}",
                    "rulings_by_madhab_fa": "{}",
                    "rulings_by_madhab_ms": "{}",
                    "rulings_by_madhab_ur": "{}"
                },
                {
                    "topic": "ibadat",
                    "title_ar": "الوضوء",
                    "title_en": "Ablution (Wudu)",
                    "title_fr": "Ablution (Wudu)",
                    "title_fa": "وضو",
                    "title_ms": "Wuduk",
                    "title_ur": "وضو",
                    "keywords_ar": "وضوء,طهارة,صلاة,حدث,غسل,مسح",
                    "keywords_en": "ablution,purity,prayer,impurity,wash,wipe",
                    "keywords_fr": "ablution,pureté,prière,impureté,laver,essuyer",
                    "keywords_fa": "وضو,طهارت,نماز,حدث,شستن,مسح",
                    "keywords_ms": "wuduk,kesucian,solat,hadas,basuh,sapu",
                    "keywords_ur": "وضو,طہارت,نماز,حدث,دھونا,مسح",
                    "ruling_vs_ar": "شرط صحة الصلاة",
                    "ruling_s_ar": "الوضوء شرط لصحة الصلاة عند جميع المذاهب",
                    "ruling_f_ar": "الوضوء شرط أساسي لصحة الصلاة، ويجب على المسلم أن يتوضأ قبل كل صلاة، وتختلف فروض الوضوء بين المذاهب.",
                    "ruling_vs_en": "Condition for prayer",
                    "ruling_s_en": "Ablution is a condition for the validity of prayer in all schools",
                    "ruling_f_en": "Ablution is a fundamental condition for the validity of prayer.",
                    "ruling_vs_fr": "Condition pour la prière",
                    "ruling_s_fr": "L'ablution est une condition pour la validité de la prière",
                    "ruling_f_fr": "L'ablution est une condition fondamentale pour la validité de la prière.",
                    "ruling_vs_fa": "شرط نماز",
                    "ruling_s_fa": "وضو شرط صحت نماز است",
                    "ruling_f_fa": "وضو شرط اساسی صحت نماز است.",
                    "ruling_vs_ms": "Syarat solat",
                    "ruling_s_ms": "Wuduk adalah syarat sah solat",
                    "ruling_f_ms": "Wuduk adalah syarat asas untuk sahnya solat.",
                    "ruling_vs_ur": "نماز کی شرط",
                    "ruling_s_ur": "وضو نماز کی صحت کے لیے شرط ہے",
                    "ruling_f_ur": "وضو نماز کی صحت کے لیے بنیادی شرط ہے۔",
                    "rulings_by_madhab_ar": json.dumps({
                        "maliki": {"very_short": "شرط", "short": "شرط لصحة الصلاة", "full": "الوضوء شرط لصحة الصلاة عند المالكية، وفرائضه: غسل الوجه واليدين ومسح الرأس وغسل الرجلين."},
                        "shafii": {"very_short": "شرط", "short": "شرط لصحة الصلاة", "full": "الوضوء شرط لصحة الصلاة عند الشافعية، وفرائضه: النية، غسل الوجه، غسل اليدين، مسح الرأس، غسل الرجلين، الترتيب."},
                        "hanafi": {"very_short": "شرط", "short": "شرط لصحة الصلاة", "full": "الوضوء شرط لصحة الصلاة عند الحنفية، وفرائضه: غسل الوجه، غسل اليدين، مسح الرأس، غسل الرجلين."},
                        "hanbali": {"very_short": "شرط", "short": "شرط لصحة الصلاة", "full": "الوضوء شرط لصحة الصلاة عند الحنابلة، وفرائضه: غسل الوجه، غسل اليدين، مسح الرأس، غسل الرجلين، الترتيب."},
                        "jafari": {"very_short": "شرط", "short": "شرط لصحة الصلاة", "full": "الوضوء شرط لصحة الصلاة عند الجعفرية، وفرائضه: غسل الوجه، غسل اليدين، مسح الرأس، غسل الرجلين."}
                    }),
                    "rulings_by_madhab_en": "{}",
                    "rulings_by_madhab_fr": "{}",
                    "rulings_by_madhab_fa": "{}",
                    "rulings_by_madhab_ms": "{}",
                    "rulings_by_madhab_ur": "{}"
                }
            ]
            
            # إدراج البيانات
            for issue in issues:
                c.execute('''
                    INSERT INTO issues (
                        topic, title_ar, title_en, title_fr, title_fa, title_ms, title_ur,
                        keywords_ar, keywords_en, keywords_fr, keywords_fa, keywords_ms, keywords_ur,
                        ruling_vs_ar, ruling_s_ar, ruling_f_ar,
                        ruling_vs_en, ruling_s_en, ruling_f_en,
                        ruling_vs_fr, ruling_s_fr, ruling_f_fr,
                        ruling_vs_fa, ruling_s_fa, ruling_f_fa,
                        ruling_vs_ms, ruling_s_ms, ruling_f_ms,
                        ruling_vs_ur, ruling_s_ur, ruling_f_ur,
                        rulings_by_madhab_ar, rulings_by_madhab_en, rulings_by_madhab_fr,
                        rulings_by_madhab_fa, rulings_by_madhab_ms, rulings_by_madhab_ur
                    ) VALUES (?,?,?,?,?,?,?, ?,?,?,?,?,?, ?,?,?, ?,?,?, ?,?,?, ?,?,?, ?,?,?, ?,?,?, ?,?,?, ?,?,?)
                ''', (
                    issue["topic"], issue["title_ar"], issue["title_en"], issue["title_fr"],
                    issue["title_fa"], issue["title_ms"], issue["title_ur"],
                    issue["keywords_ar"], issue["keywords_en"], issue["keywords_fr"],
                    issue["keywords_fa"], issue["keywords_ms"], issue["keywords_ur"],
                    issue["ruling_vs_ar"], issue["ruling_s_ar"], issue["ruling_f_ar"],
                    issue["ruling_vs_en"], issue["ruling_s_en"], issue["ruling_f_en"],
                    issue["ruling_vs_fr"], issue["ruling_s_fr"], issue["ruling_f_fr"],
                    issue["ruling_vs_fa"], issue["ruling_s_fa"], issue["ruling_f_fa"],
                    issue["ruling_vs_ms"], issue["ruling_s_ms"], issue["ruling_f_ms"],
                    issue["ruling_vs_ur"], issue["ruling_s_ur"], issue["ruling_f_ur"],
                    issue["rulings_by_madhab_ar"], issue["rulings_by_madhab_en"],
                    issue["rulings_by_madhab_fr"], issue["rulings_by_madhab_fa"],
                    issue["rulings_by_madhab_ms"], issue["rulings_by_madhab_ur"]
                ))
            
            conn.commit()
            print("✅ تم إضافة البيانات الأولية إلى قاعدة البيانات")
    
    def load_issues(self, lang: str, topic_filter: str = "all") -> List:
        """تحميل المسائل الفقهية"""
        with self._get_connection() as conn:
            c = conn.cursor()
            
            query = f'''
                SELECT id, topic, title_{lang}, keywords_{lang},
                       ruling_vs_{lang}, ruling_s_{lang}, ruling_f_{lang},
                       rulings_by_madhab_{lang}
                FROM issues
            '''
            params = ()
            if topic_filter != "all":
                query += " WHERE topic = ?"
                params = (topic_filter,)
            
            c.execute(query, params)
            rows = c.fetchall()
            
            issues = []
            for row in rows:
                kw = row[f'keywords_{lang}'].split(',') if row[f'keywords_{lang}'] else []
                issues.append({
                    "id": row['id'],
                    "topic": row['topic'],
                    "title": row[f'title_{lang}'],
                    "keywords": [k.strip() for k in kw if k.strip()],
                    "rulings": {
                        "very_short": row[f'ruling_vs_{lang}'],
                        "short": row[f'ruling_s_{lang}'],
                        "full": row[f'ruling_f_{lang}']
                    },
                    "rulings_by_madhab": json.loads(row[f'rulings_by_madhab_{lang}']) if row[f'rulings_by_madhab_{lang}'] else {}
                })
            return issues
    
    def import_from_csv(self, csv_content: bytes) -> int:
        """استيراد بيانات من CSV"""
        with self._get_connection() as conn:
            c = conn.cursor()
            reader = csv.DictReader(io.StringIO(csv_content.decode('utf-8')))
            count = 0
            
            for row in reader:
                c.execute('''
                    INSERT INTO issues (
                        topic, title_ar, title_en, title_fr, title_fa, title_ms, title_ur,
                        keywords_ar, keywords_en, keywords_fr, keywords_fa, keywords_ms, keywords_ur,
                        ruling_vs_ar, ruling_s_ar, ruling_f_ar,
                        ruling_vs_en, ruling_s_en, ruling_f_en,
                        ruling_vs_fr, ruling_s_fr, ruling_f_fr,
                        ruling_vs_fa, ruling_s_fa, ruling_f_fa,
                        ruling_vs_ms, ruling_s_ms, ruling_f_ms,
                        ruling_vs_ur, ruling_s_ur, ruling_f_ur,
                        rulings_by_madhab_ar, rulings_by_madhab_en, rulings_by_madhab_fr,
                        rulings_by_madhab_fa, rulings_by_madhab_ms, rulings_by_madhab_ur
                    ) VALUES (?,?,?,?,?,?,?, ?,?,?,?,?,?, ?,?,?, ?,?,?, ?,?,?, ?,?,?, ?,?,?, ?,?,?, ?,?,?, ?,?,?)
                ''', (
                    row.get("topic", "other"),
                    row.get("title_ar", ""), row.get("title_en", ""), row.get("title_fr", ""),
                    row.get("title_fa", ""), row.get("title_ms", ""), row.get("title_ur", ""),
                    row.get("keywords_ar", ""), row.get("keywords_en", ""), row.get("keywords_fr", ""),
                    row.get("keywords_fa", ""), row.get("keywords_ms", ""), row.get("keywords_ur", ""),
                    row.get("ruling_vs_ar", ""), row.get("ruling_s_ar", ""), row.get("ruling_f_ar", ""),
                    row.get("ruling_vs_en", ""), row.get("ruling_s_en", ""), row.get("ruling_f_en", ""),
                    row.get("ruling_vs_fr", ""), row.get("ruling_s_fr", ""), row.get("ruling_f_fr", ""),
                    row.get("ruling_vs_fa", ""), row.get("ruling_s_fa", ""), row.get("ruling_f_fa", ""),
                    row.get("ruling_vs_ms", ""), row.get("ruling_s_ms", ""), row.get("ruling_f_ms", ""),
                    row.get("ruling_vs_ur", ""), row.get("ruling_s_ur", ""), row.get("ruling_f_ur", ""),
                    row.get("rulings_by_madhab_ar", "{}"), row.get("rulings_by_madhab_en", "{}"),
                    row.get("rulings_by_madhab_fr", "{}"), row.get("rulings_by_madhab_fa", "{}"),
                    row.get("rulings_by_madhab_ms", "{}"), row.get("rulings_by_madhab_ur", "{}")
                ))
                count += 1
            
            conn.commit()
            return count
    
    def add_reference_chunk(self, title: str, madhab_tag: str, chunk: str, embedding: List[float]) -> bool:
        """إضافة مقطع مرجعي"""
        import hashlib
        import datetime
        
        chunk_hash = hashlib.md5(chunk.encode()).hexdigest()
        now = datetime.datetime.utcnow().isoformat()
        
        with self._get_connection() as conn:
            c = conn.cursor()
            try:
                c.execute(
                    """INSERT INTO reference_chunks 
                       (source_title, madhab_tag, chunk_text, embedding, added_at, chunk_hash) 
                       VALUES (?,?,?,?,?,?)""",
                    (title, madhab_tag or "", chunk, json.dumps(embedding), now, chunk_hash)
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False
    
    def get_reference_chunks(self) -> List[Dict]:
        """الحصول على جميع مقاطع المراجع"""
        with self._get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT id, source_title, madhab_tag, chunk_text, embedding FROM reference_chunks")
            rows = c.fetchall()
            return [dict(row) for row in rows]
    
    def count_reference_chunks(self) -> int:
        """عدد مقاطع المراجع"""
        with self._get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM reference_chunks")
            return c.fetchone()[0]
    
    def list_reference_sources(self) -> List[tuple]:
        """قائمة مصادر المراجع"""
        with self._get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT source_title, COUNT(*) FROM reference_chunks GROUP BY source_title")
            return c.fetchall()
