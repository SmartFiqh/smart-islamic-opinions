# ============================================================
# 📖 بيان - التطبيق الرئيسي (app.py)
# مرشد الآراء الفقهية
# ============================================================

import os
import json
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# تحميل المتغيرات البيئية
load_dotenv()

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================
# 1. تهيئة التطبيق
# ============================================================
app = Flask(__name__, static_folder='.', template_folder='.')
CORS(app)

# ============================================================
# 2. البيانات الافتراضية (يجب تعريفها أولاً)
# ============================================================

def get_default_issues():
    """المسائل الفقهية الافتراضية"""
    return [
        {
            "id": 1,
            "title": "صلاة الجماعة",
            "category": "العبادات",
            "rulings": {
                "very_short": "سنة مؤكدة",
                "short": "سنة مؤكدة عند الجمهور، واجبة عند الحنفية",
                "full": "تجب صلاة الجماعة في المسجد على الرجال عند جمهور الفقهاء؛ فهي فرض عين عند الحنابلة، واجب مؤكد عند الحنفية، فرض كفاية عند المالكية والشافعية، ومستحبة تأكيداً عند الجعفرية في زمن الغيبة."
            },
            "keywords": ["جماعة", "مسجد", "رجال", "صلاة", "فرض", "سنة", "واجب"]
        },
        {
            "id": 2,
            "title": "زكاة الأسهم",
            "category": "المعاملات",
            "rulings": {
                "very_short": "واجبة",
                "short": "زكاة الأسهم واجبة إذا بلغت النصاب",
                "full": "تجب زكاة الأسهم إذا كانت للاستثمار والتجارة، وبلغت قيمتها النصاب (85 جرام ذهب)، وتُحسب بقيمتها السوقية في نهاية الحول، ويُخرج 2.5% من قيمتها."
            },
            "keywords": ["زكاة", "أسهم", "استثمار", "تجارة", "نصاب", "مال"]
        },
        {
            "id": 3,
            "title": "الجمع في السفر",
            "category": "العبادات",
            "rulings": {
                "very_short": "جائز",
                "short": "يجوز جمع الصلاة في السفر للمسافر",
                "full": "يجوز للمسافر جمع صلاة الظهر مع العصر، والمغرب مع العشاء، تقديماً أو تأخيراً، في وقت إحداهما، وذلك تخفيفاً من الله تعالى على المسافرين."
            },
            "keywords": ["جمع", "سفر", "مسافر", "صلاة", "تخفيف", "رخصة"]
        }
    ]

def get_default_glossary():
    """المصطلحات الفقهية الافتراضية"""
    return [
        {"term": "الحلال", "definition": "ما أحله الله ورسوله، وثبوت حله في الكتاب والسنة، وفعله مباح لا إثم فيه."},
        {"term": "الحرام", "definition": "ما حرمه الله ورسوله بنص قطعي، وفاعله آثم مستحق للعقاب."},
        {"term": "المكروه", "definition": "ما طلب الشارع تركه طلباً غير جازم، ويثاب تاركه ولا يعاقب فاعله."},
        {"term": "المستحب", "definition": "ما رغب الشارع في فعله دون إلزام، ويثاب فاعله ولا يعاقب تاركه."},
        {"term": "الفرض", "definition": "ما طلب الشارع فعله طلباً جازماً على كل مكلف، ويثاب فاعله ويعاقب تاركه."}
    ]

def get_default_countries():
    """الدول والمذاهب الافتراضية"""
    return [
        {"country": "🇸🇦 السعودية", "madhab": "الحنبلي", "population": "36.4 مليون"},
        {"country": "🇪🇬 مصر", "madhab": "الشافعي", "population": "112.7 مليون"},
        {"country": "🇲🇦 المغرب", "madhab": "المالكي", "population": "37.8 مليون"},
        {"country": "🇹🇷 تركيا", "madhab": "الحنفي", "population": "87.5 مليون"},
        {"country": "🇮🇷 إيران", "madhab": "الجعفري", "population": "89.8 مليون"},
        {"country": "🇴🇲 عُمان", "madhab": "الإباضي", "population": "4.7 مليون"}
    ]

def get_default_imams():
    """الأئمة المؤسسون الافتراضية"""
    return [
        {"name": "الإمام مالك بن أنس (93-179هـ)", "school": "المذهب المالكي", "scholars": "ابن القاسم، سحنون، ابن رشد، القرافي، خليل بن إسحاق"},
        {"name": "الإمام محمد بن إدريس الشافعي (150-204هـ)", "school": "المذهب الشافعي", "scholars": "المزني، البويطي، النووي، ابن حجر الهيتمي، الرافعي"},
        {"name": "الإمام أحمد بن حنبل (164-241هـ)", "school": "المذهب الحنبلي", "scholars": "أبو بكر الخلال، ابن قدامة، ابن تيمية، ابن القيم، محمد بن عبد الوهاب"},
        {"name": "الإمام أبو حنيفة النعمان (80-150هـ)", "school": "المذهب الحنفي", "scholars": "أبو يوسف، محمد بن الحسن الشيباني، الطحاوي، الكاساني، ابن عابدين"}
    ]

# ============================================================
# 3. تحميل البيانات (بعد تعريف الدوال)
# ============================================================

