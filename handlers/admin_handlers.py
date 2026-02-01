# handlers/admin_handlers.py
from telebot import types
from cache_manager import cache
from utils.helpers import *

def handle_admin_message(message, bot):
    admin_id = str(message.from_user.id)
    
    print(f"\n🔍 معالجة رسالة أدمن: {admin_id}")
    print(f"   النص: {message.text[:50]}...")
    
    # معالجة قائمة طلبات الاستشارات للأدمنز العاديين
    if message.text == '📋 طلبات الاستشارات':
        print(f"   📊 عرض لوحة تحكم الطبيب")
        bot.send_message(message.chat.id, 
                        "📊 **لوحة تحكم الطبيب**\n\n"
                        "• ستتلقى إشعارات بالاستشارات الجديدة تلقائياً\n"
                        "• يمكنك الرد على الرسائل عبر أزرار الرد\n"
                        "• يمكنك قبول الدردشات الحية عبر أزرار القبول",
                        parse_mode='Markdown')
        return
    
    # أولا: التحقق إذا كان الأدمن في محادثة حية
    if "active_chats" in cache.data and cache.data["active_chats"]:
        for chat_id, chat_data in cache.data["active_chats"].items():
            if chat_data["admin_id"] == int(admin_id):
                print(f"   ✅ الأدمن في محادثة حية: {chat_id}")
                user_id_to = chat_data["user_id"]
                admin_name = get_admin_name(int(admin_id))
                
                # هذه الرسالة ستتم معالجتها في handle_chat_messages
                print(f"   🔄 سيتم معالجة الرسالة في handle_chat_messages")
                return  # سنعود لمعالجة الرسالة كرسالة دردشة
    
    # ثانيا: البحث عن رسالة بانتظار رد من هذا الأدمن
    if "message_consultations" in cache.data and cache.data["message_consultations"]:
        found_consultation = False
        for user_id, consultation_data in cache.data["message_consultations"].items():
            print(f"   🔍 فحص استشارة {user_id}: {consultation_data.get('step')}")
            if consultation_data.get("step") == "waiting_reply" and consultation_data.get("admin_id") == int(admin_id):
                found_consultation = True
                user_name = consultation_data.get("user_name", get_user_name(int(user_id)))
                admin_name = get_admin_name(int(admin_id))
                
                print(f"   ✅ وجدت استشارة بانتظار الرد من {admin_id}")
                
                try:
                    # إرسال الرد للمستخدم
                    bot.send_message(int(user_id), f"📬 **لديك رد من الدكتور {admin_name}:**\n\n{message.text}")
                    print(f"   ✅ تم إرسال الرد إلى المستخدم {user_id}")
                except Exception as e:
                    print(f"   ❌ خطأ في إرسال الرد للمستخدم: {e}")
                    bot.send_message(message.chat.id, f"❌ حدث خطأ في إرسال الرد: {e}")
                    return
                
                # إعلام الأدمنز الآخرين
                for other_admin_id in cache.admins["admins"]:
                    if other_admin_id != admin_id:
                        try:
                            bot.send_message(int(other_admin_id),
                                           f"📌 **تم الرد على رسالة:**\n"
                                           f"المستخدم: {user_name}\n"
                                           f"بواسطة: الدكتور {admin_name}\n\n"
                                           f"**الرد:**\n{message.text}")
                        except:
                            pass
                
                # حذف الاستشارة بعد الرد
                if user_id in cache.data["message_consultations"]:
                    del cache.data["message_consultations"][user_id]
                save_data()
                
                print(f"   ✅ تم حذف الاستشارة بعد الرد")
                bot.send_message(message.chat.id, "✅ **تم إرسال ردك بنجاح!**")
                return
        
        if not found_consultation:
            print(f"   ❌ لا توجد استشارات بانتظار الرد من هذا الأدمن")
    
    # ثالثا: إذا وصلنا هنا، فهذا يعني أن الأدمن:
    # 1. ليس في محادثة حية
    # 2. ليس لديه استشارات بانتظار الرد
    # 3. ربما حاول كتابة رسالة عادية
    
    print(f"   ⚠️ رسالة الأدمن لم يتم معالجتها")
    print(f"   📊 تحليل الوضع:")
    print(f"      - في محادثة حية: {'نعم' if is_in_active_chat(int(admin_id))[0] else 'لا'}")
    print(f"      - استشارات بانتظار: {count_waiting_consultations(int(admin_id))}")
    
    # إرسال رسالة توضيحية
    bot.send_message(message.chat.id, 
                    "💡 **ملاحظة:**\n"
                    "أنت لست في محادثة حية حالياً.\n"
                    "لتلقي رسائل من المستخدمين، يجب أن تكون:\n"
                    "1. في محادثة حية (يتم قبولها عبر زر 'قبول محادثة')\n"
                    "2. أو لديك استشارة برسالة بانتظار الرد")

