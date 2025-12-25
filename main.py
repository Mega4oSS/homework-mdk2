import datetime
import json
import os
import sys
import time
import traceback

from kivy import Config
from kivy.app import App
from kivy.core.text import LabelBase
from kivy.properties import BooleanProperty, NumericProperty, OptionProperty, StringProperty, ListProperty
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Rectangle, Line
from kivy.graphics.texture import Texture
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.animation import Animation
from datetime import datetime
from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.pickers import MDTimePicker, MDDatePicker
import logging

from kivymd.uix.selectioncontrol import MDSwitch
from kivymd.uix.textfield import MDTextField

logging.basicConfig(level=logging.DEBUG)

import taskManager

LabelBase.register(
    name='Emojis',
    fn_regular='fonts/NotoSansSymbols2-Regular.ttf',
    fn_bold='fonts/NotoEmoji-Regular.ttf'
)

def exception_handler(exc_type, exc_value, exc_traceback):
    print("=" * 50)
    print("CRITICAL ERROR:")
    print("=" * 50)
    traceback.print_exception(exc_type, exc_value, exc_traceback)
    print("=" * 50)

sys.excepthook = exception_handler

Window.clearcolor = (1, 0, 1, 1)


class RoundedBtn(Button):
    def __init__(self, bg=(0.2, 0.5, 0.9, 1), radius=dp(16), **kw):
        super().__init__(**kw)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0, 0, 0, 0)
        self.color = (1, 1, 1, 1)
        self._bg = bg
        self._original_bg = bg
        self._radius = [radius] if not isinstance(radius, (list, tuple)) else radius
        self._is_hovered = False
        self._is_pressed = False
        self._current_anim = None

        with self.canvas.before:
            self._col = Color(*self._bg)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=self._radius)

        self.bind(pos=self._u, size=self._u)
        Window.bind(mouse_pos=self._on_mouse_pos)

    def _u(self, *a):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def _on_mouse_pos(self, window, pos):
        if self.disabled:
            return

        if self.collide_point(*self.to_widget(*pos)):
            if not self._is_hovered:
                self._is_hovered = True
                self._update_color()
        else:
            if self._is_hovered:
                self._is_hovered = False
                self._update_color()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and not self.disabled:
            self._is_pressed = True
            self._update_color()
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self._is_pressed:
            self._is_pressed = False
            self._update_color()
        return super().on_touch_up(touch)

    def _update_color(self):
        if self._current_anim:
            self._current_anim.cancel(self._col)

        target_color = None
        duration = 0.2

        if self.disabled:
            target_color = (
                self._original_bg[0] * 0.5,
                self._original_bg[1] * 0.5,
                self._original_bg[2] * 0.5,
                self._original_bg[3] * 0.7
            )
        elif self._is_pressed:
            duration = 0.1
            target_color = (
                self._original_bg[0] * 0.7,
                self._original_bg[1] * 0.7,
                self._original_bg[2] * 0.7,
                self._original_bg[3]
            )
        elif self._is_hovered:
            target_color = (
                min(1.0, self._original_bg[0] * 1.15),
                min(1.0, self._original_bg[1] * 1.15),
                min(1.0, self._original_bg[2] * 1.15),
                self._original_bg[3]
            )
        else:
            target_color = self._original_bg

        self._current_anim = Animation(rgba=target_color, duration=duration, transition='out_quad')
        self._current_anim.start(self._col)

    def on_disabled(self, instance, value):
        self._update_color()

def make_vertical_gradient_texture(h=256, c1=(0.95, 0.97, 1, 1), c2=(0.9, 0.93, 0.99, 1)):
    h = max(2, int(h))
    buf = bytearray()
    for i in range(h):
        t = i / (h - 1)
        r = int((c1[0] * (1 - t) + c2[0] * t) * 255)
        g = int((c1[1] * (1 - t) + c2[1] * t) * 255)
        b = int((c1[2] * (1 - t) + c2[2] * t) * 255)
        a = int((c1[3] * (1 - t) + c2[3] * t) * 255)
        buf.extend(bytes((r, g, b, a)))
    tex = Texture.create(size=(1, h), colorfmt='rgba')
    tex.blit_buffer(bytes(buf), colorfmt='rgba', bufferfmt='ubyte')
    tex.wrap = 'repeat'
    return tex


class TopBar(BoxLayout):
    def __init__(self):
        super().__init__(size_hint_y=None, height=dp(62), spacing=dp(8))

        self._bg_tex = make_vertical_gradient_texture(
            h=128,
            c1=(0.22, 0.48, 0.88, 1),
            c2=(0.16, 0.36, 0.78, 1)
        )

        with self.canvas.before:
            Color(1, 1, 1, 1)
            self._round = RoundedRectangle(pos=self.pos, size=self.size, radius=[0, 0, dp(16), dp(16)])
            self._bg_rect = Rectangle(texture=self._bg_tex, pos=self.pos, size=self.size)

        self.bind(pos=self._upd, size=self._upd)

        left_box = BoxLayout(
            size_hint_x=1,
            padding=[dp(14), 0, 0, 0],
            spacing=dp(6)
        )

        self.logo = Label(
            text='[b]MAX[/b]',
            markup=True,
            color=(1, 1, 1, 1),
            size_hint_x=None,
            width=dp(56)
        )

        self.title = Label(
            text='TimeManagement',
            color=(1, 1, 1, 1),
            halign='left',
            valign='middle',
            font_size='15sp'
        )
        self.title.bind(size=self.title.setter('text_size'))

        left_box.add_widget(self.logo)
        left_box.add_widget(self.title)

        self.add_widget(left_box)

        right_box = BoxLayout(
            orientation='vertical',
            size_hint_x=None,
            width=dp(200),
            padding=[0, dp(8), dp(14), dp(8)]
        )

        time_row = BoxLayout(
            size_hint_y=None,
            height=dp(22),
            spacing=dp(6)
        )

        self.time_label = Label(
            text=time.strftime('%H:%M'),
            color=(1, 1, 1, 1),
            halign='right',
            valign='middle',
            font_size='18sp',
            bold=True
        )
        self.time_label.bind(size=self.time_label.setter('text_size'))

        time_row.add_widget(self.time_label)

        self.date_label = Label(
            text=self._get_full_date(),
            color=(1, 1, 1, 0.9),
            halign='right',
            valign='top',
            font_size='12sp',
            size_hint_y=None,
            height=dp(16)
        )
        self.date_label.bind(size=self.date_label.setter('text_size'))

        right_box.add_widget(time_row)
        right_box.add_widget(self.date_label)

        self.add_widget(right_box)

        Clock.schedule_interval(self._update_time, 1)

    def _get_weekday(self):
        weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
        return weekdays[datetime.now().weekday()]

    def _get_full_date(self):
        months = ['Января', 'Февраля', 'Марта', 'Апреля', 'Мая', 'Июня',
                  'Июля', 'Августа', 'Сентября', 'Октября', 'Ноября', 'Декабря']
        now = datetime.now()
        return f"{now.day} {months[now.month - 1]} {now.year} года"

    def _update_time(self, dt):
        self.time_label.text = self._get_weekday() + " " + time.strftime('%H:%M')
        self.date_label.text = self._get_full_date()

    def _upd(self, *a):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size
        self._round.pos = self.pos
        self._round.size = self.size

