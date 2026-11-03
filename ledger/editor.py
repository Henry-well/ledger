# -*- coding: utf-8 -*-
"""记账面板：类型切换 / 分类选择 / 金额数字键盘 / 备注 / 日期。"""

import calendar
import datetime

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Triangle
from kivy.metrics import dp, sp
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex

from db import fmt_money, now_str, parse_money, today_str
from theme import CAT_COLORS, F_BODY, F_HUGE, F_SMALL, F_TINY, F_TITLE, col
from widgets import (Card, ConfirmDialog, DimModal, FlatButton, GlyphCircle,
                     InputDialog, L, Space, TapBox, hexrgba, toast)


# --------------------------------------------------------------------- 箭头
class ArrowButton(ButtonBehavior, Widget):
    def __init__(self, direction="up", color="#4F6BED", **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", (dp(30), dp(24)))
        super(ArrowButton, self).__init__(**kwargs)
        self._dir = direction
        self._color = hexrgba(color)
        with self.canvas:
            self._c = Color(*self._color)
            self._t = Triangle(points=[0, 0, 0, 0, 0, 0])
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *a):
        w, h = self.size
        cx, cy = self.center_x, self.center_y
        if self._dir == "up":
            self._t.points = [cx - w * 0.28, cy - h * 0.16,
                              cx + w * 0.28, cy - h * 0.16,
                              cx, cy + h * 0.24]
        else:
            self._t.points = [cx - w * 0.28, cy + h * 0.16,
                              cx + w * 0.28, cy + h * 0.16,
                              cx, cy - h * 0.24]

    def on_press(self):
        self._c.rgba = (self._color[0], self._color[1], self._color[2], 0.45)

    def on_release(self):
        self._c.rgba = self._color


# ------------------------------------------------------------------ 数字键盘
class NumPad(GridLayout):
    def __init__(self, on_key=None, **kwargs):
        kwargs.setdefault("cols", 3)
        kwargs.setdefault("rows", 4)
        kwargs.setdefault("spacing", dp(6))
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(4 * 46 + 3 * 6))
        super(NumPad, self).__init__(**kwargs)
        self._on_key = on_key
        keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", ".", "0", "del"]
        for k in keys:
            text = "⌫" if k == "del" else k
            b = FlatButton(text, bg="#F4F6FA", fg="text",
                           font_size=sp(20), height=dp(46),
                           size_hint_x=1,
                           on_tap=(lambda kk=k: self._on_key(kk)) if on_key else None)
            if k == "del":
                b.label.font_size = sp(17)
            self.add_widget(b)


# ------------------------------------------------------------------ 分类格子
class CategoryChip(ButtonBehavior, BoxLayout):
    def __init__(self, cat, selected=False, on_tap=None, **kwargs):
        kwargs.setdefault("orientation", "vertical")
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(70))
        super(CategoryChip, self).__init__(**kwargs)
        self.cat = cat
        self.selected = selected
        self._on_tap = on_tap
        self.circle = GlyphCircle(cat.get("glyph") or "?",
                                  cat.get("color") or "#A0AEC0", d=dp(38))
        wrap = BoxLayout(size_hint_y=None, height=dp(40))
        wrap.add_widget(Widget())
        wrap.add_widget(self.circle)
        wrap.add_widget(Widget())
        self.add_widget(wrap)
        self.name_label = L(cat["name"], size=F_TINY, color="text2",
                            align="center", shorten=True)
        self.add_widget(self.name_label)
        self._apply()
        if on_tap:
            self.bind(on_release=lambda *_: on_tap(self.cat))

    def _apply(self):
        alpha = 1.0 if self.selected else 0.28
        self.circle.set_color(self.cat.get("color") or "#A0AEC0", alpha)
        self.name_label.color = col("primary") if self.selected else col("text2")

    def set_selected(self, flag):
        self.selected = flag
        self._apply()


