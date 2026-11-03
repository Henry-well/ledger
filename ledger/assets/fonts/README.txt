中文字体放这里（可选）。

App 启动时会按以下顺序查找可用中文字体：

1. assets/fonts/ 下的任意一个：
   - NotoSansSC-Regular.otf / .ttf
   - SourceHanSansCN-Regular.otf
   - NotoSansCJKsc-Regular.otf
   - DroidSansFallback.ttf
2. 安卓系统字体：/system/fonts/ 下的 NotoSansCJK / DroidSansFallback 等
3. 桌面调试：Windows 微软雅黑 / 黑体，macOS 苹方

用 GitHub Actions 打包时，流水线会自动下载 Noto Sans CJK SC 放到本目录。
Pydroid 3 直接运行时会自动使用安卓系统字体，无需手动下载。
