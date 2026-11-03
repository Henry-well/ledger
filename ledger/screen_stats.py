# -*- coding: utf-8 -*-
"""统计页：收支汇总、分类占比、近半年趋势。"""

from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex

from charts import BarChart, PieChart
from db import fmt_money, now_str, ym_add
from editor import ArrowButton
from theme import F_BODY, F_SMALL, F_TINY, F_TITLE, col
from widgets import Card, L, Space, TapBox


class ProgressRow(BoxLayout):
    def __init__(self, name, amount, pct, color, **kwargs):
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(44))
        super(ProgressRow, self).__init__(orientation="vertical", padding=[0, dp(4)], **kwargs)

        top = BoxLayout(size_hint_y=None, height=dp(18), spacing=dp(6))
        dot = Widget(size_hint=(None, 1), width=dp(3))
        with dot.canvas:
            dot._c = Color(*get_color_from_hex(color))
            dot._r = RoundedRectangle(radius=[dp(2)])
        dot.bind(pos=lambda *_: setattr(dot._r, "pos", dot.pos),
                 size=lambda *_: setattr(dot._r, "size", dot.size))
        top.add_widget(dot)
        top.add_widget(L(name, size=F_TINY + sp(1), color="text", shorten=True))
        top.add_widget(L("%d%%" % round(pct * 100), size=F_TINY, color="text3",
                         align="right", size_hint_x=None, width=dp(40)))
        top.add_widget(L(fmt_money(amount), size=F_TINY + sp(1), color="text",
                         align="right", size_hint_x=None, width=dp(76)))
        self.add_widget(top)

        bar = Widget(size_hint_y=None, height=dp(5))
        with bar.canvas:
            bar._bg = Color(0.945, 0.957, 0.973, 1)
            bar._bgr = RoundedRectangle(radius=[dp(3)])
            bar._fg = Color(*get_color_from_hex(color))
            bar._fgr = RoundedRectangle(radius=[dp(3)])
        self._bar = bar
        self._pct = max(0.02, min(1.0, pct))

        def sync(*_):
            bar._bgr.pos = bar.pos
            bar._bgr.size = bar.size
            bar._fgr.pos = bar.pos
            bar._fgr.size = (bar.width * self._pct, bar.height)
        bar.bind(pos=sync, size=sync)
        self.add_widget(bar)
        self.add_widget(Widget(size_hint_y=None, height=dp(4)))


