# utils/helpers.py
from cache_manager import cache
import datetime
from telebot import types
from config import SUPER_ADMIN_ID

def is_admin(user_id):
    return str(user_id) in cache.admins["admins"]

def is_super_admin(user_id):
    """التحقق إذا كان المستخدم هو المشرف الرئيسي"""
    return str(user_id) == str(7616340848)

def get_admin_name(admin_id):
    admin_id_str = str(admin_id)
    if admin_id_str in cache.admins["admins"]:
        return cache.admins["admins"][admin_id_str]["name"]
    return "غير معروف"

def get_user_name(user_id):
    user_id_str = str(user_id)
    if "user_names" in cache.data and user_id_str in cache.data["user_names"]:
        return cache.data["user_names"][user_id_str]
    return f"مستخدم_{user_id}"

def delete_consultation_buttons(user_id, bot):
    """حذف أزرار الرد لجميع الأدمنز عند الرد على رسالة"""
    user_id_str = str(user_id)
    if "consultation_msgs" in cache.message_ids and user_id_str in cache.message_ids["consultation_msgs"]:
        for admin_id_str, msg_id in cache.message_ids["consultation_msgs"][user_id_str].items():
            try:
                bot.edit_message_reply_markup(
                    chat_id=int(admin_id_str),
                    message_id=msg_id,
                    reply_markup=None
                )
            except:
                pass
        if user_id_str in cache.message_ids["consultation_msgs"]:
            del cache.message_ids["consultation_msgs"][user_id_str]
        cache.save_all(force=True)

def delete_live_chat_buttons(user_id, bot):
    """حذف أزرار قبول الدردشة لجميع الأدمنز عند قبول طلب"""
    user_id_str = str(user_id)
    if "live_chat_msgs" in cache.message_ids and user_id_str in cache.message_ids["live_chat_msgs"]:
        for admin_id_str, msg_id in cache.message_ids["live_chat_msgs"][user_id_str].items():
            try:
                bot.edit_message_reply_markup(
                    chat_id=int(admin_id_str),
                    message_id=msg_id,
                    reply_markup=None
                )
            except:
                pass
        if user_id_str in cache.message_ids["live_chat_msgs"]:
            del cache.message_ids["live_chat_msgs"][user_id_str]
        cache.save_all(force=True)

def save_data():
    """وظيفة للحفظ الفوري"""
    return cache.save_all(force=True)

def get_current_time():
    """الحصول على الوقت الحالي بتنسيق مناسب"""
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def create_back_button():
    """إنشاء زر الرجوع"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton('🔙 رجوع')
    markup.add(btn)
    return markup

def create_main_menu():
    """إنشاء القائمة الرئيسية"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton('🩺 طلب استشارة طبية')
    markup.add(btn)
    return markup

def create_admin_menu():
    """إنشاء قائمة الأدمنز"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton('📋 قائمة الأدمنز')
    btn2 = types.KeyboardButton('➕ إضافة أدمن')
    btn3 = types.KeyboardButton('🗑️ حذف أدمن')
    btn4 = types.KeyboardButton('🏠 القائمة الرئيسية')
    markup.add(btn1, btn2, btn3, btn4)
    return markup

def add_admin(admin_id, admin_name, added_by="system"):
    """إضافة أدمن جديد"""
    admin_id_str = str(admin_id)
    
    if admin_id_str not in cache.admins["admins"]:
        cache.admins["admins"][admin_id_str] = {
            "name": admin_name,
            "active": True,
            "added_by": added_by,
            "added_date": datetime.datetime.now().isoformat(),
            "permissions": {
                "can_view_consultations": True,
                "can_reply_consultations": True,
                "can_accept_chats": True,
                "can_manage_admins": is_super_admin(int(admin_id))
            }
        }
        cache.admins["admin_names"][admin_name] = admin_id_str
        save_data()
        return True
    return False

def remove_admin(admin_id, removed_by="system"):
    """إزالة أدمن"""
    admin_id_str = str(admin_id)
    
    if admin_id_str in cache.admins["admins"]:
        admin_name = cache.admins["admins"][admin_id_str]["name"]
        del cache.admins["admins"][admin_id_str]
        
        if admin_name in cache.admins["admin_names"]:
            del cache.admins["admin_names"][admin_name]
        
        save_data()
        return True
    return False

def get_all_admins():
    """الحصول على قائمة جميع الأدمنز"""
    return cache.admins["admins"]

def get_admin_info(admin_id):
    """الحصول على معلومات أدمن محدد"""
    admin_id_str = str(admin_id)
    if admin_id_str in cache.admins["admins"]:
        return cache.admins["admins"][admin_id_str]
    return None

def check_admin_status(user_id):
    """تصحيح حالة الأدمن"""
    user_id_str = str(user_id)
    super_admin_id = str(SUPER_ADMIN_ID)
    
    print(f"\n🔍 تصحيح صلاحيات المستخدم {user_id}:")
    print(f"   - SUPER_ADMIN_ID في config: {super_admin_id}")
    print(f"   - هو أدمن رئيسي: {user_id_str == super_admin_id}")
    print(f"   - هو أدمن عادي: {is_admin(user_id)}")
    
    if user_id_str == super_admin_id:
        print("   ✅ يجب يظهر له قائمة الأدمنز!")
    else:
        print("   ❌ ما راح يظهر له قائمة الأدمنز")
    
    return user_id_str == super_admin_id

def debug_super_admin():
    """تصحيح SUPER_ADMIN_ID"""
    import os
    
    print("\n" + "="*50)
    print("🔍 تصحيح SUPER_ADMIN_ID:")
    
    # 1. القيمة من Environment Variables
    env_value = os.environ.get('SUPER_ADMIN_ID')
    print(f"   من Environment: '{env_value}'")
    print(f"   نوع البيانات: {type(env_value)}")
    
    # 2. القيمة من config.py
    print(f"   من config.py: {SUPER_ADMIN_ID}")
    print(f"   نوع config: {type(SUPER_ADMIN_ID)}")
    
    # 3. التحقق
    try:
        if str(SUPER_ADMIN_ID) == str(env_value):
            print("   ✅ القيم متطابقة!")
        else:
            print("   ❌ القيم مختلفة!")
            print(f"      SUPER_ADMIN_ID: {SUPER_ADMIN_ID}")
            print(f"      env: {env_value}")
    except Exception as e:
        print(f"   ⚠️ خطأ في المقارنة: {e}")
    
    print("="*50)
