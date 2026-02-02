# main.py
import telebot
from telebot import types
import time
from threading import Thread
import signal
import sys
import os
from concurrent.futures import ThreadPoolExecutor

from config import TOKEN, MAX_WORKERS
from cache_manager import cache
import handlers.user_handlers as user_handlers
import handlers.admin_handlers as admin_handlers
import handlers.callback_handlers as callback_handlers
import handlers.chat_handlers as chat_handlers
import handlers.admin_management as admin_management
from utils.helpers import *
# الحل السريع: خادم ويب بسيط
from flask import Flask
import threading

# إنشاء تطبيق Flask بسيط
simple_app = Flask(__name__)

@simple_app.route('/')
def home():
    return "🤖 Medical Bot is Running"

@simple_app.route('/health')
def health():
    return "OK", 200

def run_simple_server():
    """تشغيل خادم بسيط"""
    import os
    port = int(os.environ.get('PORT', 8080))
    simple_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# بدء الخادم في thread منفصل
server_thread = threading.Thread(target=run_simple_server, daemon=True)
server_thread.start()
print("✅ خادم الويب يعمل على port 8080")
# تهيئة البوت
bot = telebot.TeleBot(TOKEN)

# إنشاء ThreadPoolExecutor للعمليات المتوازية
executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

# وظيفة لحفظ البيانات بشكل دوري
def auto_save():
    while True:
        time.sleep(30)
        try:
            if cache.save_all():
                print("💾 تم الحفظ التلقائي للبيانات")
        except Exception as e:
            print(f"خطأ في الحفظ التلقائي: {e}")

# وظيفة لإبقاء البوت نشطًا (مهم لـ Render)
def keep_alive():
    """إرسال طلبات دورية لمنع النوم على Render"""
    while True:
        time.sleep(650)  # كل 5 دقائق
        try:
            # مجرد استدعاء بسيط لإبقاء البوت نشط
            print("🔄 إبقاء البوت نشطًا...")
        except Exception as e:
            print(f"خطأ في keep_alive: {e}")

# دالة مساعدة للتحقق من المحادثات النشطة
def is_user_in_active_chat(user_id):
    """التحقق إذا كان المستخدم في محادثة نشطة"""
    if "active_chats" not in cache.data:
        return False
    
    for chat_data in cache.data["active_chats"].values():
        if chat_data["user_id"] == user_id or chat_data["admin_id"] == user_id:
            return True
    return False

# ========== معالجات الرسائل ==========

@bot.message_handler(commands=['start'])
def handle_start(message):
    executor.submit(user_handlers.send_welcome, message, bot)

@bot.message_handler(func=lambda message: message.text == '🩺 طلب استشارة طبية')
def handle_request_consultation(message):
    executor.submit(user_handlers.request_consultation, message, bot)

@bot.message_handler(func=lambda message: message.text == '📝 استشارة برسالة')
def handle_message_consultation_start(message):
    executor.submit(user_handlers.message_consultation, message, bot)

@bot.message_handler(func=lambda message: message.text == '💬 دردشة حية مع دكتور')
def handle_live_chat_request(message):
    executor.submit(user_handlers.live_chat_request, message, bot)

@bot.message_handler(func=lambda message: message.text == '❌ إلغاء الانتظار')
def handle_cancel_waiting(message):
    executor.submit(user_handlers.cancel_waiting, message, bot)

@bot.message_handler(func=lambda message: message.text == '🔙 رجوع')
def handle_go_back(message):
    executor.submit(user_handlers.go_back, message, bot)

@bot.message_handler(func=lambda message: message.text == '⏹️ إنهاء الجلسة')
def handle_end_session(message):
    executor.submit(admin_handlers.end_session, message, bot)

@bot.message_handler(func=lambda message: str(message.from_user.id) in cache.data.get("message_consultations", {}))
def handle_message_consultation_process(message):
    executor.submit(user_handlers.handle_message_consultation, message, bot)

@bot.message_handler(func=lambda message: is_admin(message.from_user.id) and 
                   (str(message.from_user.id) not in cache.admins["admins"] or not cache.admins["admins"][str(message.from_user.id)]["name"]))
def handle_register_admin(message):
    executor.submit(admin_handlers.register_admin, message, bot)

@bot.message_handler(func=lambda message: is_admin(message.from_user.id) and message.text == '📋 طلبات الاستشارات')
def handle_admin_consultations(message):
    executor.submit(admin_handlers.handle_admin_message, message, bot)

@bot.message_handler(func=lambda message: is_super_admin(message.from_user.id) and 
                   message.text in ['📋 قائمة الأدمنز', '➕ إضافة أدمن', '🗑️ حذف أدمن', '🏠 القائمة الرئيسية'])
def handle_admin_management_commands(message):
    executor.submit(admin_management.handle_admin_management, message, bot)

