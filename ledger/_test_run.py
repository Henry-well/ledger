# -*- coding: utf-8 -*-
from kivy.config import Config
Config.set("graphics", "density", "1")
"""本地调试用：注入演示数据并截图各页面。运行后自动退出。"""

import datetime
import os
import random
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "_shots")
os.makedirs(OUT, exist_ok=True)
DB = os.path.join(BASE, "_demo.db")
if os.path.exists(DB):
    os.remove(DB)
os.environ["LEDGER_DB"] = DB

from kivy.clock import Clock
from kivy.core.window import Window

import main as m
from db import now_str
from screen_settings import CategoryManager
from editor import RecordEditor


def seed(app):
    db = app.db
    db.initial_balance = 864200  # 8642.00
    cats_exp = db.categories("expense")
    cats_inc = db.categories("income")
    today = datetime.date.today()
    samples = [
        ("expense", 3250, 0, "公司楼下快餐"),
        ("expense", 1200, 1, "地铁月卡"),
        ("expense", 15800, 2, "换季衣服"),
        ("expense", 4500, 4, "电影票"),
        ("expense", 2800, 0, "早餐"),
        ("income", 1200000, 0, "10月工资"),
        ("expense", 6800, 3, "水电燃气"),
        ("expense", 9900, 6, "买书"),
        ("income", 20000, 4, "朋友红包"),
        ("expense", 5600, 0, "晚饭"),
        ("expense", 1500, 1, "打车"),
        ("expense", 23800, 5, "感冒买药"),
    ]
    for i, (t, amt, ci, note) in enumerate(samples):
        d = today - datetime.timedelta(days=i % 9)
        ts = d.strftime("%Y-%m-%d") + " %02d:%02d" % (9 + (i % 10), (i * 7) % 60)
        cat = (cats_exp if t == "expense" else cats_inc)[ci]
        db.add_record(t, amt, cat["id"], note, ts)
    app.root.refresh_all()


class TestApp(m.LedgerApp):
    def on_start(self):
        Clock.schedule_once(self.s0, 0.6)

    def s0(self, dt):
        try:
            seed(self)
        except Exception as e:
            import traceback
            traceback.print_exc()
        Clock.schedule_once(self.s1, 0.7)

    def shot(self, name):
        try:
            path = os.path.join(OUT, name + ".png")
            import ctypes
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            gdi32 = ctypes.windll.gdi32
            hwnd = user32.FindWindowW(None, "记账本")
            if not hwnd:
                raise RuntimeError("kivy window not found")
            rect = wintypes.RECT()
            user32.GetClientRect(hwnd, ctypes.byref(rect))
            w, h = rect.right, rect.bottom
            hdc = user32.GetDC(hwnd)
            mem = gdi32.CreateCompatibleDC(hdc)
            bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
            gdi32.SelectObject(mem, bmp)
            user32.PrintWindow(hwnd, mem, 2)

            class BMIH(ctypes.Structure):
                _fields_ = [("biSize", ctypes.c_uint32), ("biWidth", ctypes.c_int32),
                            ("biHeight", ctypes.c_int32), ("biPlanes", ctypes.c_uint16),
                            ("biBitCount", ctypes.c_uint16), ("biCompression", ctypes.c_uint32),
                            ("biSizeImage", ctypes.c_uint32), ("biXPelsPerMeter", ctypes.c_int32),
                            ("biYPelsPerMeter", ctypes.c_int32), ("biClrUsed", ctypes.c_uint32),
                            ("biClrImportant", ctypes.c_uint32)]
            bmi = BMIH()
            bmi.biSize = ctypes.sizeof(BMIH)
            bmi.biWidth = w
            bmi.biHeight = -h
            bmi.biPlanes = 1
            bmi.biBitCount = 32
            buf = ctypes.create_string_buffer(w * h * 4)
            gdi32.GetDIBits(mem, bmp, 0, h, buf, ctypes.byref(bmi), 0)
            from PIL import Image
            img = Image.frombuffer("RGBA", (w, h), buf.raw, "raw", "BGRA", 0, 1)
            img.convert("RGB").save(path)
            gdi32.DeleteObject(bmp)
            gdi32.DeleteDC(mem)
            user32.ReleaseDC(hwnd, hdc)
            print("saved", path)
        except Exception:
            import traceback
            traceback.print_exc()

    def s1(self, dt):
        self.shot("01_home")
        self.root.switch("records")
        Clock.schedule_once(self.s2, 0.7)

    def s2(self, dt):
        self.shot("02_records")
        self.root.switch("stats")
        Clock.schedule_once(self.s3, 0.8)

    def s3(self, dt):
        self.shot("03_stats")
        self.root.switch("me")
        Clock.schedule_once(self.s4, 0.7)

    def s4(self, dt):
        self.shot("04_me")
        ed = RecordEditor(self.db, on_saved=lambda r: self.root.refresh_all())
        ed.open()
        Clock.schedule_once(lambda dt: self.shot("05_editor"), 0.7)
        Clock.schedule_once(self.s5, 1.5)

    def s5(self, dt):
        # 关闭所有打开的弹窗（ModalView 挂在 Window 上）
        from kivy.core.window import Window
        for w in list(Window.children):
            if hasattr(w, "dismiss"):
                try:
                    w.dismiss()
                except Exception:
                    pass
        Clock.schedule_once(self.s6, 0.5)

    def s6(self, dt):
        cm = CategoryManager(self.db, on_change=None)
        cm.open()
        Clock.schedule_once(lambda dt: self.shot("06_cats"), 0.7)
        Clock.schedule_once(lambda dt: self.stop(), 1.6)


if __name__ == "__main__":
    TestApp().run()
    print("DONE")
