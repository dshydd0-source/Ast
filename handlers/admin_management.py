# handlers/admin_management.py
from telebot import types
from cache_manager import cache
from utils.helpers import *
from config import SUPER_ADMIN_ID
import handlers.user_handlers as user_handlers
import datetime

# حالات إضافة وحذف الأدمنز
admin_states = {}

def handle_admin_management(message, bot):
    """معالجة أوامر إدارة الأدمنز"""
    user_id = message.from_user.id
    
    if not is_super_admin(user_id):
        bot.send_message(user_id, "⛔ ليس لديك صلاحية لإدارة الأدمنز.")
        return
    
    if message.text == '📋 قائمة الأدمنز':
        show_admins_list(message, bot)
    
    elif message.text == '➕ إضافة أدمن':
        start_add_admin(message, bot)
    
    elif message.text == '🗑️ حذف أدمن':
        start_remove_admin(message, bot)
    
    elif message.text == '🏠 القائمة الرئيسية':
        user_handlers.send_welcome(message, bot)

def show_admins_list(message, bot):
    """عرض قائمة الأدمنز"""
    user_id = message.from_user.id
    
    if not is_super_admin(user_id):
        return
    
    admins = get_all_admins()
    
    if not admins:
        bot.send_message(user_id, "📭 لا يوجد أدمنز مسجلين حالياً.")
        return
    
    response = "📋 **قائمة الأدمنز:**\n\n"
    
    for idx, (admin_id, admin_data) in enumerate(admins.items(), 1):
        status = "✅ نشط" if admin_data.get("active", True) else "❌ غير نشط"
        added_by = admin_data.get("added_by", "غير معروف")
        added_date = admin_data.get("added_date", "غير معروف")
        
        try:
            added_date = datetime.datetime.fromisoformat(added_date).strftime("%Y-%m-%d %H:%M")
        except:
            pass
        
        response += f"{idx}. **{admin_data['name']}**\n"
        response += f"   ├ ID: `{admin_id}`\n"
        response += f"   ├ الحالة: {status}\n"
        response += f"   ├ أضيف بواسطة: {added_by}\n"
        response += f"   └ تاريخ الإضافة: {added_date}\n\n"
    
    response += f"**المجموع: {len(admins)} أدمن**"
    
    bot.send_message(user_id, response, parse_mode='Markdown')
    
    # عرض القائمة مع الأزرار
    markup = create_admin_menu()
    bot.send_message(user_id, "اختر الإجراء:", reply_markup=markup)

def start_add_admin(message, bot):
    """بدء عملية إضافة أدمن جديد"""
    user_id = message.from_user.id
    
    if not is_super_admin(user_id):
        return
    
    admin_states[user_id] = {
        "action": "add_admin",
        "step": "ask_id"
    }
    
    bot.send_message(user_id, 
                    "📝 **إضافة أدمن جديد:**\n\n"
                    "يرجى إرسال ID الأدمن المراد إضافته.\n"
                    "يمكنك الحصول على ID المستخدم باستخدام @userinfobot",
                    reply_markup=types.ReplyKeyboardRemove())

def start_remove_admin(message, bot):
    """بدء عملية حذف أدمن"""
    user_id = message.from_user.id
    
    if not is_super_admin(user_id):
        return
    
    admins = get_all_admins()
    
    if not admins:
        bot.send_message(user_id, "📭 لا يوجد أدمنز لحذفهم.")
        return
    
    # إنشاء أزرار لكل أدمن
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    for admin_id, admin_data in admins.items():
        if admin_id != str(user_id):  # لا يمكن حذف نفسه
            callback_data = f"remove_admin_{admin_id}"
            btn = types.InlineKeyboardButton(
                f"🗑️ {admin_data['name']}",
                callback_data=callback_data
            )
            markup.add(btn)
    
    btn_cancel = types.InlineKeyboardButton("❌ إلغاء", callback_data="cancel_remove")
    markup.add(btn_cancel)
    
    bot.send_message(user_id, "👥 **اختر الأدمن المراد حذفه:**", reply_markup=markup)

