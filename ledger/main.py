# -*- coding: utf-8 -*-
"""
记账本 —— 纯离线、本地存储的安卓记账 App

运行（桌面调试）：  python main.py
打包（安卓）：      见 README.md
"""

import os
import sys

from kivy.app import App
from kivy.config import Config
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import NoTransition, ScreenManager
from kivy.uix.widget import Widget
from kivy.utils import platform

import theme
from db import Database
from editor import RecordEditor
from screen_home import HomeScreen
from screen_records import RecordsScreen
from screen_settings import SettingsScreen
from screen_stats import StatsScreen
from theme import NAV_H, col
from widgets import L, Toast, hexrgba


# ------------------------------------------------------------------- 底部导航
class NavItem(BoxLayout):
    def __init__(self, text, key, on_tap, **kwargs):
        from kivy.uix.behaviors import ButtonBehavior

        super(NavItem, self).__init__(**kwargs)
        self.key = key
        self._on_tap = on_tap
        self.active = False
        with self.canvas.after:
            self._c = Color(*col("primary"))
            self._bar = RoundedRectangle(radius=[dp(2)])
        self.bind(pos=self._sync, size=self._sync)
        self.label = Label(text=text, font_size=sp(12), color=col("text3"),
                           halign="center", valign="middle")
        self.add_widget(self.label)
        self._sync()

    def _sync(self, *a):
        w = dp(18)
        self._bar.size = (w, dp(2.5)) if self.active else (0, 0)
        self._bar.pos = (self.center_x - w / 2.0, self.top - dp(3))
        self._c.rgba = col("primary", 1 if self.active else 0)

    def set_active(self, flag):
        self.active = flag
        self.label.color = col("primary") if flag else col("text3")
        self._sync()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            return super(NavItem, self).on_touch_down(touch)
        return False

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos) and not touch.is_mouse_scrolling:
            self._on_tap(self.key)
            return True
        return super(NavItem, self).on_touch_up(touch)


class BottomNav(BoxLayout):
    def __init__(self, on_change, **kwargs):
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", NAV_H)
        super(BottomNav, self).__init__(**kwargs)
        self._on_change = on_change
        with self.canvas.before:
            self._bgc = Color(*col("card"))
            self._bgr = RoundedRectangle(radius=[dp(16), dp(16), 0, 0])
        self.bind(pos=self._sync, size=self._sync)
        self.items = {}
        for text, key in (("首页", "home"), ("明细", "records"),
                          ("统计", "stats"), ("我的", "me")):
            item = NavItem(text, key, self._click)
            self.items[key] = item
            self.add_widget(item)
        self.set_active("home")

    def _sync(self, *a):
        self._bgr.pos = self.pos
        self._bgr.size = self.size

    def _click(self, key):
        self.set_active(key)
        self._on_change(key)

    def set_active(self, key):
        for k, item in self.items.items():
            item.set_active(k == key)