# ------------------------------------------------------------------ 日期选择
class DatePickerDialog(DimModal):
    def __init__(self, value=None, on_ok=None, allow_future=True, **kwargs):
        super(DatePickerDialog, self).__init__(**kwargs)
        self._on_ok = on_ok
        self._allow_future = allow_future
        d = value or datetime.date.today()
        self.y, self.m, self.d = d.year, d.month, d.day

        box = Card(size_hint=(0.9, None), height=dp(268),
                   padding=[dp(18), dp(16), dp(18), dp(14)])
        box.orientation = "vertical"
        box.add_widget(L("选择日期", size=F_TITLE))
        box.add_widget(Space(dp(10)))

        cols = BoxLayout(spacing=dp(8), size_hint_y=None, height=dp(120))
        self._cells = {}
        for key, label, color in (("y", "年", "#F1F3F7"),
                                  ("m", "月", "#F1F3F7"),
                                  ("d", "日", "#F1F3F7")):
            cell = Card(bg="#F6F8FB", radius=[dp(12)], shadow=0,
                        padding=[0, dp(6)], orientation="vertical")
            up = ArrowButton("up")
            up.bind(on_release=lambda *_, k=key: self._step(k, 1))
            val = L("", size=sp(17), color="text", align="center")
            dn = ArrowButton("down")
            dn.bind(on_release=lambda *_, k=key: self._step(k, -1))
            cell.add_widget(up)
            cell.add_widget(val)
            cell.add_widget(dn)
            cols.add_widget(cell)
            self._cells[key] = val
        box.add_widget(cols)
        box.add_widget(Space(dp(10)))

        quick = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(8))
        today = datetime.date.today()
        shortcuts = [("今天", today), ("昨天", today - datetime.timedelta(days=1)),
                     ("前天", today - datetime.timedelta(days=2))]
        for text, dt in shortcuts:
            quick.add_widget(FlatButton(
                text, bg="#F1F3F7", fg="text2", font_size=F_SMALL, height=dp(34),
                on_tap=lambda dt=dt: self._set(dt)))
        box.add_widget(quick)
        box.add_widget(Widget())

        row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        row.add_widget(FlatButton("取消", bg="#F1F3F7", fg="text2",
                                  height=dp(44), on_tap=self.dismiss))
        row.add_widget(FlatButton("确定", bg="primary", height=dp(44),
                                  on_tap=self._ok))
        box.add_widget(row)
        self.add_widget(box)
        self._refresh()

    def _set(self, dt):
        self.y, self.m, self.d = dt.year, dt.month, dt.day
        self._refresh()

    def _step(self, key, delta):
        if key == "y":
            self.y = max(2000, min(2100, self.y + delta))
        elif key == "m":
            self.m += delta
            if self.m > 12:
                self.m = 1
                self.y += 1
            elif self.m < 1:
                self.m = 12
                self.y -= 1
        else:
            cur = datetime.date(self.y, self.m, min(self.d, calendar.monthrange(self.y, self.m)[1]))
            cur += datetime.timedelta(days=delta)
            self.y, self.m, self.d = cur.year, cur.month, cur.day
            self._refresh()
            return
        last = calendar.monthrange(self.y, self.m)[1]
        self.d = min(self.d, last)
        self._refresh()

    def _refresh(self):
        self._cells["y"].text = "%d" % self.y
        self._cells["m"].text = "%d" % self.m
        self._cells["d"].text = "%d" % self.d

    def value(self):
        return datetime.date(self.y, self.m, self.d)

    def _ok(self):
        v = self.value()
        today = datetime.date.today()
        if not self._allow_future and v > today:
            toast("不能选择未来的日期")
            return
        self.dismiss()
        if self._on_ok:
            Clock.schedule_once(lambda *_: self._on_ok(v), 0.1)


