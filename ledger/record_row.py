# -*- coding: utf-8 -*-
"""明细里的一行记录。"""

from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.utils import get_color_from_hex

from db import fmt_money
from theme import F_BODY, F_TINY, col
from widgets import GlyphCircle, L, TapBox


class RecordRow(TapBox):
    def __init__(self, rec, on_tap=None, **kwargs):
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(56))
        super(RecordRow, self).__init__(
            on_tap=(lambda: on_tap(rec)) if on_tap else None, **kwargs)
        self.record = rec

        with self.canvas.before:
            self._hl = Color(0.31, 0.42, 0.93, 0)
            self._hl_rect = RoundedRectangle(radius=[dp(10)])
        self.bind(pos=self._sync, size=self._sync)

        row = BoxLayout(padding=[dp(2), dp(6), dp(2), dp(6)], spacing=dp(10))
        self.add_widget(row)

        circle = GlyphCircle(rec.get("cat_glyph") or "?", rec.get("cat_color") or "#A0AEC0",
                             d=dp(36), font_size=sp(13))
        row.add_widget(circle)

        mid = BoxLayout(orientation="vertical", spacing=dp(1))
        mid.add_widget(L(rec.get("cat_name") or "未分类", size=F_BODY, color="text",
                         shorten=True))
        note = rec.get("note") or ""
        mid.add_widget(L(note if note else rec["ts"][11:16], size=F_TINY,
                         color="text3", shorten=True))
        row.add_widget(mid)

        amt = rec.get("amount", 0)
        is_income = rec.get("type") == "income"
        txt = ("+" if is_income else "-") + fmt_money(amt)
        lbl = L(txt, size=F_BODY + sp(0.5),
                color="income" if is_income else "text", align="right")
        lbl.size_hint_x = None
        lbl.width = dp(104)
        row.add_widget(lbl)

    def _sync(self, *a):
        self._hl_rect.pos = self.pos
        self._hl_rect.size = self.size

    def on_press(self):
        self._hl.rgba = (0.31, 0.42, 0.93, 0.07)

    def on_release(self):
        self._hl.rgba = (0.31, 0.42, 0.93, 0)
