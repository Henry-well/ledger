# -*- coding: utf-8 -*-
"""我的：初始余额、分类管理、导出、清空、关于。"""

import datetime
import os
import random

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from db import fmt_money, parse_money
from record_row import RecordRow
from theme import CAT_COLORS, F_BODY, F_SMALL, F_TINY, F_TITLE, col
from widgets import (Card, ConfirmDialog, DimModal, Divider, FlatButton,
                     GlyphCircle, InputDialog, L, Space, TapBox, toast)

VERSION = "1.0.0"


class InfoDialog(DimModal):
    def __init__(self, title, body, **kwargs):
        super(InfoDialog, self).__init__(**kwargs)
        box = Card(size_hint=(0.88, None), height=dp(300),
                   padding=[dp(18), dp(18), dp(18), dp(14)])
        box.orientation = "vertical"
        box.add_widget(L(title, size=F_TITLE, color="text"))
        box.add_widget(Space(dp(10)))
        msg = L(body, size=F_SMALL, color="text2", align="left")
        msg.text_size = (Window.width * 0.88 - dp(36), None)
        msg.valign = "top"
        box.add_widget(msg)
        box.add_widget(Widget())
        box.add_widget(FlatButton("知道了", bg="primary", height=dp(44),
                                  on_tap=self.dismiss))
        self.add_widget(box)


class SettingRow(TapBox):
    def __init__(self, title, subtitle="", value="", on_tap=None, danger=False,
                 divider=True, **kwargs):
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(54))
        kwargs.setdefault("orientation", "vertical")
        super(SettingRow, self).__init__(on_tap=on_tap, **kwargs)
        box = BoxLayout(orientation="vertical", padding=[dp(4), dp(4)])
        row = BoxLayout(spacing=dp(8))
        row.add_widget(L(title, size=F_BODY,
                         color="expense" if danger else "text", shorten=True))
        self.value_lbl = None
        if value:
            v = L(value, size=F_SMALL, color="text3", align="right")
            v.size_hint_x = None
            v.width = dp(120)
            row.add_widget(v)
            self.value_lbl = v
        arrow = L("›", size=sp(18), color="text3", align="right")
        arrow.size_hint_x = None
        arrow.width = dp(14)
        row.add_widget(arrow)
        box.add_widget(row)
        if subtitle:
            box.add_widget(L(subtitle, size=F_TINY, color="text3"))
        self.add_widget(box)
        if divider:
            self.add_widget(Divider())

    def set_value(self, text):
        if self.value_lbl is not None:
            self.value_lbl.text = text