# ------------------------------------------------------------------ 记账面板
class RecordEditor(DimModal):
    def __init__(self, db, on_saved=None, record=None, default_type="expense",
                 **kwargs):
        super(RecordEditor, self).__init__(**kwargs)
        self.db = db
        self.on_saved = on_saved
        self.record = record
        self.editing = record is not None
        self.type_ = (record["type"] if record else default_type)
        self.buf = ""
        self.cat_id = None
        self.note = ""
        self.date = today_str()
        self._chips = []

        if record:
            self.buf = fmt_money(record["amount"], grouping=False).rstrip("0").rstrip(".") \
                if record["amount"] % 100 else "%d" % (record["amount"] // 100)
            self.cat_id = record.get("category_id")
            self.note = record.get("note") or ""
            self.date = record["ts"][:10]

        self._build()

    # ---------------------------------------------------------- 构建界面
    def _build(self):
        outer = BoxLayout(orientation="vertical")
        root = Card(bg="card", radius=[dp(20), dp(20), 0, 0], shadow=0,
                    orientation="vertical",
                    padding=[dp(16), dp(12), dp(16), dp(14)], spacing=dp(8))
        outer.add_widget(Widget(size_hint_y=None, height=dp(28)))
        outer.add_widget(root)
        self.add_widget(outer)

        # 顶栏
        top = BoxLayout(size_hint_y=None, height=dp(40))
        self.left_btn = FlatButton("删除" if self.editing else "取消",
                                   bg=(0, 0, 0, 0),
                                   fg="expense" if self.editing else "text2",
                                   font_size=F_BODY, width=dp(56),
                                   size_hint=(None, 1),
                                   on_tap=self._on_left)
        top.add_widget(self.left_btn)
        title = L("编辑记录" if self.editing else "记一笔", size=F_TITLE, align="center")
        top.add_widget(title)
        top.add_widget(FlatButton("保存", bg="primary", fg="white", font_size=F_BODY,
                                  width=dp(60), size_hint=(None, 1),
                                  on_tap=self._save))
        root.add_widget(top)

        # 类型切换
        seg_wrap = BoxLayout(size_hint_y=None, height=dp(40))
        seg_wrap.add_widget(Widget())
        seg = Card(bg="#EFF2F8", radius=[dp(20)], shadow=0,
                   size_hint=(None, 1), width=dp(196), padding=[dp(3), dp(3)])
        seg.orientation = "horizontal"
        self.seg_exp = FlatButton("支出", bg="#EFF2F8", fg="text2", font_size=F_SMALL,
                                  height=dp(34), radius=[dp(17)],
                                  on_tap=lambda: self._switch_type("expense"))
        self.seg_inc = FlatButton("收入", bg="#EFF2F8", fg="text2", font_size=F_SMALL,
                                  height=dp(34), radius=[dp(17)],
                                  on_tap=lambda: self._switch_type("income"))
        seg.add_widget(self.seg_exp)
        seg.add_widget(self.seg_inc)
        seg_wrap.add_widget(seg)
        seg_wrap.add_widget(Widget())
        root.add_widget(seg_wrap)

        # 金额显示
        amt_box = BoxLayout(size_hint_y=None, height=dp(62))
        self.amt_label = L("0", size=sp(36), color="text", align="center")
        amt_box.add_widget(self.amt_label)
        root.add_widget(amt_box)

        # 分类
        sv = ScrollView(size_hint_y=1, do_scroll_x=False, bar_width=0,
                        scroll_type=["bars", "content"])
        self.grid = GridLayout(cols=4, spacing=dp(4), size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter("height"))
        sv.add_widget(self.grid)
        root.add_widget(sv)

        # 备注 + 日期
        meta_row = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(8))
        self.note_btn = FlatButton("添加备注", bg="#F6F8FB", fg="text3",
                                   font_size=F_SMALL, height=dp(36),
                                   radius=[dp(10)],
                                   on_tap=self._edit_note)
        meta_row.add_widget(self.note_btn)
        self.date_btn = FlatButton(self._date_text(), bg="#F6F8FB", fg="text2",
                                   font_size=F_SMALL, width=dp(108),
                                   height=dp(36), radius=[dp(10)],
                                   size_hint=(None, 1),
                                   on_tap=self._pick_date)
        meta_row.add_widget(self.date_btn)
        root.add_widget(meta_row)

        # 键盘
        root.add_widget(NumPad(on_key=self._on_key))

        self._refresh_type()
        self._build_categories()
        self._update_amount()

    # ---------------------------------------------------------- 交互逻辑
    def _date_text(self):
        d = self.date
        today = today_str()
        if d == today:
            return "今天"
        yday = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        if d == yday:
            return "昨天"
        return d[5:]

    def _on_left(self):
        if self.editing:
            def do_delete():
                self.db.delete_record(self.record["id"])
                self.dismiss()
                if self.on_saved:
                    self.on_saved(None)
            ConfirmDialog("删除这笔记录？", "删除后无法恢复。", on_ok=do_delete,
                          ok_text="删除", danger=True).open()
        else:
            self.dismiss()

    def _switch_type(self, t):
        if t == self.type_:
            return
        self.type_ = t
        self.cat_id = None
        self._refresh_type()
        self._build_categories()

    def _refresh_type(self):
        is_exp = self.type_ == "expense"
        self.seg_exp.set_bg("primary" if is_exp else "#EFF2F8")
        self.seg_exp.label.color = (1, 1, 1, 1) if is_exp else col("text2")
        self.seg_inc.set_bg("#12B886" if not is_exp else "#EFF2F8")
        self.seg_inc.label.color = (1, 1, 1, 1) if not is_exp else col("text2")

    def _build_categories(self):
        self.grid.clear_widgets()
        self._chips = []
        cats = self.db.categories(self.type_)
        if self.cat_id is None and cats:
            self.cat_id = cats[0]["id"]
        for cat in cats:
            chip = CategoryChip(cat, selected=(cat["id"] == self.cat_id),
                                on_tap=self._select_cat)
            self._chips.append(chip)
            self.grid.add_widget(chip)

    def _select_cat(self, cat):
        self.cat_id = cat["id"]
        for chip in self._chips:
            chip.set_selected(chip.cat["id"] == self.cat_id)

    def _on_key(self, k):
        if k == "del":
            self.buf = self.buf[:-1]
        elif k == ".":
            if "." not in self.buf:
                self.buf = (self.buf or "0") + "."
        else:
            if "." in self.buf and len(self.buf.split(".")[1]) >= 2:
                return
            digits = self.buf.replace(".", "")
            if len(digits) >= 9:
                return
            if self.buf in ("", "0"):
                self.buf = k
            else:
                self.buf += k
        self._update_amount()

    def _update_amount(self):
        text = self.buf or "0"
        if "." in text:
            head, _, tail = text.partition(".")
            text = head + "." + tail[:2]
        n = len(text.replace(".", ""))
        size = sp(36)
        if n >= 8:
            size = sp(24)
        elif n >= 7:
            size = sp(28)
        elif n >= 6:
            size = sp(32)
        self.amt_label.font_size = size
        self.amt_label.text = "¥ " + text

    def _edit_note(self):
        def ok(v):
            self.note = v
            self.note_btn.set_text(v if v else "添加备注")
            self.note_btn.label.color = col("text") if v else col("text3")
            self.note_btn.label.text = (v[:12] + "…") if len(v) > 12 else (v or "添加备注")
        InputDialog("备注", value=self.note, hint="写点什么（可留空）", on_ok=ok).open()

    def _pick_date(self):
        def ok(d):
            self.date = d.strftime("%Y-%m-%d")
            self.date_btn.set_text(self._date_text())
        DatePickerDialog(value=datetime.date(*[int(x) for x in self.date.split("-")]),
                         on_ok=ok, allow_future=False).open()

    def _save(self):
        cents = parse_money(self.buf)
        if not cents or cents <= 0:
            toast("请输入有效金额")
            return
        if not self.cat_id:
            toast("请选择一个分类")
            return
        ts = self.date + " " + datetime.datetime.now().strftime("%H:%M")
        if self.editing:
            self.db.update_record(self.record["id"], self.type_, cents,
                                  self.cat_id, self.note, ts)
        else:
            self.db.add_record(self.type_, cents, self.cat_id, self.note, ts)
        self.dismiss()
        if self.on_saved:
            Clock.schedule_once(lambda *_: self.on_saved(None), 0.1)