class BottomBar(BoxLayout):
    def __init__(self):
        super().__init__(size_hint_y=None, height=dp(68), padding=[dp(12), dp(10)], spacing=dp(10))
        with self.canvas.before:
            Color(0.88, 0.88, 0.88, 1)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[18, 18, 0, 0])
        self.bind(pos=self._up, size=self._up)
        self.list_btn = RoundedBtn(text='Список задач', bg=(0.25, 0.55, 0.9, 1), radius=14, font_size='14sp')
        self.settings_btn = RoundedBtn(text='⚙', bg=(0.66, 0.66, 0.66, 1), radius=12, size_hint_x=None, width=dp(52), font_size='20sp', font_name='Emojis', bold=True)

        self.add_widget(self.list_btn)
        self.add_widget(self.settings_btn)

    def _up(self, *a):
        self._bg.pos = self.pos
        self._bg.size = self.size

def format_duration(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    parts = []
    if hours > 0:
        parts.append(f"{hours}ч")
    if minutes > 0 or hours == 0:
        parts.append(f"{minutes}м")
    return " ".join(parts)

def is_same_day(ts1: int, ts2: int) -> bool:
    d1 = datetime.fromtimestamp(ts1)
    d2 = datetime.fromtimestamp(ts2)
    return d1.date() == d2.date()

class TaskCard(BoxLayout):
    def __init__(self, title, project, description, start_time, end_time, started=False, completed_time=None, task_id=None):
        super().__init__(orientation='vertical', size_hint_y=None, spacing=dp(10))
        self._radius = [18]
        self._top_h = dp(52)
        self._bot_min = dp(48)
        self._title = title
        self._project = project
        self._description = description
        self._start_time = start_time
        self._end_time = end_time
        self._started = started
        self._task_id = task_id
        self._state = 'active' if self._started else 'next'
        self._completed_time = completed_time

        with self.canvas.before:
            Color(0, 0, 0, 0.06)
            self._shadow = RoundedRectangle(pos=(self.x, self.y - dp(1)), size=self.size, radius=self._radius)
            Color(1, 1, 1, 1)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=self._radius)
        self.bind(pos=self._upd_bg, size=self._upd_bg)

        top = BoxLayout(size_hint_y=None, height=self._top_h, padding=[dp(14), 0], spacing=dp(8))
        with top.canvas.before:
            top._col = Color(0.22, 0.5, 0.9, 1)
            top._r = RoundedRectangle(pos=top.pos, size=top.size, radius=[18, 18, 0, 0])
        top.bind(pos=lambda w, v: setattr(top._r, 'pos', v), size=lambda w, v: setattr(top._r, 'size', v))

        title_lbl = Label(text=f'[b]{self._title}[/b]', markup=True, color=(1, 1, 1, 1),
                          halign='left', valign='middle')
        title_lbl.size_hint = (1, 1)
        title_lbl.bind(size=title_lbl.setter('text_size'))

        left_anchor = AnchorLayout(anchor_x='left', anchor_y='center')
        left_anchor.add_widget(title_lbl)
        left_anchor.size_hint_x = 1

        sep = Widget(size_hint_x=None, width=dp(1))
        with sep.canvas.before:
            Color(1, 1, 1, 0.36)
            sep._r = Rectangle(pos=sep.pos, size=sep.size)
        sep.bind(pos=lambda w, v: setattr(sep._r, 'pos', v), size=lambda w, v: setattr(sep._r, 'size', v))

        proj_lbl = Label(text=self._project, color=(1, 1, 1, 0.95),
                         halign='center', valign='middle')
        proj_lbl.bind(size=proj_lbl.setter('text_size'))
        right_anchor = AnchorLayout(anchor_x='center', anchor_y='center')
        right_anchor.add_widget(proj_lbl)
        right_anchor.size_hint_x = 1

        top.add_widget(left_anchor)
        top.add_widget(sep)
        top.add_widget(right_anchor)

        mid = BoxLayout(size_hint_y=None, padding=[dp(14), dp(10), dp(14), dp(10)])
        self._desc = Label(text=self._description, color=(0.12, 0.12, 0.12, 1), halign='left', valign='top',
                           size_hint_y=None)
        self._desc.bind(size=self._desc.setter('text_size'))
        mid.add_widget(self._desc)

        bot = BoxLayout(size_hint_y=None, padding=[dp(12), dp(8), dp(12), dp(8)], spacing=dp(8))
        with bot.canvas.before:
            Color(0.96, 0.97, 0.99, 1)
            bot._r = RoundedRectangle(pos=bot.pos, size=bot.size, radius=[0, 0, 18, 18])
        bot.bind(pos=lambda w, v: setattr(bot._r, 'pos', v), size=lambda w, v: setattr(bot._r, 'size', v))

        self._time = Label(
            text='',
            color=(0.22, 0.22, 0.22, 1),
            halign='left',
            valign='middle',
            size_hint_x=1
        )
        self._time.bind(size=self._time.setter('text_size'))

        self._spacer = Widget(size_hint_x=None, width=dp(6))
        self._check = RoundedBtn(text='✓', bg=(0.25, 0.75, 0.4, 1), radius=12, size_hint_x=None, width=dp(48),
                                 font_size='20sp', font_name='Emojis')
        def _on_finish(instance):
            from datetime import datetime
            now_ts = int(datetime.now().timestamp())
            task = taskManager.get_tasks()[self._task_id]
            deadline_ts = task.get("end_time")

            if deadline_ts is not None and now_ts > deadline_ts:
                overdue_sec = now_ts - deadline_ts
                self.mark_completed_overdue(
                    datetime.fromtimestamp(now_ts).strftime('%Y-%m-%d %H:%M'),
                    overdue_sec
                )
                taskManager.edit_task(
                    self._task_id,
                    state="completed_overdue",
                    completed_time=now_ts
                )
            else:
                self.mark_completed(
                    datetime.fromtimestamp(now_ts).strftime('%Y-%m-%d %H:%M')
                )
                taskManager.edit_task(
                    self._task_id,
                    state="completed",
                    completed_time=now_ts
                )
            taskManager.edit_task(self._task_id, state="completed")
            MDApp.get_running_app().refresh_tasks()

        self._check.bind(on_release=_on_finish)

        bot.add_widget(self._time)
        bot.add_widget(self._spacer)
        bot.add_widget(self._check)

        self.add_widget(top)
        self.add_widget(mid)
        self.add_widget(bot)

        self._top = top
        self._proj_lbl = proj_lbl
        self._title_lbl = title_lbl
        self._mid = mid
        self._bot = bot

        Clock.schedule_once(self._post, 0)
        self.bind(width=lambda *a: self._layout())

    def _post(self, dt):
        self._update_state_visuals()
        self._layout()

    def _set_time_text(self):
            all_tasks = taskManager.get_tasks()
            self._time.text = self.get_task_time_display(all_tasks[self._task_id])

    @staticmethod
    def get_task_time_display(task: dict) -> str:
        now_ts = int(datetime.now().timestamp())

        if task["state"] in ("completed", "completed_overdue"):
            completed_ts = task.get("completed_time")
            if not completed_ts:
                return "-"
            display = f"Завершено {datetime.fromtimestamp(completed_ts).strftime('%d.%m %H:%M')}"
            if task["state"] == "completed_overdue":
                overdue_sec = completed_ts - task["end_time"]
                if overdue_sec > 0:
                    display += f" +{format_duration(overdue_sec)}"
            return display

        elif task["state"] == "active":
            deadline_ts = task["end_time"]
            delta = deadline_ts - now_ts
            if delta < 0:
                return f"Просрочено {format_duration(now_ts - deadline_ts)}"
            return f"Осталось {format_duration(delta)}"

        elif task["state"] == "next":
            start_ts = task["start_time"]
            delta = start_ts - now_ts
            if delta > 0:
                return f"Начало через {format_duration(delta)}"
            elif delta < 0:
                return f"Опоздание {format_duration(-delta)}"
            return "Начало сейчас"

        return "-"

    def _layout(self, *a):
        pad = dp(28)
        w = max(dp(56), self.width - pad)
        self._desc.text_size = (w, None)
        time_width = w - (self._check.width + dp(6) if self._check.parent is not None and self._check.width else dp(0))
        self._time.text_size = (time_width, None)
        self._desc.texture_update()
        self._time.texture_update()
        self._desc.height = self._desc.texture_size[1]
        self._time.height = self._time.texture_size[1]
        self._mid.height = self._desc.height + dp(20)
        self._bot.height = max(self._bot_min, self._time.height + dp(16))
        self.height = self._top_h + self._mid.height + self._bot.height + dp(14)

    def _upd_bg(self, *a):
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._shadow.pos = (self.x, self.y - dp(1))
        self._shadow.size = self.size

    def set_state(self, state: str):
        if state not in ('active', 'next', 'completed'):
            return
        self._state = state
        if state == 'active':
            self._started = True
        self._update_state_visuals()
        self._layout()

    def mark_active(self):
        self.set_state('active')

    def mark_next(self):
        self.set_state('next')

    def mark_completed_overdue(self, completed_time=None, overdue_time=None):
        if completed_time is None:
            from datetime import datetime
            completed_time = datetime.now().strftime('%Y-%m-%d %H:%M')

        self._completed_time = completed_time
        self._overdue_time = overdue_time
        self.set_state('completed_overdue')

    def mark_completed(self, completed_time=None):
        if completed_time is None:
            from datetime import datetime
            completed_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        self._completed_time = completed_time
        self.set_state('completed')

    def _update_state_visuals(self):
        if self._state == 'active':
            self._top._col.rgba = (0.22, 0.5, 0.9, 1)
        elif self._state == 'next':
            self._top._col.rgba = (0.6, 0.6, 0.6, 1)
        elif self._state == 'completed':
            self._top._col.rgba = (0.25, 0.75, 0.4, 1)
        elif self._state == 'completed_overdue':
            self._top._col.rgba = (0.25, 0.75, 0.4, 1)
        self._set_time_text()

        if self._state == 'active':
            if self._check.parent is None:
                self._bot.add_widget(self._spacer)
                self._bot.add_widget(self._check)
        else:
            if self._check.parent is not None:
                try:
                    self._bot.remove_widget(self._check)
                except Exception:
                    pass
            if self._spacer.parent is not None:
                try:
                    self._bot.remove_widget(self._spacer)
                except Exception:
                    pass

