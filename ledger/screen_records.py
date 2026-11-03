# -*- coding: utf-8 -*-
"""明细页：按月查看，按天分组。"""

import datetime

from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from db import fmt_money, now_str, ym_add
from editor import ArrowButton
from record_row import RecordRow
from theme import F_BODY, F_SMALL, F_TINY, F_TITLE, col
from widgets import Card, L, Space, TapBox, toast

WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


class RecordsScreen(Screen):
    def __init__(self, db, on_edit=None, **kwargs):
        super(RecordsScreen, self).__init__(**kwargs)
        self.db = db
        self.on_edit = on_edit
        self.ym = now_str()[:7]

        root = BoxLayout(orientation="vertical")
        self.add_widget(root)

        # 月份切换
        bar = BoxLayout(size_hint_y=None, height=dp(52), padding=[dp(8), dp(8), dp(8), dp(6)])
        left = TapBox(size_hint=(None, 1), width=dp(44),
                      on_tap=lambda: self._shift(-1))
        left.add_widget(L("‹", size=sp(22), color="text2", align="center"))
        bar.add_widget(left)
        mid = BoxLayout(orientation="vertical")
        self.month_lbl = L("", size=F_BODY, color="text", align="center")
        self.sum_lbl = L("", size=F_TINY, color="text3", align="center")
        mid.add_widget(self.month_lbl)
        mid.add_widget(self.sum_lbl)
        bar.add_widget(mid)
        right = TapBox(size_hint=(None, 1), width=dp(44),
                       on_tap=lambda: self._shift(1))
        right.add_widget(L("›", size=sp(22), color="text2", align="center"))
        bar.add_widget(right)
        root.add_widget(bar)

        sv = ScrollView(do_scroll_x=False, bar_width=dp(2))
        self.list_box = BoxLayout(orientation="vertical", size_hint_y=None,
                                  padding=[dp(16), dp(2), dp(16), dp(90)], spacing=dp(10))
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        sv.add_widget(self.list_box)
        root.add_widget(sv)
        self.sv = sv

    def _shift(self, delta):
        self.ym = ym_add(self.ym, delta)
        self.refresh()
        self.sv.scroll_y = 1

    def on_pre_enter(self, *args):
        self.refresh()

    def refresh(self):
        y, m = self.ym[:4], int(self.ym[5:7])
        self.month_lbl.text = "%s年%d月" % (y, m)
        inc, exp = self.db.summary(self.ym)
        self.sum_lbl.text = "支出 ¥%s   收入 ¥%s" % (fmt_money(exp), fmt_money(inc))

        self.list_box.clear_widgets()
        rows = self.db.records(ym=self.ym)
        if not rows:
            box = Card(size_hint_y=None, height=dp(140), shadow=0.03)
            box.orientation = "vertical"
            box.add_widget(Widget())
            box.add_widget(L("这个月还没有记录", size=F_SMALL, color="text3", align="center"))
            box.add_widget(Widget())
            self.list_box.add_widget(box)
            return

        # 按日期分组
        groups = []
        for r in rows:
            d = r["ts"][:10]
            if not groups or groups[-1][0] != d:
                groups.append((d, []))
            groups[-1][1].append(r)

        for day, items in groups:
            exp_sum = sum(i["amount"] for i in items if i["type"] == "expense")
            inc_sum = sum(i["amount"] for i in items if i["type"] == "income")

            head = BoxLayout(size_hint_y=None, height=dp(26), padding=[dp(2), 0, dp(2), 0])
            dt = datetime.date(int(day[:4]), int(day[5:7]), int(day[8:10]))
            label = "%d月%d日 · %s" % (dt.month, dt.day, WEEKDAYS[dt.weekday()])
            head.add_widget(L(label, size=F_TINY + sp(1), color="text3"))
            head.add_widget(Widget())
            parts = []
            if exp_sum:
                parts.append("支出 %s" % fmt_money(exp_sum))
            if inc_sum:
                parts.append("收入 %s" % fmt_money(inc_sum))
            head.add_widget(L("   ".join(parts), size=F_TINY + sp(1), color="text3",
                              align="right"))
            self.list_box.add_widget(head)

            card = Card(size_hint_y=None, height=len(items) * dp(56) + dp(8),
                        padding=[dp(12), dp(4), dp(12), dp(4)], shadow=0.04)
            card.orientation = "vertical"
            for r in items:
                card.add_widget(RecordRow(r, on_tap=self._edit))
            self.list_box.add_widget(card)

    def _edit(self, rec):
        if self.on_edit:
            self.on_edit(rec)