# --------------------------------------------------------------------- 悬浮键
class FAB(Widget):
    def __init__(self, on_tap, **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", (dp(56), dp(56)))
        super(FAB, self).__init__(**kwargs)
        self._on_tap = on_tap
        with self.canvas.before:
            self._sc = Color(0.31, 0.42, 0.93, 0.22)
            self._se = Ellipse(pos=(self.x, self.y - dp(3)), size=(dp(58), dp(58)))
            self._c = Color(*col("primary"))
            self._e = Ellipse(pos=self.pos, size=self.size)
        self.label = Label(text="+", font_size=dp(30), color=(1, 1, 1, 1),
                           halign="center", valign="middle", bold=True)
        self.add_widget(self.label)
        self.bind(pos=self._sync, size=self._sync)
        self._sync()

    def _sync(self, *a):
        self._e.pos = self.pos
        self._e.size = self.size
        self._se.pos = (self.x, self.y - dp(4))
        self._se.size = self.size
        self.label.pos = self.pos
        self.label.size = self.size

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._c.rgba = (0.27, 0.36, 0.80, 1)
            self._on_tap()
            return True
        return False

    def on_touch_up(self, touch):
        self._c.rgba = col("primary")
        return False


# -------------------------------------------------------------------- 根布局
class Root(FloatLayout):
    def __init__(self, db, **kwargs):
        super(Root, self).__init__(**kwargs)
        self.db = db
        with self.canvas.before:
            self._bgc = Color(*col("bg"))
            self._bgr = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._sync_bg, size=self._sync_bg)

        wrap = BoxLayout(orientation="vertical")
        self.add_widget(wrap)

        self.sm = ScreenManager(transition=NoTransition())
        self.home = HomeScreen(db, on_goto=self.switch, on_edit=self.open_editor)
        self.records = RecordsScreen(db, on_edit=self.open_editor)
        self.stats = StatsScreen(db)
        self.me = SettingsScreen(db)
        for s, name in ((self.home, "home"), (self.records, "records"),
                        (self.stats, "stats"), (self.me, "me")):
            s.name = name
            self.sm.add_widget(s)
        wrap.add_widget(self.sm)

        self.nav = BottomNav(on_change=self._on_nav)
        wrap.add_widget(self.nav)

        self.fab = FAB(on_tap=self.open_editor)
        self.add_widget(self.fab)

        self._toast = None
        self.bind(size=self._place, pos=self._place)
        self._place()

    def _sync_bg(self, *a):
        self._bgr.pos = self.pos
        self._bgr.size = self.size

    def _place(self, *a):
        self.fab.pos = (self.width - self.fab.width - dp(18), NAV_H + dp(18))

    def _on_nav(self, key):
        self.sm.current = key

    def switch(self, key):
        self.nav.set_active(key)
        self.sm.current = key

    def open_editor(self, record=None):
        editor = RecordEditor(self.db, on_saved=lambda _r: self.refresh_all(),
                              record=record)
        editor.open()

    def refresh_all(self):
        for s in (self.home, self.records, self.stats, self.me):
            try:
                s.refresh()
            except Exception as e:  # pragma: no cover
                print("[refresh]", e)

    def show_toast(self, text, duration=1.8):
        if self._toast is not None:
            try:
                self.remove_widget(self._toast)
            except Exception:
                pass
            self._toast = None
        t = Toast(text)
        t.pos = (self.width / 2.0 - t.width / 2.0, NAV_H + dp(90))
        self.add_widget(t)
        self._toast = t
        from kivy.animation import Animation
        Animation(opacity=1, d=0.15).start(t)
        from kivy.clock import Clock

        def fade(*_):
            Animation(opacity=0, d=0.3).start(t)
        Clock.schedule_once(fade, duration)

        def kill(*_):
            if self._toast is t:
                try:
                    self.remove_widget(t)
                except Exception:
                    pass
                self._toast = None
        Clock.schedule_once(kill, duration + 0.45)


# ------------------------------------------------------------------------ App
class LedgerApp(App):
    title = "记账本"

    def build(self):
        theme.setup_fonts()
        Window.clearcolor = col("bg")
        Window.softinput_mode = "below_target"
        if platform not in ("android", "ios"):
            Window.size = (390, 800)

        db_path = os.environ.get("LEDGER_DB") or os.path.join(self.user_data_dir, "ledger.db")
        self.db = Database(db_path)
        self._ask_permissions()
        self._bind_back_key()
        return Root(self.db)

    def _ask_permissions(self):
        if platform != "android":
            return
        try:
            from android.permissions import Permission, request_permissions
            request_permissions([Permission.WRITE_EXTERNAL_STORAGE,
                                 Permission.READ_EXTERNAL_STORAGE])
        except Exception:
            pass

    def _bind_back_key(self):
        Window.bind(on_keyboard=self._on_key)

    def _on_key(self, window, key, *args):
        # 安卓返回键：先关弹窗，再回到首页，最后退出
        if key != 27:
            return False
        root = self.root
        modals = [c for c in root.children if hasattr(c, "dismiss")]
        for m in modals:
            try:
                m.dismiss()
                return True
            except Exception:
                pass
        if root.sm.current != "home":
            root.switch("home")
            return True
        return False

    def on_stop(self):
        try:
            self.db.close()
        except Exception:
            pass


if __name__ == "__main__":
    LedgerApp().run()