def handle_add_admin_step(message, bot):
    """معالجة خطوات إضافة الأدمن"""
    user_id = message.from_user.id
    
    if user_id not in admin_states:
        return
    
    state = admin_states[user_id]
    
    if state["action"] == "add_admin":
        if state["step"] == "ask_id":
            try:
                new_admin_id = int(message.text)
                
                # التحقق من أن ID صحيح
                if new_admin_id == user_id:
                    bot.send_message(user_id, "⚠️ لا يمكنك إضافة نفسك!")
                    del admin_states[user_id]
                    markup = create_admin_menu()
                    bot.send_message(user_id, "اختر الإجراء:", reply_markup=markup)
                    return
                
                # التحقق إذا كان الأدمن موجوداً بالفعل
                if str(new_admin_id) in cache.admins["admins"]:
                    bot.send_message(user_id, "⚠️ هذا الأدمن مضاف مسبقاً!")
                    del admin_states[user_id]
                    markup = create_admin_menu()
                    bot.send_message(user_id, "اختر الإجراء:", reply_markup=markup)
                    return
                
                # حفظ ID والمتابعة للخطوة التالية
                state["step"] = "ask_name"
                state["admin_id"] = new_admin_id
                admin_states[user_id] = state
                
                bot.send_message(user_id, "✅ تم حفظ ID.\nالآن أرسل اسم الأدمن:")
                
            except ValueError:
                bot.send_message(user_id, "❌ ID غير صحيح! يرجى إرسال أرقام فقط.")
        
        elif state["step"] == "ask_name":
            admin_name = message.text.strip()
            new_admin_id = state["admin_id"]
            
            # إضافة الأدمن
            success = add_admin(new_admin_id, admin_name, f"admin_{user_id}")
            
            if success:
                # إرسال رسالة ترحيب للأدمن الجديد
                try:
                    welcome_msg = f"🎉 **مرحباً دكتور {admin_name}!**\n\n"
                    welcome_msg += "✅ تمت إضافتك كطبيب في بوت الاستشارات الطبية.\n"
                    welcome_msg += "يمكنك الآن:\n"
                    welcome_msg += "• تلقي طلبات الاستشارات\n"
                    welcome_msg += "• الرد على الرسائل\n"
                    welcome_msg += "• قبول الدردشات الحية\n\n"
                    welcome_msg += "استخدم الأمر /start لبدء العمل."
                    
                    bot.send_message(new_admin_id, welcome_msg, parse_mode='Markdown')
                except Exception as e:
                    print(f"خطأ في إرسال رسالة للأدمن الجديد: {e}")
                
                # إعلام المشرف الرئيسي
                bot.send_message(user_id, 
                               f"✅ **تمت إضافة الأدمن بنجاح!**\n\n"
                               f"**الاسم:** {admin_name}\n"
                               f"**ID:** `{new_admin_id}`",
                               parse_mode='Markdown')
            else:
                bot.send_message(user_id, "❌ حدث خطأ في إضافة الأدمن!")
            
            # تنظيف الحالة
            del admin_states[user_id]
            
            # العودة لقائمة الأدمنز
            markup = create_admin_menu()
            bot.send_message(user_id, "اختر الإجراء:", reply_markup=markup)

def handle_remove_admin_callback(call, bot):
    """معالجة حذف الأدمن عبر Callback"""
    user_id = call.from_user.id
    
    if not is_super_admin(user_id):
        bot.answer_callback_query(call.id, "⛔ ليس لديك صلاحية!")
        return
    
    if call.data == "cancel_remove":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        markup = create_admin_menu()
        bot.send_message(user_id, "تم الإلغاء.", reply_markup=markup)
        return
    
    if call.data.startswith("remove_admin_"):
        admin_id_to_remove = call.data.replace("remove_admin_", "")
        
        # الحصول على معلومات الأدمن قبل الحذف
        admin_info = get_admin_info(admin_id_to_remove)
        
        if not admin_info:
            bot.answer_callback_query(call.id, "❌ الأدمن غير موجود!")
            return
        
        # التحقق من عدم حذف نفسه
        if admin_id_to_remove == str(user_id):
            bot.answer_callback_query(call.id, "⚠️ لا يمكنك حذف نفسك!")
            return
        
        # حذف الأدمن
        success = remove_admin(admin_id_to_remove, f"admin_{user_id}")
        
        if success:
            bot.answer_callback_query(call.id, f"✅ تم حذف {admin_info['name']}")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            
            # إعلام الأدمن المحذوف
            try:
                bot.send_message(int(admin_id_to_remove),
                               "❌ **تم إزالتك من قائمة الأطباء**\n\n"
                               "لم تعد لديك صلاحيات الوصول إلى البوت.",
                               parse_mode='Markdown')
            except:
                pass
            
            bot.send_message(user_id, f"✅ تم حذف الدكتور {admin_info['name']} بنجاح.")
        else:
            bot.answer_callback_query(call.id, "❌ حدث خطأ في الحذف!")
        
        # عرض القائمة المحدثة
        markup = create_admin_menu()
        bot.send_message(user_id, "اختر الإجراء:", reply_markup=markup)

def handle_admin_states(message, bot):
    """معالجة حالات إدارة الأدمنز"""
    user_id = message.from_user.id
    
    if user_id in admin_states:
        handle_add_admin_step(message, bot)
        return True
    return False