import json
import os
import time
import threading
from pathlib import Path

from kivy.clock import Clock
from kivy.app import App
from kivymd.app import MDApp

def get_tasks_file():
    app = App.get_running_app()
    if app:
        return os.path.join(app.user_data_dir, "tasks.json")
    # Fallback для инициализации до запуска app
    return os.path.join(os.path.expanduser("~"), "tasks.json")

tasks = []

_initialized = False

def initialize():
    """Вызвать после инициализации приложения"""
    global _initialized
    if not _initialized:
        load_tasks()
        _initialized = True


def load_tasks():
    global tasks
    if os.path.exists(get_tasks_file()):
        try:
            with open(get_tasks_file(), "r", encoding="utf-8") as f:
                tasks = json.load(f)
        except Exception:
            tasks = []
    else:
        tasks = []

def save_tasks():
    with open(get_tasks_file(), "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=4)

def add_task(title, project, description, start_time, end_time, started=False, state='next'):
    task = {
        "title": title,
        "project": project,
        "description": description,
        "start_time": start_time,
        "end_time": end_time,
        "started": started,
        "state": state,
        "created": int(time.time())
    }
    tasks.append(task)
    save_tasks()
    return task

def delete_task(task_index):
    if 0 <= task_index < len(tasks):
        tasks.pop(task_index)
        save_tasks()

def edit_task(task_index, title=None, project=None, description=None, start_time=None, end_time=None, started=None, state=None, completed_time=None):
    if 0 <= task_index < len(tasks):
        task = tasks[task_index]
        if title is not None:
            task["title"] = title
        if project is not None:
            task["project"] = project
        if description is not None:
            task["description"] = description
        if start_time is not None:
            task["start_time"] = start_time
        if end_time is not None:
            task["end_time"] = end_time
        if completed_time is not None:
            task["completed_time"] = completed_time
        if started is not None:
            task["started"] = started
        if state is not None:
            task["state"] = state
        save_tasks()

def get_tasks():
    return tasks

RUN_LOOP_INTERVAL = 20

def _now():
    return int(time.time())

def _as_int(v):
    try:
        return int(v)
    except Exception:
        return None

def _format_duration(seconds):
    try:
        seconds = int(seconds)
    except Exception:
        return "0s"
    if seconds < 60:
        return f"{seconds}s"
    parts = []
    days = seconds // 86400
    if days:
        parts.append(f"{days}d")
        seconds -= days * 86400
    hours = seconds // 3600
    if hours:
        parts.append(f"{hours}h")
        seconds -= hours * 3600
    minutes = seconds // 60
    if minutes:
        parts.append(f"{minutes}m")
    return " ".join(parts)

try:
    from plyer import notification as _plyer_notification

    def _notify(title, message):
        try:
            _plyer_notification.notify(title=title, message=message)
        except Exception:
            print(f"[NOTIFY] {title} — {message}")
except Exception:
    def _notify(title, message):
        print(f"[NOTIFY] {title} — {message}")

def _send_task_notification(task, subject, body=None):
    title = f"Task: {task.get('title','(no title)')} — {subject}"
    message = body or ""
    _notify(title, message)

_running = False
_thread = None

def start_manager():
    global _running, _thread
    if _running:
        return
    _running = True
    _thread = threading.Thread(target=_manager_loop, daemon=True)
    _thread.start()

def stop_manager():
    global _running, _thread
    _running = False
    if _thread:
        _thread.join(timeout=1)
        _thread = None

def _manager_loop():
    while _running:
        try:
            _check_all_tasks()
        except Exception as e:
            print("manager loop error:", e)
        time.sleep(RUN_LOOP_INTERVAL)

def _check_all_tasks():
    now = _now()
    active_exists = any(t.get("state") == "active" for t in tasks)

    for idx, task in enumerate(tasks):
        start_time = _as_int(task.get("start_time"))
        end_time = _as_int(task.get("end_time"))
        state = task.get("state")
        reminders = task.setdefault("reminders_sent", {})
        missed = task.setdefault("missed_notifications", {})

        if state == "next" and start_time is not None:
            if active_exists:
                continue

            t15 = start_time - 15 * 60
            t10 = start_time - 10 * 60
            t5 = start_time - 5 * 60

            if now >= start_time:
                task["state"] = "active"
                task["started"] = True
                task["started_time"] = now

                save_tasks()
                try:
                    app = MDApp.get_running_app()
                    if app and hasattr(app, 'refresh_tasks'):
                        Clock.schedule_once(lambda dt: app.refresh_tasks(), 0)
                except Exception as e:
                    print(f"Error scheduling refresh: {e}")
                active_exists = True
            else:
                if now >= t15 and not reminders.get("r15"):
                    reminders["r15"] = now
                    save_tasks()
                    _send_task_notification(task, "Напоминание: 15 минут до старта", f"Старт через {_format_duration(start_time - now)}.")
                if now >= t10 and not reminders.get("r10"):
                    reminders["r10"] = now
                    save_tasks()
                    _send_task_notification(task, "Напоминание: 10 минут до старта", f"Старт через {_format_duration(start_time - now)}.")
                if now >= t5 and not reminders.get("r5"):
                    reminders["r5"] = now
                    save_tasks()
                    _send_task_notification(task, "Напоминание: 5 минут до старта", f"Старт через {_format_duration(start_time - now)}.")

        if end_time is not None and state not in ("completed", "completed_overdue"):
            if now >= end_time:
                if not missed.get("missed"):
                    missed["missed"] = now
                    missed["missed_time"] = now
                    save_tasks()
                    _send_task_notification(task, "Дедлайн прошёл", "Вы не успели выполнить задачу до дедлайна.")
                for mins, key, subj in ((5, "o5", "Просрочено: +5 минут"), (10, "o10", "Просрочено: +10 минут"), (15, "o15", "Просрочено: +15 минут")):
                    t_check = end_time + mins * 60
                    if now >= t_check and not missed.get(key):
                        missed[key] = now
                        save_tasks()
                        overdue = now - end_time
                        _send_task_notification(task, subj, f"Задача просрочена на {_format_duration(overdue)}.")
                after_hourly_base = end_time + 15 * 60
                if now >= after_hourly_base:
                    hours_overdue = int((now - after_hourly_base) // 3600) + 1
                    last_hour = int(missed.get("last_hour_sent", 0))
                    while last_hour < hours_overdue:
                        last_hour += 1
                        missed["last_hour_sent"] = last_hour
                        save_tasks()
                        overdue_total = now - end_time
                        _send_task_notification(task, f"Просрочено: {last_hour} час(ов) после первых 15 минут", f"Задача просрочена уже на {_format_duration(overdue_total)}.")
        state = task.get("state")
        if state == "completed":
            pass
        elif state == "completed_overdue":
            pass
        elif state == "active":
            pass
        elif state == "next":
            pass

