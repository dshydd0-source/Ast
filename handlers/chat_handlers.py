# handlers/chat_handlers.py
from cache_manager import cache
from utils.helpers import *
from handlers.admin_handlers import handle_admin_message

def handle_chat_messages(message, bot):
    user_id = message.from_user.id
    message_text = message.text
    
    print(f"\n📩 رسالة جديدة:")
    print(f"   من: {user_id}")
    print(f"   نص: {message_text[:50]}...")
    print(f"   هو أدمن: {is_admin(user_id)}")
    
    # تجاهل الأوامر والأزرار
    ignore_list = ['⏹️ إنهاء الجلسة', '🩺 طلب استشارة طبية', '📝 استشارة برسالة', 
                   '💬 دردشة حية مع دكتور', '🔙 رجوع', '❌ إلغاء الانتظار',
                   '📋 طلبات الاستشارات', '📋 قائمة الأدمنز', '➕ إضافة أدمن',
                   '🗑️ حذف أدمن', '🏠 القائمة الرئيسية']
    
    if message_text.startswith('/') or message_text in ignore_list:
        print(f"   ❌ تم تجاهل الرسالة (زر أو أمر)")
        return
    
    print(f"   ✅ معالجة الرسالة...")
    
    # التحقق من المحادثات النشطة
    if "active_chats" not in cache.data:
        cache.data["active_chats"] = {}
    
    active_chats = cache.data["active_chats"]
    print(f"   🔍 عدد المحادثات النشطة: {len(active_chats)}")
    
    # البحث عن المحادثة
    for chat_id, chat_data in active_chats.items():
        print(f"   🔍 فحص محادثة: {chat_id}")
        print(f"      مستخدم: {chat_data['user_id']}")
        print(f"      أدمن: {chat_data['admin_id']}")
        
        # إذا كان المستخدم هو الطرف الأول في المحادثة
        if chat_data["user_id"] == user_id:
            print(f"   ✅ وجدت! المستخدم في محادثة")
            admin_id = chat_data["admin_id"]
            user_name = get_user_name(user_id)
            
            try:
                # إرسال رسالة المستخدم إلى الأدمن
                bot.send_message(admin_id, f"👤 **{user_name}:**\n{message_text}")
                # تأكيد إرسال للمستخدم
                bot.send_message(user_id, f"✅ **تم إرسال رسالتك:**\n{message_text}")
                print(f"   ✅ تم إرسال رسالة من المستخدم {user_id} إلى الأدمن {admin_id}")
                return
            except Exception as e:
                print(f"   ❌ خطأ في إرسال رسالة من المستخدم: {e}")
                try:
                    bot.send_message(user_id, "❌ حدث خطأ في إرسال رسالتك، حاول مرة أخرى.")
                except:
                    pass
                return
        
        # إذا كان المستخدم هو الدكتور في المحادثة
        elif chat_data["admin_id"] == user_id:
            print(f"   ✅ وجدت! الأدمن في محادثة")
            user_id_to = chat_data["user_id"]
            admin_name = get_admin_name(user_id)
            
            try:
                # إرسال رسالة الأدمن إلى المستخدم
                bot.send_message(user_id_to, f"👨‍⚕️ **الدكتور {admin_name}:**\n{message_text}")
                # تأكيد إرسال للأدمن
                bot.send_message(user_id, f"✅ **تم إرسال ردك:**\n{message_text}")
                print(f"   ✅ تم إرسال رسالة من الأدمن {user_id} إلى المستخدم {user_id_to}")
                return
            except Exception as e:
                print(f"   ❌ خطأ في إرسال رسالة من الأدمن: {e}")
                try:
                    bot.send_message(user_id, "❌ حدث خطأ في إرسال رسالتك، حاول مرة أخرى.")
                except:
                    pass
                return
    
    print(f"   ❌ المستخدم ليس في محادثة نشطة")
    
    # إذا كان أدمن وليس في محادثة
    if is_admin(user_id):
        print(f"   🔍 البحث عن استشارات بانتظار الرد...")
        
        # البحث عن استشارة بانتظار رد من هذا الأدمن
        if "message_consultations" in cache.data:
            found_waiting = False
            for user_id_str, consultation_data in cache.data["message_consultations"].items():
                print(f"   🔍 فحص استشارة {user_id_str}: {consultation_data.get('step')}")
                if consultation_data.get("step") == "waiting_reply" and consultation_data.get("admin_id") == user_id:
                    print(f"   ✅ وجدت استشارة بانتظار الرد من {user_id}")
                    found_waiting = True
                    handle_admin_message(message, bot)
                    return
            
            if not found_waiting:
                print(f"   ❌ لا يوجد استشارات بانتظار الرد من هذا الأدمن")
        
        # إذا لم يكن في محادثة ولا يرد على استشارة
        print(f"   ❌ لا يوجد محادثات أو استشارات بانتظار الرد")
        try:
            bot.send_message(user_id, 
                           "📭 **ليس لديك محادثات نشطة حالياً.**\n\n"
                           "لبدء محادثة مع مستخدم:\n"
                           "1. انتظر ظهور طلب دردشة حية\n"
                           "2. اضغط على زر 'قبول محادثة'")
        except Exception as e:
            print(f"خطأ في إرسال رسالة للأدمن: {e}")
    else:
        # إذا كان مستخدم عادي وليس في محادثة
        print(f"   👤 مستخدم عادي ليس في محادثة")
        try:
            bot.send_message(user_id, 
                           "🔍 **أنت لست في محادثة نشطة حالياً.**\n\n"
                           "لبدء محادثة مع طبيب:\n"
                           "1. اختر '💬 دردشة حية مع دكتور'\n"
                           "2. انتظر حتى يقبل الطبيب المحادثة")
        except:
            pass

# دالة مساعدة للتحقق من المحادثات النشطة
def is_in_active_chat(user_id):
    """التحقق إذا كان المستخدم في محادثة نشطة"""
    if "active_chats" not in cache.data:
        return False, None
    
    for chat_id, chat_data in cache.data["active_chats"].items():
        if chat_data["user_id"] == user_id or chat_data["admin_id"] == user_id:
            return True, chat_data
    return False, None