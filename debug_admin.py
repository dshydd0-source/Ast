# debug_admin.py
import os
import json

def debug_all():
    """تصحيح كامل للنظام"""
    
    print("\n" + "="*60)
    print("🔧 DEBUG MODE - تصحيح كامل")
    print("="*60)
    
    # 1. Environment Variables
    print("\n📋 1. متغيرات البيئة:")
    bot_token = os.environ.get('BOT_TOKEN')
    super_admin = os.environ.get('SUPER_ADMIN_ID')
    
    print(f"   BOT_TOKEN موجود: {'نعم' if bot_token else 'لا'}")
    print(f"   SUPER_ADMIN_ID: '{super_admin}'")
    print(f"   نوع SUPER_ADMIN_ID: {type(super_admin)}")
    
    # 2. ملف admins.json
    print("\n📋 2. ملف admins.json:")
    admins_file = 'data/admins.json'
    
    if os.path.exists(admins_file):
        try:
            with open(admins_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"   ✅ الملف موجود")
            print(f"   📁 محتوى الملف:")
            print(f"      IDs: {list(data.get('admins', {}).keys())}")
            
            if data.get('admins'):
                for admin_id, info in data['admins'].items():
                    print(f"      - {admin_id}: {info.get('name')}")
        except Exception as e:
            print(f"   ❌ خطأ في قراءة الملف: {e}")
    else:
        print("   ❌ الملف غير موجود!")
    
    # 3. config.py
    print("\n📋 3. إعدادات config.py:")
    try:
        # محاولة استيراد config
        import sys
        sys.path.append('.')
        from config import SUPER_ADMIN_ID as config_id
        
        print(f"   SUPER_ADMIN_ID في config: {config_id}")
        print(f"   النوع في config: {type(config_id)}")
        
        # مقارنة
        if str(config_id) == str(super_admin):
            print("   ✅ config و Environment متطابقين")
        else:
            print(f"   ❌ مختلفين! config: {config_id}, env: {super_admin}")
            
    except Exception as e:
        print(f"   ❌ خطأ في استيراد config: {e}")
    
    # 4. رسالة للمستخدم
    print("\n📋 4. التعليمات:")
    print(f"   • تأكد أن ID حسابك في تليجرام هو: {super_admin}")
    print(f"   • افتح @userinfobot في تليجرام لتحصل على IDك")
    print(f"   • إذا الـ ID مختلف، عدل SUPER_ADMIN_ID في Render")
    
    print("\n" + "="*60)
    print("✅ انتهى التصحيح")
    print("="*60)
    
    return super_admin

if __name__ == "__main__":
    debug_all()
