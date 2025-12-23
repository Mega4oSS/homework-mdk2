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
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Rectangle, Line
from kivy.graphics.texture import Texture
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.animation import Animation


Window.clearcolor = (1, 0, 1, 1)

class RoundedBtn(Button):
    def __init__(self, bg=(0.2, 0.5, 0.9, 1), radius=dp(16), **kw):
        super().__init__(**kw)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0, 0, 0, 0)
        self.color = (1, 1, 1, 1)
        self._bg = bg
        self._radius = [radius] if not isinstance(radius, (list, tuple)) else radius
        with self.canvas.before:
            self._col = Color(*self._bg)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=self._radius)
        self.bind(pos=self._u, size=self._u)

    def _u(self, *a):
        self._rect.pos = self.pos
        self._rect.size = self.size

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

        self.project_btn = RoundedBtn(
            text='MAX Core ▼',
            bg=(0.16, 0.36, 0.78, 1),
            size_hint_x=None,
            radius=[dp(0), dp(0), dp(0), dp(16)],
            width=dp(120),
            font_size='13sp'
        )

        self.add_widget(left_box)
        self.add_widget(self.project_btn)

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
        self.settings_btn = RoundedBtn(text='⚙', bg=(0.66, 0.66, 0.66, 1), radius=12, size_hint_x=None, width=dp(52), font_size='20sp')

        self.add_widget(self.list_btn)
        self.add_widget(self.settings_btn)

    def _up(self, *a):
        self._bg.pos = self.pos
        self._bg.size = self.size


class TaskCard(BoxLayout):
    def __init__(self, title, project, description, start_time, end_time, started=False):
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

        self._state = 'active' if self._started else 'next'
        self._completed_time = None

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
                                 font_size='20sp')
        def _on_finish(instance):
            from datetime import datetime
            now = datetime.now().strftime('%Y-%m-%d %H:%M')
            self.mark_completed(now)
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
        if self._state == 'active':
            self._time.text = f'До конца {self._end_time}'
        elif self._state == 'next':
            self._time.text = f'До начала {self._start_time}'
        elif self._state == 'completed':
            if self._completed_time:
                self._time.text = f'Завершено {self._completed_time}'
            else:
                self._time.text = f'Завершено {self._end_time}'

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

        self.scroll = ScrollView(
            size_hint=(1, 1),
            bar_width=dp(4),
            do_scroll_x=False
        )

        self.container = BoxLayout(
            orientation='vertical',
            size_hint_x=1,
            size_hint_y=None,
            spacing=dp(24),
            padding=[dp(20), dp(18), dp(20), dp(18)]
        )
        self.container.bind(minimum_height=self.container.setter('height'))

        self.prev_card = TaskCard(
            title='Составить диз доки',
            project='MAX Core',
            description=('Достаточно дллнное описание диз доков для тестов '
                         'Карточка корректно растягивается по высоте и сохраняет аккуратные отступы.'),
            start_time='2ч 15м',
            end_time='3ч 40м',
            started=False
        )
        self.prev_card.size_hint_y = None
        self.prev_card.mark_completed('Сегодня 11:20')

        self.card = TaskCard(
            title='Сверстать главный экран',
            project='MAX Core',
            description=('Очень длинное описание задачи, которое может быть сколько угодно большим. '
                         'Карточка корректно растягивается по высоте и сохраняет аккуратные отступы.'),
            start_time='2ч 15м',
            end_time='3ч 40м',
            started=False
        )
        self.card.size_hint_y = None
        self.card.mark_active()

        self.next_card = TaskCard(
            title='Подключить аналитику',
            project='MAX Core',
            description='Подключение событий и проверка корректности отправки данных.',
            start_time='1ч 10м',
            end_time='1ч 10м',
            started=True
        )
        self.next_card.size_hint_y = None
        self.next_card.mark_next()

        for c in (self.prev_card, self.card, self.next_card):
            c.bind(height=lambda *a: setattr(self.container, 'height', self.container.minimum_height))
            self.container.add_widget(c)

        self.scroll.add_widget(self.container)
        self.add_widget(self.scroll)

    def _up(self, *a):
        self._bg.pos = self.pos
        self._bg.size = self.size


