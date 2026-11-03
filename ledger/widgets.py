# -*- coding: utf-8 -*-
"""通用 UI 组件：圆角卡片、按钮、圆形图标、提示条、确认/输入弹窗。"""

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex

from theme import (F_BODY, F_SMALL, F_TINY, F_TITLE, PAD, RADIUS, col)


def hexrgba(h, a=1.0):
    if isinstance(h, str) and not h.startswith("#"):
        return col(h, a)  # 主题色名，如 "primary"
    r, g, b, _ = get_color_from_hex(h)
    return (r, g, b, a)


# --------------------------------------------------------------------- 文本
def L(text="", size=F_BODY, color="text", bold=False, align="left",
      valign="middle", shorten=False, **kw):
    lbl = Label(text=text, font_size=size,
                color=col(color) if isinstance(color, str) else color,
                bold=bold, halign=align, valign=valign, shorten=shorten,
                shorten_from="right", **kw)
    lbl.bind(size=lambda *_: setattr(lbl, "text_size", (lbl.width, lbl.height)))
    Clock.schedule_once(lambda *_: setattr(lbl, "text_size", (lbl.width, lbl.height)), 0)
    return lbl


# --------------------------------------------------------------------- 卡片
class Card(BoxLayout):
    """白底圆角卡片，可带轻微投影。"""

    def __init__(self, bg=None, radius=None, shadow=0.05, **kwargs):
        self._bg_color = hexrgba(bg) if isinstance(bg, str) else (bg or col("card"))
        self._radius_val = radius if radius is not None else [RADIUS]
        self._shadow_alpha = shadow
        kwargs.setdefault("padding", [0, 0])
        super(Card, self).__init__(**kwargs)
        r = [dp(x) for x in self._radius_val]
        with self.canvas.before:
            self._sh_color = Color(0, 0, 0, 0)
            self._sh_rect = RoundedRectangle(radius=r)
            self._bg_color_instr = Color(*self._bg_color)
            self._rect = RoundedRectangle(radius=r)
        self.bind(pos=self._sync, size=self._sync)
        self._sync()

    def _sync(self, *a):
        self._rect.pos = self.pos
        self._rect.size = self.size
        if self._shadow_alpha:
            self._sh_color.rgba = (0.06, 0.09, 0.16, self._shadow_alpha)
            self._sh_rect.pos = (self.x + dp(1), self.y - dp(2.5))
            self._sh_rect.size = (self.width - dp(2), self.height + dp(1))
        else:
            self._sh_color.rgba = (0, 0, 0, 0)
            self._sh_rect.size = self.size
            self._sh_rect.pos = self.pos

    def set_bg(self, bg, alpha=1.0):
        self._bg_color = hexrgba(bg, alpha) if isinstance(bg, str) else bg
        self._bg_color_instr.rgba = self._bg_color


# --------------------------------------------------------------------- 按钮
class FlatButton(ButtonBehavior, BoxLayout):
    """自绘圆角按钮，按下时轻微变色。"""

    def __init__(self, text="", bg="primary", fg="white", font_size=F_BODY,
                 radius=None, on_tap=None, bold=False, **kwargs):
        if "size_hint" not in kwargs and "size_hint_y" not in kwargs:
            kwargs.setdefault("size_hint_y", None)
        super(FlatButton, self).__init__(**kwargs)
        self._radius = [dp(x) for x in (radius if radius is not None else [dp(12)])]
        self._bg = hexrgba(bg) if isinstance(bg, str) else bg
        with self.canvas.before:
            self._color = Color(*self._bg)
            self._rect = RoundedRectangle(radius=self._radius)
        self.bind(pos=self._sync, size=self._sync)
        self.label = L(text, size=font_size, color=fg, bold=bold, align="center")
        self.add_widget(self.label)
        self._on_tap = on_tap
        if on_tap:
            self.bind(on_release=lambda *_: on_tap())
        self._sync()

    def _sync(self, *a):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def on_state(self, *a):
        if self.state == "down":
            self._color.rgba = (self._bg[0] * 0.86, self._bg[1] * 0.86, self._bg[2] * 0.86, self._bg[3])
        else:
            self._color.rgba = self._bg

    def on_press(self):
        self.on_state()

    def on_release(self):
        self.on_state()

    def set_text(self, t):
        self.label.text = t

    def set_bg(self, bg):
        self._bg = hexrgba(bg) if isinstance(bg, str) else bg
        self._color.rgba = self._bg


class TapBox(ButtonBehavior, BoxLayout):
    """可点击容器（透明背景）。"""

    def __init__(self, on_tap=None, **kwargs):
        super(TapBox, self).__init__(**kwargs)
        if on_tap:
            self.bind(on_release=lambda *_: on_tap())


# ------------------------------------------------------------------ 圆形图标
class GlyphCircle(Widget):
    """圆形底色 + 中间一个汉字，用作分类图标。"""

    def __init__(self, text="", color_hex="#A0AEC0", d=dp(40), font_size=None, **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", (d, d))
        super(GlyphCircle, self).__init__(**kwargs)
        with self.canvas.before:
            self._c = Color(*hexrgba(color_hex))
            self._e = Ellipse(pos=self.pos, size=self.size)
        self.bind(pos=self._sync, size=self._sync)
        self._label = Label(text=text, font_size=font_size or (self.height * 0.42),
                            color=(1, 1, 1, 1), bold=True)
        self.add_widget(self._label)
        self._label.pos = self.pos
        self._label.size = self.size
        self.bind(pos=self._sync_label, size=self._sync_label)

    def _sync(self, *a):
        self._e.pos = self.pos
        self._e.size = self.size

    def _sync_label(self, *a):
        self._label.pos = self.pos
        self._label.size = self.size

    def set_color(self, color_hex, alpha=1.0):
        self._c.rgba = hexrgba(color_hex, alpha)


# ------------------------------------------------------------------ 分隔线
class Divider(Widget):
    def __init__(self, color="#EDF0F5", thickness=1, **kwargs):
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(thickness))
        super(Divider, self).__init__(**kwargs)
        with self.canvas.before:
            self._c = Color(*hexrgba(color))
            self._r = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *a):
        self._r.pos = self.pos
        self._r.size = self.size


