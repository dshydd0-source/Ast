# handlers/user_handlers.py
from telebot import types
import datetime
from cache_manager import cache
from utils.helpers import *

def send_welcome(message, bot):
    user_id = message.from_user.id
    
    # أضف هذه السطور للتصحيح
    from utils.helpers import debug_super_admin, is_super_admin
    debug_super_admin()
    
    print(f"\n🔍 التحقق من صلاحيات {user_id}:")
    print(f"   هو super admin: {is_super_admin(user_id)}")
    print(f"   SUPER_ADMIN_ID: {SUPER_ADMIN_ID}")
    print(f"   user_id: {user_id}")
    
    # باقي الكود...
    
    if is_admin(user_id):
        admin_name = get_admin_name(user_id)
        welcome_msg = f"مرحباً دكتور {admin_name}!\n\n"
        welcome_msg += "يمكنك الآن تلقي طلبات الاستشارات والرد عليها."
        
        # إذا كان مشرف رئيسي، أضف أزرار إدارة الأدمنز
        if is_super_admin(user_id):
            markup = create_admin_menu()
            welcome_msg += "\n\n⚙️ **أنت المشرف الرئيسي، يمكنك إدارة الأدمنز:**"
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn1 = types.KeyboardButton('📋 طلبات الاستشارات')
            markup.add(btn1)
        
        bot.send_message(message.chat.id, welcome_msg, reply_markup=markup)
        
        # إذا لم يكن مسجلاً بالاسم
        admin_id_str = str(user_id)
        if admin_id_str not in cache.admins["admins"] or not cache.admins["admins"][admin_id_str]["name"]:
            bot.send_message(user_id, "مرحباً دكتور! يرجى تسجيل اسمك أولاً:")
    else:
        markup = create_main_menu()
        bot.send_message(message.chat.id, 
                        "مرحباً بك في بوت الاستشارات الطبية!\n\n"
                        "يمكنك طلب استشارة طبية من خلال الزر أدناه.",
                        reply_markup=markup)

def request_consultation(message, bot):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('📝 استشارة برسالة')
    btn2 = types.KeyboardButton('💬 دردشة حية مع دكتور')
    btn3 = types.KeyboardButton('🔙 رجوع')
    markup.add(btn1, btn2, btn3)
    
    bot.send_message(message.chat.id, "اختر نوع الاستشارة:", reply_markup=markup)

def message_consultation(message, bot):
    user_id_str = str(message.from_user.id)
    
    if "message_consultations" not in cache.data:
        cache.data["message_consultations"] = {}
    
    cache.data["message_consultations"][user_id_str] = {
        "step": "ask_name",
        "message": ""
    }
    save_data()
    
    bot.send_message(message.chat.id, 
                    "لبدء الاستشارة، يرجى كتابة اسمك أولاً:",
                    reply_markup=types.ReplyKeyboardRemove())

def live_chat_request(message, bot):
    user_id = message.from_user.id
    user_name = get_user_name(user_id)
    
    if "waiting_list" not in cache.data:
        cache.data["waiting_list"] = []
    
    if user_id not in cache.data["waiting_list"]:
        cache.data["waiting_list"].append(user_id)
    
    if "live_chat_msgs" not in cache.message_ids:
        cache.message_ids["live_chat_msgs"] = {}
    
    cache.message_ids["live_chat_msgs"][str(user_id)] = {}
    
    for admin_id in cache.admins["admins"]:
        try:
            markup = types.InlineKeyboardMarkup()
            callback_data = f"accept_chat_{user_id}"
            btn = types.InlineKeyboardButton(f"قبول محادثة مع {user_name}", callback_data=callback_data)
            markup.add(btn)
            
            sent_msg = bot.send_message(int(admin_id),
                           f"📞 طلب دردشة حية جديد:\n"
                           f"المستخدم: {user_name}\n"
                           f"ID: {user_id}\n"
                           f"الوقت: {get_current_time()}",
                           reply_markup=markup)
            
            cache.message_ids["live_chat_msgs"][str(user_id)][admin_id] = sent_msg.message_id
            
        except Exception as e:
            print(f"خطأ في إرسال رسالة للأدمن {admin_id}: {e}")
    
    save_data()
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = types.KeyboardButton('❌ إلغاء الانتظار')
    markup.add(btn)
    
    bot.send_message(message.chat.id,
                    "🔍 جاري البحث عن دكتور متاح...\n"
                    "يرجى الانتظار، سنقوم بتوصيلك بأقبل دكتور متاح.",
                    reply_markup=markup)

def cancel_waiting(message, bot):
    user_id = message.from_user.id
    
    if "waiting_list" in cache.data and user_id in cache.data["waiting_list"]:
        cache.data["waiting_list"].remove(user_id)
        save_data()
        delete_live_chat_buttons(user_id, bot)
    
    markup = create_main_menu()
    bot.send_message(message.chat.id, "تم إلغاء طلب الانتظار.", reply_markup=markup)

def go_back(message, bot):
    markup = create_main_menu()
    bot.send_message(message.chat.id, "تم الرجوع للقائمة الرئيسية.", reply_markup=markup)

def handle_message_consultation(message, bot):
    user_id_str = str(message.from_user.id)
    
    if "message_consultations" not in cache.data or user_id_str not in cache.data["message_consultations"]:
        return
    
    consultation_data = cache.data["message_consultations"][user_id_str]
    
    if consultation_data["step"] == "ask_name":
        if "user_names" not in cache.data:
            cache.data["user_names"] = {}
        
        cache.data["user_names"][user_id_str] = message.text
        consultation_data["step"] = "ask_message"
        save_data()
        
        bot.send_message(int(user_id_str), f"شكراً {message.text}، يرجى الآن كتابة رسالتك الطبية:")
    
    elif consultation_data["step"] == "ask_message":
        consultation_data["message"] = message.text
        consultation_data["step"] = "completed"
        consultation_data["timestamp"] = datetime.datetime.now().isoformat()
        consultation_data["user_name"] = cache.data["user_names"][user_id_str]
        save_data()
        
        if "consultation_msgs" not in cache.message_ids:
            cache.message_ids["consultation_msgs"] = {}
        
        cache.message_ids["consultation_msgs"][user_id_str] = {}
        
        for admin_id in cache.admins["admins"]:
            try:
                markup = types.InlineKeyboardMarkup()
                callback_data = f"reply_msg_{user_id_str}"
                btn = types.InlineKeyboardButton(f"الرد على {cache.data['user_names'][user_id_str]}", callback_data=callback_data)
                markup.add(btn)
                
                sent_msg = bot.send_message(int(admin_id),
                               f"📩 استشارة جديدة:\n"
                               f"من: {cache.data['user_names'][user_id_str]}\n"
                               f"الوقت: {get_current_time()}\n\n"
                               f"الرسالة:\n{message.text}",
                               reply_markup=markup)
                
                cache.message_ids["consultation_msgs"][user_id_str][admin_id] = sent_msg.message_id
                
            except Exception as e:
                print(f"خطأ في إرسال رسالة للأدمن {admin_id}: {e}")
        
        save_data()
        
        markup = create_main_menu()
        bot.send_message(int(user_id_str),
                        "✅ تم إرسال استشارتك بنجاح!\n"
                        "سوف تتلقى رداً من أحد الأطباء قريباً.",
                        reply_markup=markup)
