# config.py
import os

# الحصول على التوكن من متغيرات البيئة أو استخدام القيمة الافتراضية
TOKEN = os.environ.get('BOT_TOKEN', 'التوكن_الافتراضي_هنا')

# ملفات التخزين
DATA_FILE = 'data/bot_data.json'
ADMINS_FILE = 'data/admins.json'
MESSAGE_IDS_FILE = 'data/message_ids.json'

# إعدادات الأداء
MAX_WORKERS = 10
AUTO_SAVE_INTERVAL = 30  # ثانية

# إعدادات الأدمنز
# الحصول من متغير البيئة أو استخدام الافتراضي
SUPER_ADMIN_ID = int(os.environ.get('SUPER_ADMIN_ID', '123456789'))