@bot.message_handler(func=lambda message: message.from_user.id in admin_management.admin_states)
def handle_admin_states_messages(message):
    if admin_management.handle_admin_states(message, bot):
        return
    executor.submit(chat_handlers.handle_chat_messages, message, bot)

# معالجة الرسائل العامة
@bot.message_handler(func=lambda message: True)
def handle_general_chat(message):
    user_id = message.from_user.id
    message_text = message.text
    
    # تجاهل الأوامر والأزرار
    if message_text.startswith('/') or message_text in ['⏹️ إنهاء الجلسة', '🩺 طلب استشارة طبية', 
                                                       '📝 استشارة برسالة', '💬 دردشة حية مع دكتور', 
                                                       '🔙 رجوع', '❌ إلغاء الانتظار', '📋 طلبات الاستشارات',
                                                       '📋 قائمة الأدمنز', '➕ إضافة أدمن', '🗑️ حذف أدمن',
                                                       '🏠 القائمة الرئيسية']:
        return
    
    # إذا كان المستخدم في محادثة نشطة
    if is_user_in_active_chat(user_id):
        executor.submit(chat_handlers.handle_chat_messages, message, bot)
    # إذا كان أدمن (وليس في محادثة نشطة)
    elif is_admin(user_id):
        executor.submit(admin_handlers.handle_admin_message, message, bot)
    # إذا كان مستخدم عادي (وليس في محادثة)
    else:
        executor.submit(chat_handlers.handle_chat_messages, message, bot)

# ========== معالجات ال callbacks ==========

@bot.callback_query_handler(func=lambda call: call.data.startswith('reply_msg_'))
def handle_reply_callback(call):
    executor.submit(callback_handlers.handle_reply_message, call, bot)

@bot.callback_query_handler(func=lambda call: call.data.startswith('accept_chat_'))
def handle_accept_chat_callback(call):
    executor.submit(callback_handlers.handle_accept_chat, call, bot)

@bot.callback_query_handler(func=lambda call: call.data.startswith('remove_admin_') or call.data == 'cancel_remove')
def handle_remove_admin_callback(call):
    executor.submit(admin_management.handle_remove_admin_callback, call, bot)

# ========== إدارة الإغلاق ==========

def graceful_shutdown(signum, frame):
    """إغلاق آمن للبرنامج"""
    print("\n" + "="*50)
    print("🔄 جاري الحفظ والإغلاق...")
    print("="*50)
    cache.save_all(force=True)
    executor.shutdown(wait=True)
    print("✅ تم الإغلاق بنجاح")
    sys.exit(0)

# ========== تشغيل البوت ==========

def run_bot():
    """تشغيل البوت مع معالجة الأخطاء"""
    # تسجيل معالج الإغلاق الآمن
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)
    
    # بدء حفظ البيانات التلقائي في خيط منفصل
    save_thread = Thread(target=auto_save, daemon=True)
    save_thread.start()
    
    # بدء خيط إبقاء البوت نشطًا
    keep_alive_thread = Thread(target=keep_alive, daemon=True)
    keep_alive_thread.start()
    
    print("=" * 50)
    print("🚀 بدء تشغيل بوت الاستشارات الطبية...")
    print("=" * 50)
    
    print(f"\n📊 إحصائيات النظام:")
    print(f"   ✅ عدد الأدمنز المسجلين: {len(cache.admins['admins'])}")
    print(f"   ✅ عدد المستخدمين: {len(cache.data.get('user_names', {}))}")
    print(f"   ✅ عدد المحادثات النشطة: {len(cache.data.get('active_chats', {}))}")
    print(f"   ✅ عدد المستخدمين في الانتظار: {len(cache.data.get('waiting_list', []))}")
    print(f"   ✅ عدد الخيوط العاملين: {MAX_WORKERS}")
    
    # طباعة جميع الأدمنز
    print("\n📋 قائمة الأدمنز:")
    if cache.admins["admins"]:
        for admin_id, admin_data in cache.admins["admins"].items():
            print(f"   👨‍⚕️ {admin_data['name']} (ID: {admin_id})")
    else:
        print("   ❌ لا يوجد أدمنز مسجلين")
    
    print("\n" + "=" * 50)
    print("🔍 جاري الاستماع للرسائل...")
    print("=" * 50)
    
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20, long_polling_timeout=20)
        except Exception as e:
            print(f"\n❌ خطأ في polling: {e}")
            print("🔄 إعادة المحاولة بعد 5 ثواني...")
            time.sleep(5)

if __name__ == "__main__":
    # إنشاء مجلد البيانات إذا لم يكن موجوداً
    os.makedirs('data', exist_ok=True)
    
    # التحقق من وجود التوكن
    if not TOKEN or TOKEN == 'YOUR_BOT_TOKEN_HERE':
        print("❌ خطأ: لم تقم بتعيين التوكن في config.py")
        print("يرجى تعيين التوكن الصحيح في ملف config.py")
        exit(1)
    
    run_bot()
