# handlers/callback_handlers.py
from telebot import types
import datetime
from cache_manager import cache
from utils.helpers import *

def handle_reply_message(call, bot):
    user_id = call.data.replace('reply_msg_', '')
    admin_id = call.from_user.id
    
    print(f"\n🔔 callback: الرد على رسالة")
    print(f"   المستخدم: {user_id}")
    print(f"   الأدمن: {admin_id}")
    
    delete_consultation_buttons(int(user_id), bot)
    
    if "message_consultations" not in cache.data:
        cache.data["message_consultations"] = {}
    
    cache.data["message_consultations"][user_id] = {
        "step": "waiting_reply",
        "admin_id": admin_id,
        "admin_name": get_admin_name(admin_id)
    }
    save_data()
    
    print(f"   ✅ تم تعيين الاستشارة بانتظار الرد من {admin_id}")
    
    bot.send_message(admin_id, f"✍️ **اكتب ردك للمستخدم {get_user_name(int(user_id))}:**\n(سيتم إرسال الرد فور كتابته)")
    bot.answer_callback_query(call.id, "يمكنك الآن كتابة الرد")

def handle_accept_chat(call, bot):
    user_id = int(call.data.replace('accept_chat_', ''))
    admin_id = call.from_user.id
    
    print(f"\n🔔 callback: قبول دردشة")
    print(f"   المستخدم: {user_id}")
    print(f"   الأدمن: {admin_id}")
    
    delete_live_chat_buttons(user_id, bot)
    
    if "waiting_list" in cache.data and user_id in cache.data["waiting_list"]:
        cache.data["waiting_list"].remove(user_id)
        print(f"   ✅ تم إزالة المستخدم من قائمة الانتظار")
    
    chat_id = f"{user_id}_{admin_id}"
    
    if "active_chats" not in cache.data:
        cache.data["active_chats"] = {}
    
    cache.data["active_chats"][chat_id] = {
        "user_id": user_id,
        "admin_id": admin_id,
        "start_time": datetime.datetime.now().isoformat()
    }
    save_data()
    
    print(f"   ✅ تم إنشاء محادثة جديدة: {chat_id}")
    
    admin_name = get_admin_name(admin_id)
    
    # إعداد واجهة المستخدم
    markup_user = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_end_user = types.KeyboardButton('⏹️ إنهاء الجلسة')
    markup_user.add(btn_end_user)
    
    try:
        bot.send_message(user_id,
                        f"✅ **تم قبول طلب الاستشارة!**\n\n"
                        f"الدكتور **{admin_name}** متاح الآن للدردشة.\n\n"
                        "يمكنك البدء في كتابة رسائلك.",
                        reply_markup=markup_user)
        print(f"   ✅ تم إعلام المستخدم")
    except Exception as e:
        print(f"   ❌ خطأ في إرسال رسالة للمستخدم: {e}")
    
    # إعداد واجهة الأدمن
    markup_admin = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_end_admin = types.KeyboardButton('⏹️ إنهاء الجلسة')
    markup_admin.add(btn_end_admin)
    
    try:
        bot.send_message(admin_id,
                        f"✅ **تم قبول المحادثة مع {get_user_name(user_id)}**\n\n"
                        "يمكنك الآن التحدث مع المستخدم.\n"
                        "استخدم زر 'إنهاء الجلسة' لإنهاء المحادثة.",
                        reply_markup=markup_admin)
        print(f"   ✅ تم إعلام الأدمن")
    except Exception as e:
        print(f"   ❌ خطأ في إرسال رسالة للأدمن: {e}")
    
    bot.answer_callback_query(call.id, "تم قبول المحادثة")