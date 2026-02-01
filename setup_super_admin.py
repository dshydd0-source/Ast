# setup_super_admin.py
import json
import os
from config import SUPER_ADMIN_ID

def setup_super_admin():
    """إعداد المشرف الرئيسي لأول مرة"""
    
    # إنشاء مجلد البيانات إذا لم يكن موجوداً
    os.makedirs('data', exist_ok=True)
    
    # تهيئة ملف الأدمنز
    admins_file = 'data/admins.json'
    
    if os.path.exists(admins_file):
        with open(admins_file, 'r', encoding='utf-8') as f:
            admins = json.load(f)
    else:
        admins = {
            "admins": {},
            "admin_names": {}
        }
    
    # إضافة المشرف الرئيسي إذا لم يكن موجوداً
    super_admin_id_str = str(SUPER_ADMIN_ID)
    
    if super_admin_id_str not in admins["admins"]:
        admins["admins"][super_admin_id_str] = {
            "name": "المشرف الرئيسي",
            "active": True,
            "added_by": "system",
            "added_date": "2024-01-01T00:00:00",
            "permissions": {
                "can_view_consultations": True,
                "can_reply_consultations": True,
                "can_accept_chats": True,
                "can_manage_admins": True
            }
        }
        admins["admin_names"]["المشرف الرئيسي"] = super_admin_id_str
        
        with open(admins_file, 'w', encoding='utf-8') as f:
            json.dump(admins, f, ensure_ascii=False, indent=2)
        
        print(f"✅ تم إضافة المشرف الرئيسي (ID: {SUPER_ADMIN_ID})")
    else:
        print(f"✅ المشرف الرئيسي موجود بالفعل (ID: {SUPER_ADMIN_ID})")

if __name__ == "__main__":
    setup_super_admin()