class CategoryManager(DimModal):
    def __init__(self, db, on_change=None, **kwargs):
        super(CategoryManager, self).__init__(**kwargs)
        self.db = db
        self.on_change = on_change
        self.type_ = "expense"

        box = Card(size_hint=(0.92, 0.82), padding=[dp(16), dp(14), dp(16), dp(12)])
        box.orientation = "vertical"
        head = BoxLayout(size_hint_y=None, height=dp(36))
        head.add_widget(L("分类管理", size=F_TITLE, color="text"))
        head.add_widget(Widget())
        close = TapBox(size_hint=(None, 1), width=dp(44), on_tap=self.dismiss)
        close.add_widget(L("完成", size=F_SMALL, color="primary", align="right"))
        head.add_widget(close)
        box.add_widget(head)
        box.add_widget(Space(dp(6)))

        tabs = BoxLayout(size_hint_y=None, height=dp(36), spacing=dp(8))
        self.tab_exp = FlatButton("支出分类", bg="primary", fg="white", font_size=F_SMALL,
                                  height=dp(34), radius=[dp(10)],
                                  on_tap=lambda: self._tab("expense"))
        self.tab_inc = FlatButton("收入分类", bg="#F1F3F7", fg="text2", font_size=F_SMALL,
                                  height=dp(34), radius=[dp(10)],
                                  on_tap=lambda: self._tab("income"))
        tabs.add_widget(self.tab_exp)
        tabs.add_widget(self.tab_inc)
        box.add_widget(tabs)
        box.add_widget(Space(dp(8)))

        sv = ScrollView(do_scroll_x=False, bar_width=dp(2))
        self.list_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(2))
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        sv.add_widget(self.list_box)
        box.add_widget(sv)
        box.add_widget(Space(dp(8)))
        box.add_widget(FlatButton("+ 新增分类", bg="#EAEEFF", fg="primary",
                                  height=dp(44), radius=[dp(12)],
                                  on_tap=self._add))
        self.add_widget(box)
        self._refresh()

    def _tab(self, t):
        if t == self.type_:
            return
        self.type_ = t
        self.tab_exp.set_bg("primary" if t == "expense" else "#F1F3F7")
        self.tab_exp.label.color = (1, 1, 1, 1) if t == "expense" else col("text2")
        self.tab_inc.set_bg("primary" if t == "income" else "#F1F3F7")
        self.tab_inc.label.color = (1, 1, 1, 1) if t == "income" else col("text2")
        self._refresh()

    def _refresh(self):
        self.list_box.clear_widgets()
        for cat in self.db.categories(self.type_):
            row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
            row.add_widget(Widget(size_hint_x=None, width=dp(2)))
            row.add_widget(GlyphCircle(cat["glyph"] or "?", cat["color"], d=dp(32),
                                       font_size=sp(12)))
            row.add_widget(L(cat["name"], size=F_BODY, color="text"))
            row.add_widget(Widget())
            cnt = self.db.category_record_count(cat["id"])
            if cnt:
                n = L("%d笔" % cnt, size=F_TINY, color="text3", align="right")
                n.size_hint_x = None
                n.width = dp(46)
                row.add_widget(n)
            rm = TapBox(size_hint=(None, 1), width=dp(40),
                        on_tap=lambda c=cat: self._delete(c))
            rm.add_widget(L("删除", size=F_TINY, color="text3", align="right"))
            row.add_widget(rm)
            row.add_widget(Divider())
            self.list_box.add_widget(row)

    def _add(self):
        def ok(name):
            if not name:
                toast("请输入分类名称")
                return
            used = self.db.categories(self.type_)
            name_in_use = any(c["name"] == name for c in used)
            if name_in_use:
                toast("已存在同名分类")
                return
            if len(name) > 6:
                toast("名称最多 6 个字")
                return
            color = random.choice(CAT_COLORS)
            self.db.add_category(name, self.type_, color=color)
            self._refresh()
            if self.on_change:
                self.on_change()
        InputDialog("新增%s分类" % ("支出" if self.type_ == "expense" else "收入"),
                    hint="例如：宠物、健身", on_ok=ok, max_len=6).open()

    def _delete(self, cat):
        cnt = self.db.category_record_count(cat["id"])
        msg = "该分类下有 %d 笔记录，删除后会移到「其他」分类。" % cnt if cnt \
            else "删除后不可恢复。"
        def do():
            self.db.delete_category(cat["id"])
            self._refresh()
            if self.on_change:
                self.on_change()
            toast("已删除")
        ConfirmDialog("删除「%s」？" % cat["name"], msg, on_ok=do,
                      ok_text="删除", danger=True).open()