class ContentPanel(BoxLayout):
    def __init__(self):
        super().__init__(orientation='vertical', padding=[0, dp(64), 0, dp(64)])
        with self.canvas.before:
            Color(1, 1, 1, 0)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._up, size=self._up)

        self.scroll = ScrollView(size_hint=(1, 1), bar_width=dp(4), do_scroll_x=False)
        self.container = BoxLayout(
            orientation='vertical',
            size_hint_x=1,
            size_hint_y=None,
            spacing=dp(24),
            padding=[dp(20), dp(18), dp(20), dp(18)]
        )
        self.container.bind(minimum_height=self.container.setter('height'))

        all_tasks = taskManager.get_tasks() or []

        center_idx = None
        prev_idx = None
        next_idx = None

        if all_tasks:
            for i, t in enumerate(all_tasks):
                if t.get("state") == "active":
                    center_idx = i
                    break

            if center_idx is None:
                next_indices = [i for i, t in enumerate(all_tasks) if t.get("state") == "next"]
                if next_indices:
                    center_idx = next_indices[0]
                    prev_idx = center_idx - 1 if center_idx - 1 >= 0 else None
                    next_idx = next_indices[1] if len(next_indices) > 1 else None
                else:
                    center_idx = 0
            else:
                prev_idx = center_idx - 1 if center_idx - 1 >= 0 else None
                next_idx = center_idx + 1 if center_idx + 1 < len(all_tasks) else None

        cards_to_add = []
        if all_tasks:
            if prev_idx is not None:
                cards_to_add.append(("prev", all_tasks[prev_idx], prev_idx))
            cards_to_add.append(("center", all_tasks[center_idx], center_idx))
            if next_idx is not None:
                cards_to_add.append(("next", all_tasks[next_idx], next_idx))

        for role, task, idx in cards_to_add:
            card = TaskCard(
                title=task.get("title", "Без названия"),
                project=task.get("project", ""),
                description=task.get("description", ""),
                start_time=task.get("start_time", 0),
                end_time=task.get("end_time", 0),
                started=task.get("started", False),
                task_id=idx
            )
            state = task.get("state")
            if state == "completed":
                card.mark_completed(task.get("completed_time"))
            elif state == "completed_overdue":
                completed_time = task.get("completed_time")
                end_time = task.get("end_time")
                overdue = (completed_time - end_time) if (completed_time and end_time) else None
                card.mark_completed_overdue(completed_time, overdue)
            elif state == "active":
                card.mark_active()
            elif state == "next":
                card.mark_next()

            card.bind(height=lambda *a: setattr(self.container, 'height', self.container.minimum_height))
            self.container.add_widget(card)

        self.scroll.add_widget(self.container)
        self.add_widget(self.scroll)

    def _up(self, *a):
        self._bg.pos = self.pos
        self._bg.size = self.size

    def refresh(self):
        self.container.clear_widgets()
        all_tasks = taskManager.get_tasks() or []

        center_idx = None
        prev_idx = None
        next_idx = None

        if all_tasks:
            for i, t in enumerate(all_tasks):
                if t.get("state") == "active":
                    center_idx = i
                    break

            if center_idx is None:
                next_indices = [i for i, t in enumerate(all_tasks) if t.get("state") == "next"]
                if next_indices:
                    center_idx = next_indices[0]
                    prev_idx = center_idx - 1 if center_idx - 1 >= 0 else None
                    next_idx = next_indices[1] if len(next_indices) > 1 else None
                else:
                    center_idx = 0
            else:
                prev_idx = center_idx - 1 if center_idx - 1 >= 0 else None
                next_idx = center_idx + 1 if center_idx + 1 < len(all_tasks) else None

        cards_to_add = []
        if all_tasks:
            if prev_idx is not None:
                cards_to_add.append(("prev", all_tasks[prev_idx], prev_idx))
            cards_to_add.append(("center", all_tasks[center_idx], center_idx))
            if next_idx is not None:
                cards_to_add.append(("next", all_tasks[next_idx], next_idx))

        for role, task, idx in cards_to_add:
            card = TaskCard(
                title=task.get("title", "Без названия"),
                project=task.get("project", ""),
                description=task.get("description", ""),
                start_time=task.get("start_time", 0),
                end_time=task.get("end_time", 0),
                started=task.get("started", False),
                task_id=idx
            )
            state = task.get("state")
            if state == "completed":
                card.mark_completed(task.get("completed_time"))
            elif state == "completed_overdue":
                completed_time = task.get("completed_time")
                end_time = task.get("end_time")
                overdue = (completed_time - end_time) if (completed_time and end_time) else None
                card.mark_completed_overdue(completed_time, overdue)
            elif state == "active":
                card.mark_active()
            elif state == "next":
                card.mark_next()

            card.bind(height=lambda *a: setattr(self.container, 'height', self.container.minimum_height))
            self.container.add_widget(card)

