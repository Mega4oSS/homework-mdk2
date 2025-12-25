import json
import os
from kivymd.app import MDApp

def get_settings_file():
    app = MDApp.get_running_app()
    if app:
        return os.path.join(app.user_data_dir, "settings.json")
    return os.path.join(os.path.expanduser("~"), "settings.json")

def load_settings():
    if os.path.exists(get_settings_file()):
        try:
            with open(get_settings_file(), "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"notifications_enabled": True}
    return {"notifications_enabled": True}

def save_settings(settings):
    with open(get_settings_file(), "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)

def is_notifications_enabled():
    return load_settings().get("notifications_enabled", True)