class STaskCard(FloatLayout):
    def __init__(self, title, project, description, start_time, end_time, started=False, overdue_time=None):
        super().__init__(size_hint_y=None)
        self._radius = [18]
        self._compact_h = dp(56)
        self._title = title
        self._project = project
        self._description = description
        self._start_time = start_time
        self._end_time = end_time
        self._started = started
        self._overdue_time = overdue_time

        self._state = 'active' if self._started else 'next'
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
                              size_hint_x=None, width=dp(80))
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
                                   size=(dp(80), self._compact_h), font_size='24sp', pos=(0, 0))
        self.edit_btn.opacity = 0

        self.delete_btn = RoundedBtn(text='🗑', bg=(0.9, 0.3, 0.3, 1), radius=[0, 12, 12, 0], size_hint=(None, None),
                                     size=(dp(80), self._compact_h), font_size='24sp', pos=(0, 0))
        self.delete_btn.opacity = 0

        self.add_widget(self.edit_btn)
        self.add_widget(self.delete_btn)
        self.add_widget(self.main_container)

        self._swipe_gap = dp(14)
        self._swipe_full = dp(80) - self._swipe_gap
        Clock.schedule_once(self._post, 0)
        self.bind(size=self._layout, pos=self._layout)

    def _post(self, dt):
        self._update_state_visuals()
        self._layout()

    def _set_time_text(self):
        if self._state == 'active':
            self.time_lbl.text = self._end_time
        elif self._state == 'next':
            self.time_lbl.text = self._start_time
        elif self._state == 'completed':
            if self._completed_time:
                self.time_lbl.text = self._completed_time
            else:
                self.time_lbl.text = self._end_time
        elif self._state == 'completed_overdue':
            text = self._completed_time if self._completed_time else self._end_time
            if self._overdue_time:
                text += f'\n+{self._overdue_time}'
            self.time_lbl.text = text

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
            self.compact_view._col.rgba = (0.6, 0.6, 0.4, 1)

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

            if not self._is_swiping and abs(dx) > dp(10):
                if abs(dx) > abs(dy) * 1.5:
                    self._is_swiping = True

            if self._is_swiping:
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
        # Сброс флага свайпа: дальше клики будут обычными
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
    """Добавляет контур для отладки к виджету"""
    with widget.canvas.after:  # Используем canvas.after чтобы контур был поверх
        widget.debug_color = Color(*border_color)
        # Создаем контур (линию) вместо закрашенного прямоугольника
        widget.debug_rect = Line(
            rectangle=(widget.x, widget.y, widget.width, widget.height),
            width=line_width
        )

    def update_debug_rect(instance, value):
        # Обновляем координаты контура при изменении позиции или размера
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

        # Временная заглушка
        header = BoxLayout(
            size_hint_y=None,
            height=dp(56),
        )

        headerKostyl = BoxLayout(
            size_hint_y=None,
            height=dp(56),
            padding=[dp(16), 0]
        )

        title = Label(
            text='[b]Список задач[/b]',
            markup=True,
            color=(0.2, 0.2, 0.2, 1),
            halign='left',
            valign='middle',
            font_size='18sp'
        )
        title.bind(size=title.setter('text_size'))

        close_btn = RoundedBtn(
            text='X',
            bg=(0.7, 0.7, 0.7, 1),
            radius=12,
            size_hint_x=None,
            font_size='20sp'
        )
        close_btn.bind(height=lambda instance, value: setattr(instance, 'width', value))
        headerKostyl.add_widget(title)
        header.add_widget(headerKostyl)
        header.add_widget(close_btn)


        self.add_widget(header)

        self._close_btn = close_btn

        self.scroll = ScrollView(
            size_hint=(1, 1),
            bar_width=dp(4),
            do_scroll_x=False
        )

        self.container = BoxLayout(
            orientation='vertical',
            size_hint_x=1,
            size_hint_y=None,
            spacing=dp(12),
            padding=[dp(20), dp(18), dp(20), dp(18)]
        )
        self.container.bind(minimum_height=self.container.setter('height'))

        card1 = STaskCard(
            title='Завершено с просрочкой',
            project='MAX Core',
            description='Пример карточки с просрочкой выполнения задачи.',
            start_time='2ч',
            end_time='3ч 40м',
            started=False,
            overdue_time='1ч 20м'
        )
        card1.mark_completed_overdue('12.12', '1ч 20м')

        card2 = STaskCard(
            title='Завершенная задача',
            project='MAX Core',
            description='Задача была успешно завершена в срок.',
            start_time='2ч 15м',
            end_time='3ч 40м',
            started=False
        )
        card2.mark_completed('11:20')

        card3 = STaskCard(
            title='Активная задача',
            project='MAX Core',
            description='Описание активной задачи, которая выполняется прямо сейчас.',
            start_time='2ч 15м',
            end_time='3ч 40м',
            started=True
        )
        card3.set_state('active')

        card4 = STaskCard(
            title='Следующая задача',
            project='MAX Core',
            description='Задача в очереди на выполнение.',
            start_time='1ч 10м',
            end_time='2ч 30м',
            started=False
        )
        card4.set_state('next')

        for c in (card1, card2, card3, card4):
            c.bind(height=lambda *a: setattr(self.container, 'height', self.container.minimum_height))
            self.container.add_widget(c)

        self.scroll.add_widget(self.container)
        self.add_widget(self.scroll)

    def _upd(self, *a):
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

        # Панель списка задач (скрыта)
        self.task_list = TaskListPanel()
        self.task_list.pos_hint = {'x': 0}
        self.task_list.y = -self.height  # Прячем за нижней границей
        self.add_widget(self.task_list)

        # Привязываем кнопки
        self.bottom_bar.list_btn.bind(on_release=self._show_task_list)
        self.task_list._close_btn.bind(on_release=self._hide_task_list)

        # Обновляем позицию панели при изменении размера окна
        self.bind(height=self._update_task_list_position)

    def _update_task_list_position(self, *args):
        # Если панель скрыта, обновляем её начальную позицию
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


class MainApp(App):
    def build(self):
        return RootLayout()


MainApp().run()