class STaskCard(FloatLayout):
    def __init__(self, title, project, description, start_time, end_time, completed_time=None, started=False, state="", task_id=0):
        super().__init__(size_hint_y=None)
        self._radius = [18]
        self._compact_h = dp(56)
        self._title = title
        self._project = project
        self._description = description
        self._start_time = start_time
        self._end_time = end_time
        self._started = started
        self._task_id = task_id
        if completed_time is not None and end_time is not None:
            self._overdue_time = completed_time - end_time
        else:
            self._overdue_time = None
        self._completed_time = completed_time
        self._state = state
        self._completed_time = None
        self._expanded = False

        self._touch_start_x = 0
        self._touch_start_y = 0
        self._swipe_offset = 0
        self._is_swiping = False

        self.main_container = BoxLayout(orientation='vertical', size_hint=(None, None))
        self.main_container.size = (self.width, self._compact_h)

        with self.main_container.canvas.before:
            Color(0, 0, 0, 0.06)
            self._shadow = RoundedRectangle(pos=(self.main_container.x, self.main_container.y - dp(1)),
                                            size=self.main_container.size, radius=self._radius)
            Color(1, 1, 1, 1)
            self._bg = RoundedRectangle(pos=self.main_container.pos, size=self.main_container.size, radius=self._radius)

        self.main_container.bind(pos=self._upd_bg, size=self._upd_bg)

        self.compact_view = BoxLayout(size_hint_y=None, height=self._compact_h, padding=[dp(14), 0], spacing=dp(8))
        with self.compact_view.canvas.before:
            self.compact_view._col = Color(0.22, 0.5, 0.9, 1)
            self.compact_view._r = RoundedRectangle(pos=self.compact_view.pos, size=self.compact_view.size,
                                                    radius=self._radius)
        self.compact_view.bind(pos=lambda w, v: setattr(self.compact_view._r, 'pos', v),
                               size=lambda w, v: setattr(self.compact_view._r, 'size', v))

        self.title_lbl = Label(text=f'[b]{self._title}[/b]', markup=True, color=(1, 1, 1, 1),
                               halign='left', valign='middle')
        self.title_lbl.bind(size=self.title_lbl.setter('text_size'))
        left_anchor = AnchorLayout(anchor_x='left', anchor_y='center')
        left_anchor.add_widget(self.title_lbl)
        left_anchor.size_hint_x = 1

        self.time_lbl = Label(text='', color=(1, 1, 1, 0.95), halign='right', valign='middle',
                              size_hint_x=None, width=dp(100))
        self.time_lbl.bind(size=self.time_lbl.setter('text_size'))

        self.compact_view.add_widget(left_anchor)
        self.compact_view.add_widget(self.time_lbl)

        self.expanded_content = BoxLayout(orientation='vertical', size_hint_y=None, height=0, opacity=0)

        self.desc_container = BoxLayout(size_hint_y=None, padding=[dp(14), dp(10), dp(14), dp(10)])
        self._desc = Label(text=self._description, color=(0.12, 0.12, 0.12, 1), halign='left', valign='top',
                           size_hint_y=None)
        self._desc.bind(size=self._desc.setter('text_size'))
        self.desc_container.add_widget(self._desc)

        bot = BoxLayout(size_hint_y=None, height=dp(48), padding=[dp(12), dp(8), dp(12), dp(8)], spacing=dp(8))
        with bot.canvas.before:
            Color(0.96, 0.97, 0.99, 1)
            bot._r = RoundedRectangle(pos=bot.pos, size=bot.size, radius=[0, 0, 18, 18])
        bot.bind(pos=lambda w, v: setattr(bot._r, 'pos', v), size=lambda w, v: setattr(bot._r, 'size', v))

        proj_lbl = Label(text=self._project, color=(0.22, 0.22, 0.22, 1), halign='left', valign='middle')
        proj_lbl.bind(size=proj_lbl.setter('text_size'))
        bot.add_widget(proj_lbl)

        self.expanded_content.add_widget(self.desc_container)
        self.expanded_content.add_widget(bot)

        self.main_container.add_widget(self.compact_view)
        self.main_container.add_widget(self.expanded_content)

        self.edit_btn = RoundedBtn(text='✎', bg=(0.3, 0.6, 0.9, 1), radius=[12, 0, 0, 12], size_hint=(None, None),
                                   size=(dp(80), self._compact_h), font_size='24sp', pos=(0, 0), font_name='Emojis')
        self.edit_btn.opacity = 0
        self.edit_btn.bind(on_release=self._on_edit)

        self.delete_btn = RoundedBtn(text='🗑', bg=(0.9, 0.3, 0.3, 1), radius=[0, 12, 12, 0], size_hint=(None, None),
                                     size=(dp(80), self._compact_h), font_size='24sp', pos=(0, 0), font_name='Emojis')
        self.delete_btn.opacity = 0
        self.delete_btn.bind(on_release=self._on_delete)

        self.add_widget(self.edit_btn)
        self.add_widget(self.delete_btn)
        self.add_widget(self.main_container)

        self._swipe_gap = dp(14)
        self._swipe_full = dp(80) - self._swipe_gap
        Clock.schedule_once(self._post, 0)
        self.bind(size=self._layout, pos=self._layout)

    def _on_edit(self, instance):
        task = taskManager.get_tasks()[self._task_id]
        app = MDApp.get_running_app()
        if app and hasattr(app, 'root_layout'):
            app.root_layout.show_task_editor(task=task, task_id=self._task_id)
        self._animate_swipe_close()

    def _on_delete(self, instance):
        if not hasattr(self, '_delete_dialog') or self._delete_dialog is None:
            self._delete_dialog = MDDialog(
                title="Удаление задачи",
                text=f"Вы уверены, что хотите удалить задачу '{self._title}'?",
                buttons=[
                    MDFlatButton(
                        text="ОТМЕНА",
                        on_release=lambda x: self._cancel_delete()
                    ),
                    MDFlatButton(
                        text="УДАЛИТЬ",
                        theme_text_color="Custom",
                        text_color=(0.9, 0.3, 0.3, 1),
                        on_release=lambda x: self._confirm_delete()
                    ),
                ],
            )
        else:
            self._delete_dialog.text = f"Вы уверены, что хотите удалить задачу '{self._title}'?"

        self._delete_dialog.open()

    def _cancel_delete(self):
        self._delete_dialog.dismiss()
        self._animate_swipe_close()

    def _confirm_delete(self):
        self._delete_dialog.dismiss()
        taskManager.delete_task(self._task_id)
        app = MDApp.get_running_app()
        if app and hasattr(app, 'refresh_tasks'):
            app.refresh_tasks()
        self._animate_swipe_close()

    def _post(self, dt):
        self._update_state_visuals()
        self._layout()

    def _set_time_text(self):
        import time
        from datetime import datetime

        task = taskManager.get_tasks()[self._task_id]

        def format_duration(seconds: int) -> str:
            hours, rem = divmod(seconds, 3600)
            minutes, _ = divmod(rem, 60)
            if hours > 0:
                return f"{hours}ч {minutes}м"
            return f"{minutes}м"

        now_ts = int(time.time())

        state = task.get("state")
        start_ts = task.get("start_time")
        end_ts = task.get("end_time")
        completed_ts = task.get("completed_time")
        overdue_sec = max(0, completed_ts - end_ts) if completed_ts and end_ts else None
        overdue_sec_two = max(0, now_ts - end_ts) if now_ts and end_ts else None

        if state in ("completed", "completed_overdue"):
            text = "Завершено " + datetime.fromtimestamp(completed_ts).strftime(
                "%d.%m %H:%M") if completed_ts else datetime.fromtimestamp(end_ts).strftime("%d.%m %H:%M")
            if state == "completed_overdue" and overdue_sec:
                text += f"\n+{format_duration(overdue_sec)}"
            self.time_lbl.text = text
            return

        if state == "active":
            delta = end_ts - now_ts
            self.time_lbl.text = "До " + format_duration(delta) if delta > 0 else f"Просрочено на {format_duration(overdue_sec_two)}"
            return

        if state == "next":
            delta = start_ts - now_ts
            if delta > 0:
                self.time_lbl.text = format_duration(delta)
            elif delta < 0:
                self.time_lbl.text = f"опоздание {format_duration(-delta)}"
            else:
                self.time_lbl.text = "Совсем скоро начнётся"
            return

    def _layout(self, *a):
        if self.width == 100:
            return

        self.main_container.width = self.width
        pad = dp(28)
        w = max(dp(56), self.width - pad)
        self._desc.text_size = (w, None)
        self._desc.texture_update()
        self._desc.height = self._desc.texture_size[1]
        self.desc_container.height = self._desc.height + dp(20)

        if self._expanded:
            self.expanded_content.height = self.desc_container.height + dp(48)
            self.main_container.height = self._compact_h + self.expanded_content.height
        else:
            self.main_container.height = self._compact_h

        self.height = self.main_container.height

        self.main_container.x = self.x + self._swipe_offset
        self.main_container.y = self.y

        self.edit_btn.y = self.y
        self.edit_btn.x = self.x
        self.edit_btn.height = self.height

        self.delete_btn.y = self.y
        self.delete_btn.x = self.x + self.width - dp(80)
        self.delete_btn.height = self.height

    def _upd_bg(self, *a):
        self._bg.pos = self.main_container.pos
        self._bg.size = self.main_container.size
        self._shadow.pos = (self.main_container.x, self.main_container.y - dp(1))
        self._shadow.size = self.main_container.size

    def toggle_expand(self):
        self._expanded = not self._expanded

        if self._expanded:
            target_height = self.desc_container.height + dp(48)
            anim = Animation(height=target_height, opacity=1, duration=0.2)
            anim.start(self.expanded_content)
        else:
            anim = Animation(height=0, opacity=0, duration=0)
            anim.start(self.expanded_content)

        Clock.schedule_once(lambda dt: self._layout(), 0.21)

    def set_state(self, state: str):
        if state not in ('active', 'next', 'completed', 'completed_overdue'):
            return
        self._state = state
        if state == 'active':
            self._started = True
        self._update_state_visuals()

    def mark_completed(self, completed_time=None):
        if completed_time is None:
            from datetime import datetime
            completed_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        self._completed_time = completed_time
        self.set_state('completed')

    def mark_completed_overdue(self, completed_time=None, overdue_time=None):
        if completed_time is None:
            from datetime import datetime
            completed_time = datetime.now().strftime('%Y-%m-%d %H:%M')
        self._completed_time = completed_time
        if overdue_time:
            self._overdue_time = overdue_time
        self.set_state('completed_overdue')

    def _update_state_visuals(self):
        if self._state == 'active':
            self.compact_view._col.rgba = (0.4, 0.5, 0.6, 1)
        elif self._state == 'next':
            self.compact_view._col.rgba = (0.5, 0.5, 0.5, 1)
        elif self._state == 'completed':
            self.compact_view._col.rgba = (0.4, 0.7, 0.5, 1)
        elif self._state == 'completed_overdue':
            self.compact_view._col.rgba = (0.6, 0.3, 0.4, 1)

        self._set_time_text()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.edit_btn.collide_point(*touch.pos) and self.edit_btn.opacity > 0:
                return self.edit_btn.on_touch_down(touch)
            if self.delete_btn.collide_point(*touch.pos) and self.delete_btn.opacity > 0:
                return self.delete_btn.on_touch_down(touch)

            self._touch_start_x = touch.x
            self._touch_start_y = touch.y
            self._is_swiping = False
            touch.grab(self)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            dx = touch.x - self._touch_start_x
            dy = touch.y - self._touch_start_y

            # если вы это заметили то не реагируйте на это, это рудимент.
            # РУДИМЕНТ
            if not self._is_swiping and abs(dx) > dp(10):
                if abs(dx) > abs(dy) * 1.5:
                    self._is_swiping = True
            # РУДИМЕНТ

            if dx > 0:
                self._swipe_offset = min(dx, self._swipe_full)
                self.edit_btn.opacity = self._swipe_offset / dp(80)
                self.delete_btn.opacity = 0
            else:
                self._swipe_offset = max(dx, -self._swipe_full)
                self.delete_btn.opacity = abs(self._swipe_offset) / dp(80)
                self.edit_btn.opacity = 0
            self._layout()
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)

            if not self._is_swiping:
                self.toggle_expand()

            threshold = dp(40)
            full = self._swipe_full

            if abs(self._swipe_offset) >= threshold:
                target = full if self._swipe_offset > 0 else -full
                self._animate_swipe_to(target)
            else:
                self._animate_swipe_to(0)

            return True
        return super().on_touch_up(touch)

    def _animate_swipe_to(self, target_offset):
        anim = Animation(_swipe_offset=target_offset, duration=0.18)
        anim.bind(on_progress=lambda *a: self._layout())

        if target_offset == 0:
            anim.bind(on_complete=lambda *a: self._on_swipe_closed())
        else:
            anim.bind(on_complete=lambda *a: self._on_swipe_open(target_offset))

        anim.start(self)

    def _on_swipe_closed(self):
        self._swipe_offset = 0
        self.edit_btn.opacity = 0
        self.delete_btn.opacity = 0
        self._layout()
        self._is_swiping = False

    def _on_swipe_open(self, final_offset):
        self._swipe_offset = final_offset
        if final_offset > 0:
            self.edit_btn.opacity = 1
            self.delete_btn.opacity = 0
        else:
            self.delete_btn.opacity = 1
            self.edit_btn.opacity = 0
        self._layout()
        self._is_swiping = False

    def _animate_swipe_close(self):
        anim = Animation(_swipe_offset=0, duration=0.2)
        anim.bind(on_progress=lambda *a: self._layout())
        anim.bind(on_complete=lambda *a: self._on_swipe_closed())
        anim.start(self)