def load_json_file(filename):
    """تحميل ملف JSON بأمان"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"⚠️ ملف {filename} غير موجود")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"❌ خطأ في قراءة {filename}: {e}")
        return None

# تحميل البيانات من الملفات أو استخدام الافتراضية
issues_data = load_json_file('data/issues.json')
if not issues_data:
    issues_data = get_default_issues()
    logger.info("✅ تم استخدام البيانات الافتراضية للمسائل")

glossary_terms = load_json_file('data/glossary.json')
if not glossary_terms:
    glossary_terms = get_default_glossary()
    logger.info("✅ تم استخدام البيانات الافتراضية للمصطلحات")

countries_data = load_json_file('data/countries.json')
if not countries_data:
    countries_data = get_default_countries()
    logger.info("✅ تم استخدام البيانات الافتراضية للدول")

imams_data = load_json_file('data/imams.json')
if not imams_data:
    imams_data = get_default_imams()
    logger.info("✅ تم استخدام البيانات الافتراضية للأئمة")

# تحميل الترجمات
translations = {}
locales_dir = 'locales'
if os.path.exists(locales_dir):
    for filename in os.listdir(locales_dir):
        if filename.endswith('.json'):
            lang_code = filename.replace('.json', '')
            translations[lang_code] = load_json_file(os.path.join(locales_dir, filename))
            if translations[lang_code]:
                logger.info(f"✅ تم تحميل ترجمة {lang_code}")

# ============================================================
# 4. دوال المساعدة
# ============================================================

def search_issues(query, language='ar', level='full'):
    """البحث في المسائل"""
    if not query:
        return []
    
    query = query.strip().lower()
    results = []
    
    for issue in issues_data:
        title_match = query in issue.get('title', '').lower()
        keyword_match = any(query in kw.lower() for kw in issue.get('keywords', []))
        full_text = issue.get('rulings', {}).get('full', '').lower()
        full_match = query in full_text
        
        if title_match or keyword_match or full_match:
            rulings = issue.get('rulings', {})
            answer = rulings.get(level, rulings.get('full', 'لا توجد إجابة'))
            
            results.append({
                'id': issue.get('id'),
                'title': issue.get('title'),
                'category': issue.get('category'),
                'answer': answer,
                'level': level
            })
    
    return results

# ============================================================
# 5. واجهات API
# ============================================================

@app.route('/')
def index():
    """الصفحة الرئيسية"""
    return send_from_directory('.', 'index.html')

@app.route('/style.css')
def serve_css():
    return send_from_directory('.', 'style.css')

@app.route('/script.js')
def serve_js():
    return send_from_directory('.', 'script.js')

@app.route('/locales/<lang>.json')
def serve_locale(lang):
    return send_from_directory('locales', f'{lang}.json')

@app.route('/api/issues', methods=['GET'])
def api_get_issues():
    return jsonify({'success': True, 'data': issues_data, 'count': len(issues_data)})

@app.route('/api/search', methods=['GET', 'POST'])
def api_search():
    if request.method == 'POST':
        data = request.get_json() or {}
        query = data.get('query', '')
        language = data.get('language', 'ar')
        level = data.get('level', 'full')
    else:
        query = request.args.get('q', '')
        language = request.args.get('lang', 'ar')
        level = request.args.get('level', 'full')
    
    if not query:
        return jsonify({'success': False, 'error': 'الرجاء إدخال نص للبحث'}), 400
    
    results = search_issues(query, language, level)
    return jsonify({'success': True, 'results': results, 'count': len(results)})

@app.route('/api/glossary', methods=['GET'])
def api_get_glossary():
    return jsonify({'success': True, 'data': glossary_terms, 'count': len(glossary_terms)})

@app.route('/api/countries', methods=['GET'])
def api_get_countries():
    return jsonify({'success': True, 'data': countries_data, 'count': len(countries_data)})

@app.route('/api/imams', methods=['GET'])
def api_get_imams():
    return jsonify({'success': True, 'data': imams_data, 'count': len(imams_data)})

@app.route('/api/languages', methods=['GET'])
def api_get_languages():
    languages = [
        {'code': 'ar', 'name': 'العربية', 'flag': '🇸🇦'},
        {'code': 'en', 'name': 'English', 'flag': '🇬🇧'},
        {'code': 'fr', 'name': 'Français', 'flag': '🇫🇷'},
        {'code': 'fa', 'name': 'فارسی', 'flag': '🇮🇷'},
        {'code': 'ur', 'name': 'اُردُو', 'flag': '🇵🇰'},
        {'code': 'ms', 'name': 'Bahasa Melayu', 'flag': '🇲🇾'}
    ]
    return jsonify({'success': True, 'data': languages})

@app.route('/api/health', methods=['GET'])
def api_health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'data': {
            'issues': len(issues_data),
            'glossary': len(glossary_terms),
            'countries': len(countries_data),
            'imams': len(imams_data),
            'languages': len(translations)
        }
    })

# ============================================================
# 6. تشغيل التطبيق
# ============================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"🚀 تشغيل تطبيق بيان على المنفذ {port}")
    logger.info(f"📚 عدد المسائل: {len(issues_data)}")
    logger.info(f"📖 عدد المصطلحات: {len(glossary_terms)}")
    logger.info(f"🌍 عدد الدول: {len(countries_data)}")
    logger.info(f"🕌 عدد الأئمة: {len(imams_data)}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
