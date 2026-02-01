# cache_manager.py
import json
import os
import time
from threading import Lock
from config import DATA_FILE, ADMINS_FILE, MESSAGE_IDS_FILE, AUTO_SAVE_INTERVAL

class CacheManager:
    def __init__(self):
        self.data = {}
        self.admins = {}
        self.message_ids = {}
        self.locks = {
            'data': Lock(),
            'admins': Lock(),
            'message_ids': Lock()
        }
        self.last_save = time.time()
        self.load_all()
    
    def load_all(self):
        """تحميل جميع البيانات إلى الكاش"""
        self._load_file('data', DATA_FILE)
        self._load_file('admins', ADMINS_FILE)
        self._load_file('message_ids', MESSAGE_IDS_FILE)
    
    def _load_file(self, key, filename):
        """تحميل ملف واحد"""
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    setattr(self, key, json.load(f))
            except Exception as e:
                print(f"خطأ في تحميل ملف {filename}: {e}")
                self._init_default_data(key)
        else:
            self._init_default_data(key)
    
    def _init_default_data(self, key):
        """تهيئة البيانات الافتراضية"""
        if key == 'data':
            self.data = {
                "waiting_list": [],
                "active_chats": {},
                "message_consultations": {},
                "user_names": {},
                "admin_messages": {},
                "pending_requests": {}
            }
        elif key == 'admins':
            self.admins = {
                "admins": {},
                "admin_names": {}
            }
        elif key == 'message_ids':
            self.message_ids = {
                "consultation_msgs": {},
                "live_chat_msgs": {}
            }
    
    def save_all(self, force=False):
        """حفظ جميع البيانات من الكاش"""
        current_time = time.time()
        if force or (current_time - self.last_save) >= AUTO_SAVE_INTERVAL:
            self._save_file('data', DATA_FILE)
            self._save_file('admins', ADMINS_FILE)
            self._save_file('message_ids', MESSAGE_IDS_FILE)
            self.last_save = current_time
            return True
        return False
    
    def _save_file(self, key, filename):
        """حفظ ملف واحد"""
        with self.locks[key]:
            try:
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(getattr(self, key), f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"خطأ في حفظ ملف {filename}: {e}")
    
    # Methods for safe data access
    def get_data(self, key, default=None):
        with self.locks['data']:
            return self.data.get(key, default)
    
    def set_data(self, key, value):
        with self.locks['data']:
            self.data[key] = value
    
    def get_admins(self, key, default=None):
        with self.locks['admins']:
            return self.admins.get(key, default)
    
    def set_admins(self, key, value):
        with self.locks['admins']:
            self.admins[key] = value

# إنشاء كائن كاش عالمي
cache = CacheManager()