class SettingsScreen(Screen):
    def __init__(self, db, **kwargs):
        super(SettingsScreen, self).__init__(**kwargs)
        self.db = db

        root = BoxLayout(orientation="vertical")
        self.add_widget(root)
        sv = ScrollView(do_scroll_x=False, bar_width=dp(2))
        body = BoxLayout(orientation="vertical", size_hint_y=None,
                         padding=[dp(16), dp(14), dp(16), dp(90)], spacing=dp(10))
        body.bind(minimum_height=body.setter("height"))
        sv.add_widget(body)
        root.add_widget(sv)

        body.add_widget(L("我的", size=sp(20), color="text"))

        # 余额概览
        self.bal_card = Card(size_hint_y=None, height=dp(88), bg="primary",
                             radius=[dp(18)], shadow=0.12, padding=[dp(18), dp(12)])
        self.bal_card.orientation = "vertical"
        self.bal_card.add_widget(L("当前总资产（元）", size=F_TINY,
                                   color=(0.9, 0.93, 1, 0.95)))
        self.bal_value = L("0.00", size=sp(26), color=(1, 1, 1, 1))
        self.bal_card.add_widget(self.bal_value)
        body.add_widget(self.bal_card)

        # 数据
        body.add_widget(self._group_title("账本设置"))
        g1 = Card(size_hint_y=None, padding=[dp(14), dp(2)], shadow=0.04)
        g1.bind(minimum_height=g1.setter("height"))
        g1.orientation = "vertical"
        self.row_initial = SettingRow(
            "初始金额", "开户前的余额，用于计算总资产", value=fmt_money(self.db.initial_balance),
            on_tap=self._edit_initial)
        g1.add_widget(self.row_initial)
        g1.add_widget(SettingRow("分类管理", "增删自己的收支分类",
                                 on_tap=self._open_categories))
        g1.add_widget(SettingRow("导出账本", "导出为 CSV，可用 Excel 打开",
                                 on_tap=self._export, divider=False))
        body.add_widget(g1)

        # 数据维护
        body.add_widget(self._group_title("数据"))
        g2 = Card(size_hint_y=None, padding=[dp(14), dp(2)], shadow=0.04)
        g2.bind(minimum_height=g2.setter("height"))
        g2.orientation = "vertical"
        self.row_count = SettingRow("记录条数", value="%d 条" % self.db.record_count(),
                                    on_tap=None)
        g2.add_widget(self.row_count)
        g2.add_widget(SettingRow("清空所有记录", "只删记录，保留分类和初始金额",
                                 danger=True, on_tap=self._clear, divider=False))
        body.add_widget(g2)

        body.add_widget(self._group_title("关于"))
        g3 = Card(size_hint_y=None, padding=[dp(14), dp(2)], shadow=0.04)
        g3.bind(minimum_height=g3.setter("height"))
        g3.orientation = "vertical"
        g3.add_widget(SettingRow("版本", value=VERSION, on_tap=None))
        g3.add_widget(SettingRow("使用说明", on_tap=self._about, divider=False))
        body.add_widget(g3)

        body.add_widget(Space(dp(10)))
        body.add_widget(L("全部数据保存在手机本地 · 无需联网 · 不上传任何信息",
                          size=F_TINY, color="text3", align="center"))
        self.group1 = g1

    def _group_title(self, text):
        box = BoxLayout(size_hint_y=None, height=dp(28))
        box.add_widget(L(text, size=F_TINY + sp(1), color="text3"))
        return box

    def on_pre_enter(self, *args):
        self.refresh()

    def refresh(self):
        self.bal_value.text = fmt_money(self.db.balance())
        self.row_initial.set_value(fmt_money(self.db.initial_balance))
        self.row_count.set_value("%d 条" % self.db.record_count())

    # ------------------------------------------------------------ 动作
    def _edit_initial(self):
        cur = fmt_money(self.db.initial_balance, grouping=False)
        def ok(v):
            cents = parse_money(v)
            if cents is None:
                toast("请输入有效金额")
                return
            self.db.initial_balance = cents
            self.refresh()
            app = self._app()
            if app:
                app.refresh_all()
            toast("初始金额已更新")
        InputDialog("初始金额", value=cur, hint="例如：12000", numeric=True,
                    on_ok=ok).open()

    def _open_categories(self):
        app = self._app()
        CategoryManager(self.db, on_change=lambda: app and app.refresh_all()).open()

    def _clear(self):
        n = self.db.record_count()
        if n == 0:
            toast("还没有任何记录")
            return
        def do():
            self.db.clear_records()
            self.refresh()
            app = self._app()
            if app:
                app.refresh_all()
            toast("已清空 %d 条记录" % n)
        ConfirmDialog("清空所有记录？", "将删除全部 %d 条记账记录，此操作不可恢复。" % n,
                      on_ok=do, ok_text="清空", danger=True).open()

    def _export(self):
        app = self._app()
        name = "账本_%s.csv" % datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        dirs = []
        try:
            from android.storage import primary_external_storage_path
            dirs.append(os.path.join(primary_external_storage_path(), "Download"))
        except Exception:
            pass
        ext = os.environ.get("EXTERNAL_STORAGE")
        if ext:
            dirs.append(os.path.join(ext, "Download"))
            dirs.append(ext)
        home = os.path.expanduser("~")
        dirs.append(os.path.join(home, "Downloads"))
        if app:
            dirs.append(app.user_data_dir)
        for d in dirs:
            try:
                if not os.path.isdir(d):
                    continue
                path = os.path.join(d, name)
                self.db.export_csv(path)
                InfoDialog("导出成功", "文件已保存到：\n\n%s\n\n共 %d 条记录，可用 Excel / WPS 打开。"
                           % (path, self.db.record_count())).open()
                return
            except Exception:
                continue
        toast("导出失败：找不到可写目录")

    def _about(self):
        InfoDialog("使用说明",
                   "1. 在「我的 → 初始金额」填入手头现有的钱，作为起点。\n\n"
                   "2. 点右下角 + 记一笔，选分类、输金额、可加备注和改日期。\n\n"
                   "3. 总资产 = 初始金额 + 收入 − 支出，随时可在首页查看。\n\n"
                   "4. 明细页左右滑动月份可查历史；点任意一条可修改或删除。\n\n"
                   "5. 所有数据存在手机本地 SQLite 文件里，卸载 App 会一并删除，"
                   "建议定期用「导出账本」备份。").open()

    def _app(self):
        from kivy.app import App
        return App.get_running_app()