class StatsScreen(Screen):
    def __init__(self, db, **kwargs):
        super(StatsScreen, self).__init__(**kwargs)
        self.db = db
        self.ym = now_str()[:7]
        self.mode = "expense"

        root = BoxLayout(orientation="vertical")
        self.add_widget(root)
        sv = ScrollView(do_scroll_x=False, bar_width=dp(2))
        body = BoxLayout(orientation="vertical", size_hint_y=None,
                         padding=[dp(16), dp(8), dp(16), dp(90)], spacing=dp(12))
        body.bind(minimum_height=body.setter("height"))
        sv.add_widget(body)
        root.add_widget(sv)
        self.body = body

        # 月份切换
        bar = BoxLayout(size_hint_y=None, height=dp(44))
        left = TapBox(size_hint=(None, 1), width=dp(40), on_tap=lambda: self._shift(-1))
        left.add_widget(L("‹", size=sp(22), color="text2", align="center"))
        bar.add_widget(left)
        self.month_lbl = L("", size=F_BODY, color="text", align="center")
        bar.add_widget(self.month_lbl)
        right = TapBox(size_hint=(None, 1), width=dp(40), on_tap=lambda: self._shift(1))
        right.add_widget(L("›", size=sp(22), color="text2", align="center"))
        bar.add_widget(right)
        body.add_widget(bar)

        # 汇总三格
        summary = Card(size_hint_y=None, height=dp(78), shadow=0.04,
                       padding=[dp(8), dp(10)])
        srow = BoxLayout(spacing=dp(4))
        self.s_inc = self._stat_cell(srow, "收入", "income")
        self.s_exp = self._stat_cell(srow, "支出", "expense")
        self.s_bal = self._stat_cell(srow, "结余", "text")
        summary.add_widget(srow)
        body.add_widget(summary)

        # 分类占比
        self.pie_card = Card(size_hint_y=None, height=dp(430), shadow=0.04,
                             padding=[dp(16), dp(14), dp(16), dp(10)])
        self.pie_card.orientation = "vertical"
        head = BoxLayout(size_hint_y=None, height=dp(32))
        head.add_widget(L("分类占比", size=F_BODY, color="text"))
        head.add_widget(Widget())
        self.seg_exp = TapBox(size_hint=(None, 1), width=dp(46),
                              on_tap=lambda: self._set_mode("expense"))
        self.seg_exp.add_widget(L("支出", size=F_TINY + sp(1), color="primary", align="center"))
        self.seg_inc = TapBox(size_hint=(None, 1), width=dp(46),
                              on_tap=lambda: self._set_mode("income"))
        self.seg_inc.add_widget(L("收入", size=F_TINY + sp(1), color="text3", align="center"))
        head.add_widget(self.seg_exp)
        head.add_widget(self.seg_inc)
        self.pie_card.add_widget(head)

        pie_wrap = BoxLayout(size_hint_y=None, height=dp(150))
        self.pie = PieChart(size_hint=(None, 1), width=dp(150))
        pie_wrap.add_widget(Widget())
        pie_wrap.add_widget(self.pie)
        pie_wrap.add_widget(Widget())
        self.pie_card.add_widget(pie_wrap)
        self.pie_card.add_widget(Space(dp(6)))

        self.rank_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(1))
        self.pie_card.add_widget(self.rank_box)
        body.add_widget(self.pie_card)

        # 趋势
        trend_card = Card(size_hint_y=None, height=dp(190), shadow=0.04,
                          padding=[dp(16), dp(14), dp(14), dp(10)])
        trend_card.orientation = "vertical"
        t_head = BoxLayout(size_hint_y=None, height=dp(26))
        t_head.add_widget(L("近半年收支", size=F_BODY, color="text"))
        t_head.add_widget(Widget())
        legend = BoxLayout(size_hint=(None, 1), width=dp(96), spacing=dp(6))
        legend.add_widget(self._legend("支出", "#E8553F"))
        legend.add_widget(self._legend("收入", "#12B886"))
        t_head.add_widget(legend)
        trend_card.add_widget(t_head)
        self.bar = BarChart(size_hint_y=None, height=dp(126))
        trend_card.add_widget(self.bar)
        body.add_widget(trend_card)

    def _legend(self, text, color):
        box = BoxLayout(spacing=dp(4), size_hint_x=None, width=dp(44))
        dot = Widget(size_hint=(None, None), size=(dp(7), dp(7)))
        with dot.canvas:
            dot._c = Color(*get_color_from_hex(color))
            dot._r = RoundedRectangle(radius=[dp(4)], pos=dot.pos, size=dot.size)
        dot.bind(pos=lambda *_: setattr(dot._r, "pos", dot.pos))
        box.add_widget(dot)
        box.add_widget(L(text, size=F_TINY, color="text3"))
        return box

    def _stat_cell(self, parent, title, color):
        cell = BoxLayout(orientation="vertical", spacing=dp(2))
        cell.add_widget(L(title, size=F_TINY, color="text3", align="center"))
        v = L("0.00", size=F_BODY + sp(2), color=color, align="center")
        cell.add_widget(v)
        parent.add_widget(cell)
        return v

    def _shift(self, delta):
        self.ym = ym_add(self.ym, delta)
        self.refresh()

    def _set_mode(self, mode):
        self.mode = mode
        self.seg_exp.children[0].color = col("primary") if mode == "expense" else col("text3")
        self.seg_inc.children[0].color = col("primary") if mode == "income" else col("text3")
        self.refresh()

    def on_pre_enter(self, *args):
        self.refresh()

    def refresh(self):
        y, m = self.ym[:4], int(self.ym[5:7])
        self.month_lbl.text = "%s年%d月" % (y, m)
        inc, exp = self.db.summary(self.ym)
        self.s_inc.text = fmt_money(inc)
        self.s_exp.text = fmt_money(exp)
        self.s_bal.text = fmt_money(inc - exp)
        self.s_bal.color = col("income") if inc >= exp else col("expense")

        data = self.db.breakdown(self.ym, self.mode)
        total = sum(d["total"] for d in data)
        pie_data = [{"name": d["name"], "total": d["total"], "color": d["color"]} for d in data]
        self.pie.set_data(pie_data,
                          "总支出" if self.mode == "expense" else "总收入", total)

        self.rank_box.clear_widgets()
        if not data:
            self.rank_box.add_widget(L("本月还没有数据", size=F_SMALL, color="text3",
                                       align="center", size_hint_y=None, height=dp(60)))
            self.rank_box.height = dp(60)
        else:
            for d in data:
                pct = d["total"] / float(total) if total else 0
                self.rank_box.add_widget(ProgressRow(d["name"], d["total"], pct, d["color"]))
            self.rank_box.height = len(data) * dp(44)
        self.pie_card.height = dp(212) + max(dp(60), len(data) * dp(44))

        months = []
        cur = now_str()[:7]
        for i in range(5, -1, -1):
            months.append(ym_add(cur, -i))
        trend = self.db.trend(months)
        self.bar.set_data([("%d月" % int(ym[5:7]), i, e) for ym, i, e in trend])
