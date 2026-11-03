# -*- coding: utf-8 -*-
"""配色、字体、尺寸。"""

import os

from kivy.core.text import LabelBase
from kivy.metrics import dp, sp
from kivy.resources import resource_find
from kivy.utils import get_color_from_hex

PALETTE = {
    "bg": "#F3F5F9",
    "card": "#FFFFFF",
    "primary": "#4F6BED",
    "primary_light": "#EAEEFF",
    "primary_dark": "#3A50C4",
    "text": "#1B2233",
    "text2": "#6B7280",
    "text3": "#A3AAB8",
    "line": "#EDF0F5",
    "expense": "#E8553F",
    "income": "#12B886",
    "warn": "#F59E0B",
    "chip_bg": "#F4F6FA",
    "white": "#FFFFFF",
    "black": "#000000",
    "mask": (0, 0, 0, 0.45),
}

# 分类自定义时可选的颜色
CAT_COLORS = [
    "#FF7A45", "#40A9FF", "#B37FEB", "#36CFC9", "#FF7875",
    "#597EF7", "#52C41A", "#FAAD14", "#F759AB", "#8C7B70",
    "#13C2C2", "#7A8FA6",
]


def col(key, alpha=1.0):
    """取色，返回 RGBA 元组。支持主题色名或 '#RRGGBB'。"""
    if isinstance(key, (tuple, list)):
        return tuple(key)
    if isinstance(key, str) and key.startswith("#"):
        r, g, b, _a = get_color_from_hex(key)
        return (r, g, b, alpha)
    r, g, b, _a = get_color_from_hex(PALETTE[key])
    return (r, g, b, alpha)


FONT_NAME = "Roboto"  # 注册后所有默认文本都用中文字体


def _pick_font():
    candidates = [
        "assets/fonts/NotoSansSC-Regular.otf",
        "assets/fonts/NotoSansSC-Regular.ttf",
        "assets/fonts/SourceHanSansCN-Regular.otf",
        "assets/fonts/NotoSansCJKsc-Regular.otf",
        "assets/fonts/DroidSansFallback.ttf",
        # Android 系统自带
        "/system/fonts/NotoSansCJK-Regular.ttc",
        "/system/fonts/DroidSansFallback.ttf",
        "/system/fonts/NotoSansSC-Regular.otf",
        "/system/fonts/DroidSansChinese.ttf",
        # 桌面端调试用
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyh.ttf",
        "C:/Windows/Fonts/simhei.ttf",
        "/System/Library/Fonts/PingFang.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    for p in candidates:
        if os.path.isabs(p):
            hit = p if os.path.exists(p) else None
        else:
            hit = resource_find(p)
            if hit and not os.path.exists(hit):
                hit = None
        if hit:
            return hit
    return None


def setup_fonts():
    """把中文字体注册成默认字体（覆盖 Roboto），这样所有控件都能显示中文。"""
    global FONT_NAME
    path = _pick_font()
    if not path:
        print("[theme] 未找到中文字体，中文可能显示为方块。"
              "请把 NotoSansSC-Regular.otf 放到 assets/fonts/")
        return None
    try:
        LabelBase.register(name="Roboto", fn_regular=path)
        FONT_NAME = "Roboto"
        print("[theme] 使用字体:", path)
    except Exception as e:  # pragma: no cover
        print("[theme] 字体注册失败:", e)
        return None
    return path


# ------------------------------------------------------------------ 常用尺寸
RADIUS = dp(16)
PAD = dp(16)
NAV_H = dp(58)

F_TITLE = sp(19)
F_BODY = sp(14)
F_SMALL = sp(12)
F_TINY = sp(10)
F_HUGE = sp(34)
