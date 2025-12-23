import json
import os
import time

from pathlib import Path
TASKS_FILE = Path.home() / "tasks.json"

tasks = []

def load_tasks():
    global tasks
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE, "r", encoding="utf-8") as f:
                tasks = json.load(f)
        except Exception:
            tasks = []
    else:
        tasks = []

def save_tasks():
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=4)

def add_task(title, project, description, start_time, end_time, started=False):
    task = {
        "title": title,
        "project": project,
        "description": description,
        "start_time": start_time,
        "end_time": end_time,
        "started": started,
        "created": int(time.time())
    }
    tasks.append(task)
    save_tasks()
    return task

def delete_task(task_index):
    if 0 <= task_index < len(tasks):
        tasks.pop(task_index)
        save_tasks()

def edit_task(task_index, title=None, project=None, description=None, start_time=None, end_time=None, started=None):
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
        if started is not None:
            task["started"] = started
        save_tasks()

def get_tasks():
    return tasks

load_tasks()