def register_admin(message, bot):
    admin_id = str(message.from_user.id)
    
    if admin_id not in cache.admins["admins"]:
        cache.admins["admins"][admin_id] = {"name": "", "active": True}
    
    if not cache.admins["admins"][admin_id]["name"]:
        cache.admins["admins"][admin_id]["name"] = message.text
        cache.admins["admin_names"][message.text] = admin_id
        save_data()
        
        print(f"✅ تسجيل أدمن جديد: {message.text} (ID: {admin_id})")
        bot.send_message(int(admin_id), f"✅ **تم تسجيل اسمك بنجاح دكتور {message.text}!**")

def end_session(message, bot):
    user_id = message.from_user.id
    
    print(f"\n⏹️ محاولة إنهاء جلسة للمستخدم: {user_id}")
    
    if "active_chats" not in cache.data:
        print(f"   ❌ لا توجد محادثات نشطة")
        return
    
    chat_to_end = None
    chat_data_to_end = None
    
    for chat_id, chat_data in cache.data["active_chats"].items():
        if chat_data["user_id"] == user_id or chat_data["admin_id"] == user_id:
            chat_to_end = chat_id
            chat_data_to_end = chat_data
            break
    
    if chat_to_end:
        user_id_in_chat = chat_data_to_end["user_id"]
        admin_id_in_chat = chat_data_to_end["admin_id"]
        
        print(f"   ✅ وجدت محادثة للإنهاء: {chat_to_end}")
        
        # المستخدم أنهى الجلسة
        if user_id == user_id_in_chat:
            user_name = get_user_name(user_id_in_chat)
            admin_name = get_admin_name(admin_id_in_chat)
            
            print(f"   👤 المستخدم أنهى الجلسة")
            
            # إعلام الأدمن
            try:
                bot.send_message(admin_id_in_chat, f"📞 **قام المستخدم {user_name} بإنهاء الجلسة.**")
            except Exception as e:
                print(f"   ❌ خطأ في إعلام الأدمن: {e}")
            
            # إعادة تعيين واجهة الأدمن
            try:
                bot.send_message(admin_id_in_chat, "تم إنهاء الجلسة.", reply_markup=types.ReplyKeyboardRemove())
            except:
                pass
            
            # إعادة تعيين واجهة المستخدم للقائمة الرئيسية
            markup = create_main_menu()
            try:
                bot.send_message(user_id_in_chat, "شكراً لاستخدامك خدمتنا الطبية.", reply_markup=markup)
            except:
                pass
        
        # الأدمن أنهى الجلسة
        else:
            admin_name = get_admin_name(user_id)
            user_name = get_user_name(user_id_in_chat)
            
            print(f"   👨‍⚕️ الأدمن أنهى الجلسة")
            
            # إعلام المستخدم
            try:
                bot.send_message(user_id_in_chat,
                               f"📞 **قام الدكتور {admin_name} بإنهاء الجلسة.**\n"
                               "شكراً لاستخدامك خدمتنا الطبية.")
            except Exception as e:
                print(f"   ❌ خطأ في إعلام المستخدم: {e}")
            
            # إعادة تعيين واجهة المستخدم للقائمة الرئيسية
            markup = create_main_menu()
            try:
                bot.send_message(user_id_in_chat, "القائمة الرئيسية:", reply_markup=markup)
            except:
                pass
            
            # إعادة تعيين واجهة الأدمن
            try:
                bot.send_message(user_id, "تم إنهاء الجلسة.", reply_markup=types.ReplyKeyboardRemove())
            except:
                pass
        
        # حذف المحادثة النشطة
        del cache.data["active_chats"][chat_to_end]
        save_data()
        print(f"   ✅ تم حذف المحادثة: {chat_to_end}")
    else:
        print(f"   ❌ لم يتم العثور على محادثة للمستخدم")

# دوال مساعدة جديدة
def is_in_active_chat(user_id):
    """التحقق إذا كان المستخدم في محادثة نشطة"""
    if "active_chats" not in cache.data:
        return False, None
    
    for chat_id, chat_data in cache.data["active_chats"].items():
        if chat_data["user_id"] == user_id or chat_data["admin_id"] == user_id:
            return True, chat_data
    return False, None

def count_waiting_consultations(admin_id):
    """عد استشارات بانتظار الرد من أدمن معين"""
    count = 0
    if "message_consultations" in cache.data:
        for consultation_data in cache.data["message_consultations"].values():
            if consultation_data.get("step") == "waiting_reply" and consultation_data.get("admin_id") == admin_id:
                count += 1
    return count