class Space(Widget):
    def __init__(self, h=dp(8), **kwargs):
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", h)
        super(Space, self).__init__(**kwargs)


# -------------------------------------------------------------------- 提示条
class Toast(BoxLayout):
    def __init__(self, text, **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("height", dp(40))
        super(Toast, self).__init__(**kwargs)
        self.opacity = 0
        with self.canvas.before:
            self._c = Color(0.10, 0.13, 0.20, 0.92)
            self._r = RoundedRectangle(radius=[dp(20)])
        self.bind(pos=self._sync, size=self._sync)
        lbl = L(text, size=F_SMALL, color=(1, 1, 1, 1), align="center")
        self.add_widget(lbl)
        self._label = lbl
        self.bind(width=self._resize)
        self._resize()

    def _resize(self, *a):
        self._label.texture_update()
        self.width = min(max(self._label.texture_size[0] + dp(36), dp(120)),
                         Window.width - dp(48))

    def _sync(self, *a):
        self._r.pos = self.pos
        self._r.size = self.size


# ------------------------------------------------------------------ 弹窗外壳
class DimModal(ModalView):
    """带半透明遮罩的弹窗基类。"""

    def __init__(self, **kwargs):
        kwargs.setdefault("size_hint", (1, 1))
        kwargs.setdefault("background", "")
        kwargs.setdefault("background_color", (0, 0, 0, 0))
        super(DimModal, self).__init__(**kwargs)
        with self.canvas.before:
            self._dim = Color(0.06, 0.09, 0.16, 0.45)
            self._dim_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._sync_dim, size=self._sync_dim)

    def _sync_dim(self, *a):
        self._dim_rect.pos = self.pos
        self._dim_rect.size = self.size


# ------------------------------------------------------------------ 确认弹窗
class ConfirmDialog(DimModal):
    def __init__(self, title, message="", on_ok=None, ok_text="确定",
                 cancel_text="取消", danger=False, **kwargs):
        super(ConfirmDialog, self).__init__(**kwargs)
        box = Card(size_hint=(0.86, None), height=dp(178),
                   padding=[dp(18), dp(18), dp(18), dp(14)])
        box.orientation = "vertical"
        box.add_widget(L(title, size=F_TITLE, color="text"))
        box.add_widget(Space(dp(8)))
        msg = L(message, size=F_SMALL, color="text2", align="left")
        msg.text_size = (Window.width * 0.86 - dp(36), None)
        msg.valign = "top"
        box.add_widget(msg)
        box.add_widget(Widget())
        row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        row.add_widget(FlatButton(cancel_text, bg="#F1F3F7", fg="text2",
                                  height=dp(44), on_tap=self.dismiss))
        row.add_widget(FlatButton(ok_text, bg="expense" if danger else "primary",
                                  height=dp(44), on_tap=lambda: self._ok(on_ok)))
        box.add_widget(row)
        self.add_widget(box)

    def _ok(self, cb):
        self.dismiss()
        if cb:
            Clock.schedule_once(lambda *_: cb(), 0.12)


# ------------------------------------------------------------------ 输入弹窗
class InputDialog(DimModal):
    def __init__(self, title, value="", hint="", numeric=False, on_ok=None,
                 ok_text="确定", max_len=None, **kwargs):
        super(InputDialog, self).__init__(**kwargs)
        box = Card(size_hint=(0.88, None), height=dp(196),
                   padding=[dp(18), dp(16), dp(18), dp(14)])
        box.orientation = "vertical"
        box.add_widget(L(title, size=F_TITLE, color="text"))
        box.add_widget(Space(dp(12)))
        self.ti = TextInput(text=str(value), hint_text=hint, multiline=False,
                            input_type="number" if numeric else "text",
                            font_size=F_BODY + sp(1),
                            background_normal="", background_active="",
                            background_color=(0.955, 0.965, 0.982, 1),
                            foreground_color=col("text"),
                            cursor_color=col("primary"),
                            hint_text_color=col("text3"),
                            padding=[dp(12), dp(12), dp(12), dp(12)])
        if max_len:
            self.ti.max_length = max_len
        wrap = Card(bg="#F4F6FA", radius=[dp(10)], shadow=0,
                    size_hint_y=None, height=dp(46), padding=[dp(2), 0, dp(2), 0])
        wrap.add_widget(self.ti)
        box.add_widget(wrap)
        box.add_widget(Widget())
        row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        row.add_widget(FlatButton("取消", bg="#F1F3F7", fg="text2",
                                  height=dp(44), on_tap=self.dismiss))
        row.add_widget(FlatButton(ok_text, bg="primary", height=dp(44),
                                  on_tap=lambda: self._ok(on_ok)))
        box.add_widget(row)
        self.add_widget(box)
        self.bind(on_open=lambda *_: setattr(self.ti, "focus", not numeric))

    def _ok(self, cb):
        v = self.ti.text.strip()
        self.dismiss()
        if cb:
            Clock.schedule_once(lambda *_: cb(v), 0.12)


# ------------------------------------------------------------------ 全局提示
def toast(text, duration=1.8):
    app = App.get_running_app()
    root = getattr(app, "root", None)
    if root is not None and hasattr(root, "show_toast"):
        root.show_toast(text, duration)
    else:  # 兜底
        print("[toast]", text)
