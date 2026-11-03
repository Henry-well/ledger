# -*- coding: utf-8 -*-
"""首页：总资产 + 本月收支 + 最近记录。"""

import datetime

from kivy.graphics import Color, Ellipse, Rectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from db import fmt_money, now_str
from record_row import RecordRow
from theme import F_BODY, F_HUGE, F_SMALL, F_TINY, F_TITLE, col
from widgets import Card, GlyphCircle, L, Space, TapBox


WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


class AssetCard(Card):
    """主色总资产卡片。"""

    def __init__(self, **kwargs):
        super(AssetCard, self).__init__(bg="primary", radius=[dp(20)], shadow=0.16, **kwargs)
        with self.canvas.before:
            self._d1 = Color(1, 1, 1, 0.07)
            self._e1 = Ellipse()
            self._d2 = Color(1, 1, 1, 0.05)
            self._e2 = Ellipse()
        self.bind(pos=self._deco, size=self._deco)

        box = BoxLayout(orientation="vertical", padding=[dp(18), dp(16), dp(18), dp(14)],
                        spacing=dp(2))
        self.add_widget(box)

        box.add_widget(L("当前总资产（元）", size=F_TINY + sp(1), color=(0.92, 0.94, 1, 1)))
        self.amount = L("0.00", size=sp(34), color=(1, 1, 1, 1))
        box.add_widget(self.amount)
        box.add_widget(Widget())

        line = Widget(size_hint_y=None, height=dp(1))
        with line.canvas.before:
            line._c = Color(1, 1, 1, 0.18)
            line._r = Rectangle(pos=line.pos, size=line.size)
        line.bind(pos=lambda *_: setattr(line._r, "pos", line.pos),
                  size=lambda *_: setattr(line._r, "size", line.size))
        box.add_widget(line)

        stats = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        self.exp_box = self._stat("本月支出", "0.00")
        self.inc_box = self._stat("本月收入", "0.00")
        stats.add_widget(self.exp_box[0])
        stats.add_widget(self.inc_box[0])
        box.add_widget(stats)

    def _stat(self, title, value):
        box = BoxLayout(orientation="vertical", spacing=dp(1))
        box.add_widget(L(title, size=F_TINY, color=(0.88, 0.91, 1, 0.9)))
        v = L(value, size=F_BODY + sp(5), color=(1, 1, 1, 1))
        box.add_widget(v)
        return box, v

    def _deco(self, *a):
        r = self.width * 0.55
        self._e1.pos = (self.right - r * 0.55, self.top - r * 0.55)
        self._e1.size = (r, r)
        r2 = self.width * 0.35
        self._e2.pos = (self.right - r2 * 0.9, self.y - r2 * 0.35)
        self._e2.size = (r2, r2)

    def update(self, balance, exp, inc):
        text = fmt_money(balance)
        self.amount.text = text
        n = len(text)
        self.amount.font_size = sp(34) if n < 10 else (sp(28) if n < 13 else sp(23))
        self.exp_box[1].text = fmt_money(exp)
        self.inc_box[1].text = fmt_money(inc)


class HomeScreen(Screen):
    def __init__(self, db, on_goto=None, on_edit=None, **kwargs):
        super(HomeScreen, self).__init__(**kwargs)
        self.db = db
        self.on_goto = on_goto
        self.on_edit = on_edit

        root = BoxLayout(orientation="vertical")
        sv = ScrollView(do_scroll_x=False, bar_width=dp(2))
        body = BoxLayout(orientation="vertical", size_hint_y=None,
                         padding=[dp(16), dp(14), dp(16), dp(20)], spacing=dp(12))
        body.bind(minimum_height=body.setter("height"))
        sv.add_widget(body)
        root.add_widget(sv)
        self.add_widget(root)

        # 顶部
        head = BoxLayout(size_hint_y=None, height=dp(40))
        today = datetime.date.today()
        head.add_widget(L("我的账本", size=sp(20), color="text"))
        right = BoxLayout(orientation="vertical", size_hint_x=None, width=dp(120))
        date_lbl = L("%d月%d日 %s" % (today.month, today.day,
                                     WEEKDAYS[today.weekday()]),
                     size=F_TINY + sp(1), color="text3", align="right")
        right.add_widget(date_lbl)
        head.add_widget(right)
        body.add_widget(head)

        # 资产卡片
        self.card = AssetCard(size_hint_y=None, height=dp(168))
        body.add_widget(self.card)

        # 快捷入口
        quick = BoxLayout(size_hint_y=None, height=dp(64), spacing=dp(10))
        for text, key in (("记一笔", "add"), ("看明细", "records"), ("做统计", "stats")):
            quick.add_widget(self._quick_btn(text, key))
        body.add_widget(quick)

        # 最近记录
        sec = BoxLayout(size_hint_y=None, height=dp(30))
        sec.add_widget(L("最近记录", size=F_BODY, color="text"))
        more = TapBox(size_hint=(None, 1), width=dp(70),
                      on_tap=lambda: self.on_goto and self.on_goto("records"))
        more.add_widget(L("查看全部 ›", size=F_TINY + sp(1), color="text3", align="right"))
        sec.add_widget(Widget())
        sec.add_widget(more)
        body.add_widget(sec)

        self.recent = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(2))
        self.recent.bind(minimum_height=self.recent.setter("height"))
        card = Card(size_hint_y=None, height=dp(8),
                    padding=[dp(12), dp(4), dp(12), dp(4)], shadow=0.04)
        card.add_widget(self.recent)
        self.empty = L("还没有记录，点右下角「+」记第一笔", size=F_SMALL,
                       color="text3", align="center")
        self.empty.size_hint_y = None
        self.empty.height = dp(80)
        body.add_widget(card)
        body.add_widget(self.empty)
        self.card_wrap = card
        self.body = body

    def _quick_btn(self, text, action):
        from kivy.uix.anchorlayout import AnchorLayout
        c = Card(bg="card", radius=[dp(14)], shadow=0.04, size_hint=(1, 1))
        anchor = AnchorLayout()
        lbl = L(text, size=F_SMALL, color="text2", align="center")
        lbl.size_hint = (None, None)
        lbl.size = (dp(90), dp(30))
        anchor.add_widget(lbl)
        anchor.add_widget(TapBox(on_tap=lambda: self._quick(action)))
        c.add_widget(anchor)
        return c

    def _quick(self, action):
        if action == "add":
            app = self.get_app()
            if app:
                app.open_editor()
        else:
            if self.on_goto:
                self.on_goto(action)

    def get_app(self):
        from kivy.app import App
        return App.get_running_app()

    def on_pre_enter(self, *args):
        self.refresh()

    def refresh(self):
        ym = now_str()[:7]
        inc, exp = self.db.summary(ym)
        self.card.update(self.db.balance(), exp, inc)

        self.recent.clear_widgets()
        rows = self.db.records(limit=6)
        for r in rows:
            self.recent.add_widget(RecordRow(r, on_tap=self._edit))
        self.empty.opacity = 0 if rows else 1
        self.empty.height = 0 if rows else dp(80)
        self.card_wrap.opacity = 1 if rows else 0
        self.card_wrap.height = 0 if not rows else len(rows) * dp(56) + dp(8)

    def _edit(self, rec):
        app = self.get_app()
        if app:
            app.open_editor(record=rec)
