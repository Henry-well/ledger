[app]

# 应用显示名（安卓桌面图标下的名字）
title = 记账本

# 应用内部标识：最终包名 = package.domain + "." + package.name
# 即 org.local.ledger
package.name = ledger
package.domain = org.local

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,otf,ttf,ttc
# 中文字体目录必须显式包含（GitHub Actions 会先下载字体再打包）
source.include_patterns = assets/fonts/*
# 不要把这些开发文件打进 APK
source.exclude_patterns = _test_run.py,_*.db,_shots/*,bin/*,.github/*,README.md,*.pyc,__pycache__/*

version = 1.0.0

# sqlite3 由 p4a 的 python3 recipe 内置，不能写进 requirements（否则报 recipe 找不到）
requirements = python3,kivy==2.3.1,android

orientation = portrait
fullscreen = 0

# ---------------------------------------------------------------- 安卓参数
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 34
android.minapi = 24
android.ndk_api = 24
# 双架构兼容老机型；只想要更小更快的包可删掉 armeabi-v7a
android.archs = arm64-v8a, armeabi-v7a
android.accept_sdk_license = True
# 允许应用把 CSV 导出到公共 Download 目录
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