def add_debug_border(widget, border_color=(1, 0, 0, 1), line_width=2):
    with widget.canvas.after:
        widget.debug_color = Color(*border_color)
        widget.debug_rect = Line(
            rectangle=(widget.x, widget.y, widget.width, widget.height),
            width=line_width
        )

    def update_debug_rect(instance, value):
        instance.debug_rect.rectangle = (
            instance.x, instance.y, instance.width, instance.height
        )

    widget.bind(pos=update_debug_rect, size=update_debug_rect)



class TaskListPanel(BoxLayout):
    def __init__(self):
        super().__init__(orientation='vertical')

        with self.canvas.before:
            Color(0.95, 0.96, 0.98, 1)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(16), dp(16), 0, 0])

        self.bind(pos=self._upd, size=self._upd)

        header = BoxLayout(size_hint_y=None, height=dp(56),padding=[dp(16), 4], spacing=dp(8))
        title = Label(
            text='[b]Список задач[/b]',
            markup=True,
            color=(0.2, 0.2, 0.2, 1),
            halign='left',
            valign='middle',
            font_size='18sp'
        )
        title.bind(size=title.setter('text_size'))
        header.add_widget(title)

        right_box = BoxLayout(size_hint_x=None, height=dp(56), width=dp(120), spacing=dp(8), padding=[dp(0), 0])

        add_btn = RoundedBtn(text='➕', bg=(0.25, 0.6, 0.95, 1), radius=12, size_hint_x=None, font_size='20sp', font_name='Emojis', bold=True)
        add_btn.bind(height=lambda i, v: setattr(i, 'width', v))
        add_btn.bind(on_release=lambda *_: self.parent.show_task_editor())


        close_btn = RoundedBtn(text='❌', bg=(0.7, 0.7, 0.7, 1), radius=12, size_hint_x=None, font_size='20sp', font_name='Emojis', bold=True)
        close_btn.bind(height=lambda instance, value: setattr(instance, 'width', value))

        header.add_widget(add_btn)
        header.add_widget(close_btn)

        # header.add_widget(right_box)
        self.add_widget(header)

        self._close_btn = close_btn
        self._add_btn = add_btn

        self._add_btn.bind(on_release=lambda *a: Clock.schedule_once(lambda dt: MDApp.get_running_app().root.show_task_editor_new(), 0))

        self.scroll = ScrollView(size_hint=(1, 1), bar_width=dp(4), do_scroll_x=False)
        self.container = BoxLayout(
            orientation='vertical',
            size_hint_x=1,
            size_hint_y=None,
            spacing=dp(12),
            padding=[dp(20), dp(18), dp(20), dp(18)]
        )
        self.container.bind(minimum_height=self.container.setter('height'))

        all_tasks = taskManager.get_tasks() or []

        for task_id, task in enumerate(all_tasks):
            card = STaskCard(
                title=task.get("title", "Без названия"),
                project=task.get("project", ""),
                description=task.get("description", ""),
                start_time=task.get("start_time", 0),
                end_time=task.get("end_time", 0),
                completed_time=task.get("completed_time", None),
                started=task.get("started", False),
                state=task.get("state", ""),
                task_id=task_id
            )
            card.bind(height=lambda *a: setattr(self.container, 'height', self.container.minimum_height))
            self.container.add_widget(card)

        self.scroll.add_widget(self.container)
        self.add_widget(self.scroll)

    def _upd(self, *a):
        self._bg.pos = self.pos
        self._bg.size = self.size

    def refresh(self):
        self.container.clear_widgets()

        all_tasks = taskManager.get_tasks() or []

        for task_id, task in enumerate(all_tasks):
            card = STaskCard(
                title=task.get("title", "Без названия"),
                project=task.get("project", ""),
                description=task.get("description", ""),
                start_time=task.get("start_time", 0),
                end_time=task.get("end_time", 0),
                completed_time=task.get("completed_time", None),
                started=task.get("started", False),
                state=task.get("state", ""),
                task_id=task_id
            )
            card.bind(height=lambda *a: setattr(self.container, 'height', self.container.minimum_height))
            self.container.add_widget(card)


