# -*- coding: utf-8 -*-
"""纯 Canvas 绘制的图表，不依赖任何第三方绘图库，保证打包体积和离线可用。

注意：此处刻意不使用 kivy.graphics.Mesh —— 部分设备/驱动上无索引的裸 Mesh
不可见；改用 Line(ellipse=...) 粗弧线绘制环形图，兼容性更好。
"""

import math

from kivy.uix.anchorlayout import AnchorLayout
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex

from theme import F_TINY, col
from db import fmt_money


def _rgba(h, a=1.0):
    if isinstance(h, (tuple, list)):
        return tuple(h)
    r, g, b, _ = get_color_from_hex(h)
    return (r, g, b, a)


class _PieCanvas(Widget):
    """只负责画环形图，与文字分层，避免 canvas 指令影响子控件渲染。"""
    pass


class PieChart(AnchorLayout):
    """环形占比图，中心显示总额。"""

    def __init__(self, data=None, center_title="总支出", center_value=0, **kwargs):
        kwargs.setdefault("anchor_x", "center")
        kwargs.setdefault("anchor_y", "center")
        super(PieChart, self).__init__(**kwargs)
        self.data = data or []
        self.center_title = center_title
        self.center_value = center_value
        self._chart = _PieCanvas(size_hint=(1, 1))
        self.add_widget(self._chart)
        mid = BoxLayout(orientation="vertical", size_hint=(None, None),
                        size=(dp(140), dp(54)))
        mid.add_widget(Widget(size_hint_y=None, height=dp(4)))
        self._value_label = Label(font_size=dp(15), color=col("text"),
                                  halign="center", valign="middle",
                                  size_hint_y=None, height=dp(24))
        self._title_label = Label(font_size=dp(10), color=col("text3"),
                                  halign="center", valign="middle",
                                  size_hint_y=None, height=dp(16))
        mid.add_widget(self._value_label)
        mid.add_widget(self._title_label)
        self._mid = mid
        self.add_widget(mid)
        self.bind(pos=self._layout, size=self._layout)
        self._chart.bind(pos=self._layout, size=self._layout)

    def set_data(self, data, center_title=None, center_value=None):
        self.data = data or []
        if center_title is not None:
            self.center_title = center_title
        if center_value is not None:
            self.center_value = center_value
        self._layout()

    def _layout(self, *a):
        if self.width <= 0 or self._chart.width <= 0:
            return
        self._value_label.text = fmt_money(self.center_value)
        self._value_label.text_size = (dp(140), dp(24))
        self._title_label.text = self.center_title
        self._title_label.text_size = (dp(140), dp(16))
        self._redraw()

    def _redraw(self):
        c = self._chart
        c.canvas.clear()
        d = min(c.width, c.height)
        cx, cy = c.center_x, c.center_y
        r_out = d / 2.0
        r_in = r_out * 0.62
        thick = r_out - r_in
        r_mid = (r_out + r_in) / 2.0
        total = sum(max(0, item.get("total", 0)) for item in self.data)
        with c.canvas:
            Color(*_rgba("#EEF1F6"))
            Ellipse(pos=(cx - r_out, cy - r_out), size=(r_out * 2, r_out * 2))
            if total <= 0:
                return
            angle = 90.0  # 从顶部开始，顺时针
            for item in self.data:
                val = max(0, item.get("total", 0))
                if val <= 0:
                    continue
                sweep = 360.0 * val / total
                a, b = angle, angle - sweep  # 区间 [b, a]
                gap = 1.5 if sweep > 5 else 0
                Color(*_rgba(item.get("color", "#A0AEC0")))
                Line(ellipse=(cx - r_mid, cy - r_mid, r_mid * 2, r_mid * 2,
                              b + gap, a - gap),
                     width=thick, cap="none")
                angle = b


class BarChart(BoxLayout):
    """近 N 个月收支柱状图（支出为主色，收入为次色）。"""

    def __init__(self, data=None, **kwargs):
        kwargs.setdefault("orientation", "vertical")
        kwargs.setdefault("spacing", dp(2))
        super(BarChart, self).__init__(**kwargs)
        self.data = data or []
        self.plot = Widget(size_hint_y=1)
        self.label_row = BoxLayout(size_hint_y=None, height=dp(16))
        self.add_widget(self.plot)
        self.add_widget(self.label_row)
        self._labels = []
        self.plot.bind(pos=self._redraw, size=self._redraw)

    def set_data(self, data):
        self.data = data or []
        self._sync_labels()
        self._redraw()

    def _sync_labels(self):
        need = len(self.data)
        while len(self._labels) < need:
            lb = Label(font_size=dp(10), color=col("text3"),
                       halign="center", valign="middle")
            self._labels.append(lb)
            self.label_row.add_widget(lb)
        for i, lb in enumerate(self._labels):
            if i < need:
                lb.text = self.data[i][0]
                lb.opacity = 1
            else:
                lb.opacity = 0

    def _redraw(self, *a):
        self.plot.canvas.clear()
        w, h = self.plot.width, self.plot.height
        if not self.data or w <= 0 or h <= 0:
            return
        pad_l, pad_r = dp(4), dp(4)
        n = len(self.data)
        slot = (w - pad_l - pad_r) / float(n)
        bar_w = min(dp(13), slot * 0.3)
        vmax = max([max(i, e) for _, i, e in self.data] + [1])
        with self.plot.canvas:
            Color(*_rgba("#EFF2F7"))
            for k in range(1, 4):
                gy = self.plot.y + h * k / 4.0
                Line(points=[self.plot.x + pad_l, gy, self.plot.right - pad_r, gy],
                     width=dp(0.6))
            for idx, (label, inc, exp) in enumerate(self.data):
                cx = self.plot.x + pad_l + slot * (idx + 0.5)
                for j, (val, cstr) in enumerate(((exp, "#E8553F"), (inc, "#12B886"))):
                    if val <= 0:
                        continue
                    bh = max(dp(2), h * val / float(vmax))
                    bx = cx - bar_w - dp(1.5) + j * (bar_w + dp(3))
                    Color(*_rgba(cstr, 0.9 if j == 0 else 0.75))
                    RoundedRectangle(pos=(bx, self.plot.y), size=(bar_w, bh),
                                     radius=[dp(3), dp(3), 0, 0])


class MiniBars(Widget):
    """小型支出强度条，用于展示当月每日支出。"""

    def __init__(self, values=None, **kwargs):
        super(MiniBars, self).__init__(**kwargs)
        self.values = values or []
        self.bind(pos=self._redraw, size=self._redraw)

    def set_values(self, values):
        self.values = values or []
        self._redraw()

    def _redraw(self, *a):
        self.canvas.clear()
        if not self.values or self.width <= 0:
            return
        n = len(self.values)
        slot = self.width / float(n)
        bar_w = max(dp(1.5), slot - dp(1))
        vmax = max(self.values + [1])
        with self.canvas:
            for i, v in enumerate(self.values):
                h = max(dp(1.5), (self.height - dp(2)) * v / float(vmax))
                Color(*_rgba("#4F6BED", 0.25 + 0.6 * (v / float(vmax))))
                RoundedRectangle(pos=(self.x + i * slot, self.y),
                                 size=(bar_w, h), radius=[dp(1)])