class TaskEditorPanel(BoxLayout):
    def __init__(self, root, task=None, task_id=None):
        super().__init__(orientation='vertical')
        self.root = root
        self.task = task or {}
        self.task_id = task_id

        with self.canvas.before:
            Color(0.95, 0.96, 0.98, 1)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(16), dp(16), 0, 0])

        self.bind(pos=self._upd, size=self._upd)

        header = BoxLayout(size_hint_y=None, height=dp(56), padding=[dp(16), 4], spacing=dp(8))
        title = Label(
            text='[b]Редактирование задачи[/b]' if task else '[b]Новая задача[/b]',
            markup=True,
            halign='left',
            valign='middle',
            color=(0, 0, 0, 1)
        )
        title.bind(size=title.setter('text_size'))

        self.save_btn = RoundedBtn(text='✔️', bg=(0.5, 0.5, 0.5, 1), radius=12, size_hint_x=None, font_name='Emojis', bold=True)
        self.save_btn.bind(height=lambda i, v: setattr(i, 'width', v))
        self.save_btn.bind(on_release=self._save)
        self.save_btn.disabled = True

        close_btn = RoundedBtn(text='❌', bg=(0.7, 0.7, 0.7, 1), radius=12, size_hint_x=None, font_name='Emojis', bold=True)
        close_btn.bind(height=lambda i, v: setattr(i, 'width', v))
        close_btn.bind(on_release=self._close)

        header.add_widget(title)
        header.add_widget(self.save_btn)
        header.add_widget(close_btn)
        self.add_widget(header)

        scroll = ScrollView()
        content = BoxLayout(orientation='vertical', size_hint_y=None, padding=[dp(20), dp(20)], spacing=dp(16))
        content.bind(minimum_height=content.setter('height'))

        self.title_input = self._field(content, 'Название', self.task.get('title', ''))
        self.project_input = self._field(content, 'Проект', self.task.get('project', ''))
        self.desc_input = self._field(content, 'Описание', self.task.get('description', ''), multiline=True, h=dp(96))

        self.title_input.bind(text=self._check_validation)
        self.project_input.bind(text=self._check_validation)
        self.desc_input.bind(text=self._check_validation)

        self.start_time = self.task.get('start_time')
        self.end_time = self.task.get('end_time')

        self.start_btn = self._time_btn(content, 'Дата начала', self.start_time, self._pick_start)
        self.end_btn = self._time_btn(content, 'Дедлайн', self.end_time, self._pick_end)

        scroll.add_widget(content)
        self.add_widget(scroll)

        self._check_validation()

    def _field(self, parent, text, value, multiline=False, h=dp(96)):
        box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(4))

        lbl = Label(text=text, size_hint_y=None, height=dp(20), halign='left',
                    valign='middle', color=(0, 0, 0, 1), font_size='14sp')
        lbl.bind(size=lbl.setter('text_size'))

        inp = MDTextField(
            hint_text=text,
            mode="rectangle",
            size_hint_y=None,
            multiline=multiline
        )

        if multiline:
            inp.height = h
            inp.max_height = h
            box.height = h + dp(24)
        else:
            inp.height = dp(56)
            box.height = dp(80)

        # box.add_widget(lbl)
        box.add_widget(inp)
        parent.add_widget(box)

        Clock.schedule_once(lambda dt: setattr(inp, 'text', value), 0)

        return inp

    def _time_btn(self, parent, text, value, callback):
        box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(64))

        lbl = Label(text=text, size_hint_y=None, height=dp(20), halign='left', valign='middle', color=(0, 0, 0, 1))
        lbl.bind(size=lbl.setter('text_size'))

        btn = RoundedBtn(
            text=time.strftime('%d.%m.%Y %H:%M', time.localtime(value)) if value else 'Выбрать',
            bg=(0.8, 0.8, 0.8, 1)
        )
        btn.bind(on_release=callback)

        box.add_widget(lbl)
        box.add_widget(btn)
        parent.add_widget(box)
        return btn

    def _check_validation(self, *args):
        is_valid = (
                self.title_input.text.strip() != '' and
                self.project_input.text.strip() != '' and
                self.desc_input.text.strip() != '' and
                self.start_time is not None and
                self.end_time is not None
        )

        self.save_btn.disabled = not is_valid
        if is_valid:
            self.save_btn.bg = (0.3, 0.6, 0.3, 1)
        else:
            self.save_btn.bg = (0.5, 0.5, 0.5, 1)

    def _pick_start(self, *_):
        picker = MDDatePicker()
        picker.bind(on_save=self._start_date)
        picker.open()

    def _start_date(self, _, date, *__):
        picker = MDTimePicker()
        picker.bind(on_save=lambda _, t: self._set_start(date, t))
        picker.open()

    def _set_start(self, date, t):
        self.start_time = int(time.mktime(date.timetuple())) + t.hour * 3600 + t.minute * 60
        self.start_btn.text = time.strftime('%d.%m.%Y %H:%M', time.localtime(self.start_time))
        self._check_validation()

    def _pick_end(self, *_):
        picker = MDDatePicker()
        picker.bind(on_save=self._end_date)
        picker.open()

    def _end_date(self, _, date, *__):
        picker = MDTimePicker()
        picker.bind(on_save=lambda _, t: self._set_end(date, t))
        picker.open()

    def _set_end(self, date, t):
        self.end_time = int(time.mktime(date.timetuple())) + t.hour * 3600 + t.minute * 60
        self.end_btn.text = time.strftime('%d.%m.%Y %H:%M', time.localtime(self.end_time))
        self._check_validation()

    def _save(self, *_):
        if not self.title_input.text.strip() or not self.project_input.text.strip() or \
                not self.desc_input.text.strip() or self.start_time is None or self.end_time is None:
            return

        if self.task_id is None:
            taskManager.add_task(
                title=self.title_input.text,
                project=self.project_input.text,
                description=self.desc_input.text,
                start_time=self.start_time,
                end_time=self.end_time,
                started=False,
                state="next"
            )
        else:
            taskManager.edit_task(
                self.task_id,
                title=self.title_input.text,
                project=self.project_input.text,
                description=self.desc_input.text,
                start_time=self.start_time,
                end_time=self.end_time
            )

        self.root.update_all_task_cards()
        self._close()

    def _close(self, *_):
        anim = Animation(y=-self.height, duration=0.25, transition='in_cubic')
        anim.bind(on_complete=lambda *_: self.root.remove_widget(self))
        anim.start(self)

    def _upd(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size


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


class SettingsPanel(BoxLayout):
    title = ''
    def __init__(self, root):
        super().__init__(orientation='vertical')
        with self.canvas.before:
            Color(0.95, 0.96, 0.98, 1)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(16), dp(16), 0, 0])

        self.bind(pos=self._upd, size=self._upd)
        self.root = root
        self.settings = load_settings()

        header = BoxLayout(size_hint_y=None, height=dp(56), padding=[dp(16), 4], spacing=dp(8))
        _title = Label(
            text='[b]Настройки[/b]',
            markup=True,
            halign='left',
            valign='middle',
            color=(0, 0, 0, 1),
            font_size='18sp'
        )
        _title.bind(size=_title.setter('text_size'))

        close_btn = RoundedBtn(text='❌', bg=(0.7, 0.7, 0.7, 1), radius=12, size_hint_x=None, font_name='Emojis',
                               bold=True)
        close_btn.bind(height=lambda i, v: setattr(i, 'width', v))
        close_btn.bind(on_release=self._close)

        header.add_widget(_title)
        header.add_widget(close_btn)
        self.add_widget(header)

        scroll = ScrollView()
        content = BoxLayout(orientation='vertical', size_hint_y=None, padding=[dp(20), dp(20)], spacing=dp(16))
        content.bind(minimum_height=content.setter('height'))

        section_label = Label(
            text='[b]Уведомления[/b]',
            markup=True,
            size_hint_y=None,
            height=dp(30),
            halign='left',
            valign='middle',
            color=(0.3, 0.3, 0.3, 1),
            font_size='14sp'
        )
        section_label.bind(size=section_label.setter('text_size'))
        content.add_widget(section_label)

        switch_card = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(64),
            padding=[dp(16), dp(12), dp(28), dp(12)],
            spacing=dp(16)
        )

        with switch_card.canvas.before:
            Color(1, 1, 1, 1)
            switch_card._bg = RoundedRectangle(pos=switch_card.pos, size=switch_card.size, radius=[12])
        switch_card.bind(
            pos=lambda w, v: setattr(switch_card._bg, 'pos', v),
            size=lambda w, v: setattr(switch_card._bg, 'size', v)
        )

        label_box = BoxLayout(orientation='vertical', spacing=dp(2))
        notif_label = Label(
            text='Включить уведомления',
            halign='left',
            valign='bottom',
            color=(0.1, 0.1, 0.1, 1),
            font_size='16sp',
            size_hint_y=None,
            height=dp(20)
        )
        notif_label.bind(size=notif_label.setter('text_size'))

        notif_desc = Label(
            text='Получать напоминания о задачах',
            halign='left',
            valign='top',
            color=(0.5, 0.5, 0.5, 1),
            font_size='12sp',
            size_hint_y=None,
            height=dp(16)
        )
        notif_desc.bind(size=notif_desc.setter('text_size'))

        label_box.add_widget(notif_label)
        label_box.add_widget(notif_desc)

        self.notif_switch = MDSwitch(
            size_hint=(None, None),
            size=(dp(36), dp(48))
        )
        Clock.schedule_once(lambda dt: setattr(self.notif_switch, 'active', self.settings.get("notifications_enabled", True)), 0.1)
        self.notif_switch.bind(active=self._on_notif_toggle)

        switch_card.add_widget(label_box)
        switch_card.add_widget(self.notif_switch)
        content.add_widget(switch_card)

        scroll.add_widget(content)
        self.add_widget(scroll)

        footer = BoxLayout(
            size_hint_y=None,
            height=dp(80),
            orientation='vertical',
            padding=[dp(20), dp(12)]
        )

        with footer.canvas.before:
            Color(0.92, 0.93, 0.95, 1)
            footer._bg = Rectangle(pos=footer.pos, size=footer.size)
        footer.bind(
            pos=lambda w, v: setattr(footer._bg, 'pos', v),
            size=lambda w, v: setattr(footer._bg, 'size', v)
        )

        app_name = Label(
            text='[b]Max TimeManagement[/b]',
            markup=True,
            halign='center',
            valign='bottom',
            color=(0.22, 0.5, 0.9, 1),
            font_size='14sp',
            size_hint_y=None,
            height=dp(18)
        )
        app_name.bind(size=app_name.setter('text_size'))

        author = Label(
            text='Автор: Mega4oSS',
            halign='center',
            valign='middle',
            color=(0.4, 0.4, 0.4, 1),
            font_size='12sp',
            size_hint_y=None,
            height=dp(16)
        )
        author.bind(size=author.setter('text_size'))

        year = Label(
            text='2025 год',
            halign='center',
            valign='top',
            color=(0.5, 0.5, 0.5, 1),
            font_size='11sp',
            size_hint_y=None,
            height=dp(14)
        )
        year.bind(size=year.setter('text_size'))

        footer.add_widget(app_name)
        footer.add_widget(author)
        footer.add_widget(year)

        self.add_widget(footer)

    def _on_notif_toggle(self, instance, value):
        self.settings["notifications_enabled"] = value
        save_settings(self.settings)

    def _close(self, *_):
        anim = Animation(y=-self.height, duration=0.25, transition='in_cubic')
        anim.bind(on_complete=lambda *_: self.root.remove_widget(self))
        anim.start(self)

    def _upd(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size

class RootLayout(FloatLayout):
    def __init__(self):
        super().__init__()

        self._bg_tex = make_vertical_gradient_texture(
            h=128,
            c1=(0.95, 0.96, 0.97, 1),
            c2=(0.88, 0.90, 0.93, 1)
        )

        with self.canvas.before:
            Color(1, 1, 1, 1)
            self._round = RoundedRectangle(pos=self.pos, size=self.size, radius=[0, 0, dp(16), dp(16)])
            self._bg_rect = Rectangle(texture=self._bg_tex, pos=self.pos, size=self.size)

        self.bind(pos=self._upd, size=self._upd)

        self.content = ContentPanel()
        self.add_widget(self.content)

        self.top_bar = TopBar()
        self.top_bar.size_hint_y = None
        self.top_bar.height = dp(64)
        self.top_bar.pos_hint = {'top': 1}
        self.add_widget(self.top_bar)

        self.bottom_bar = BottomBar()
        self.bottom_bar.size_hint_y = None
        self.bottom_bar.height = dp(64)
        self.bottom_bar.pos_hint = {'y': 0}
        self.add_widget(self.bottom_bar)

        self.task_list = TaskListPanel()
        self.task_list.pos_hint = {'x': 0}
        self.task_list.y = -self.height
        self.add_widget(self.task_list)

        self.bottom_bar.list_btn.bind(on_release=self._show_task_list)
        self.task_list._close_btn.bind(on_release=self._hide_task_list)

        self.bottom_bar.settings_btn.bind(on_release=self._show_settings)
        self.bind(height=self._update_task_list_position)

    def _show_settings(self, *args):
        panel = SettingsPanel(root=self)
        panel.size_hint = (1, 1)
        panel.size = (self.width, self.height)
        panel.pos_hint = {'x': 0}
        panel.y = -self.height
        self.add_widget(panel)

        anim = Animation(y=0, duration=0.3, transition='out_cubic')
        anim.start(panel)

    def update_all_task_cards(self):
        self.task_list.refresh()
        self.content.refresh()

    def show_task_editor_new(self, *a):
        self.show_task_editor(None)

    def show_task_editor(self, task=None, task_id=None):
        panel = TaskEditorPanel(self, task, task_id)
        panel.pos_hint = {'x': 0}
        panel.y = -self.height
        self.add_widget(panel)

        anim = Animation(y=0, duration=0.3, transition='out_cubic')
        anim.start(panel)

    def hide_task_editor(self):
        if self._task_editor:
            self._task_editor.hide()
            def _clear(dt):
                self._task_editor = None
            Clock.schedule_once(_clear, 0.3)

    def _update_task_list_position(self, *args):
        if not hasattr(self, '_task_list_visible') or not self._task_list_visible:
            self.task_list.y = -self.height

    def _show_task_list(self, *args):
        self._task_list_visible = True
        anim = Animation(y=0, duration=0.3, transition='out_cubic')
        anim.start(self.task_list)

    def _hide_task_list(self, *args):
        self._task_list_visible = False
        anim = Animation(y=-self.height, duration=0.3, transition='in_cubic')
        anim.start(self.task_list)

    def _upd(self, *a):
        self._bg_rect.pos = self.pos
        self._bg_rect.size = self.size
        self._round.pos = self.pos
        self._round.size = self.size


class MainApp(MDApp):
    title = 'MAX Time Management'

    def build(self):
        self.root_layout = RootLayout()
        return self.root_layout

    def on_start(self):
        taskManager.initialize()
        taskManager.start_manager()
        self.refresh_tasks()

    def on_stop(self):
        taskManager.stop_manager()
        return True

    def refresh_tasks(self):
        self.root_layout.update_all_task_cards()

MainApp().run()