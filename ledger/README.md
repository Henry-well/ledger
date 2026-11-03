# 记账本（ledger）—— 纯离线安卓记账 App（Python / Kivy）

一个完全离线的个人记账应用，用 Python + Kivy 编写，可打包成安卓 APK。
所有数据保存在手机本地 SQLite 文件中，**不联网、不上传、无任何第三方依赖服务**。

## 功能

- **总资产**：首次使用设置"初始金额"，总资产 = 初始金额 + 收入 − 支出，首页随时查看
- **记一笔**：支出 / 收入切换、10+ 内置分类、自定义数字键盘（不怕软键盘遮挡）、备注、日期可选（支持今天/昨天/前天快捷键）
- **明细**：按月浏览、按天分组显示当日收支小计，点任意一条可修改或删除
- **统计**：当月收支结余、分类占比环形图、分类排行（含百分比进度条）、近半年收支柱状图
- **分类管理**：新增 / 删除自定义分类（支出、收入分开管理）
- **导出**：一键导出 CSV（UTF-8 BOM，Excel/WPS 可直接打开），优先存到公共 Download 目录
- **数据维护**：清空所有记录（保留分类与初始金额）

## 项目结构

```
ledger/
├── main.py              # 入口：App、根布局、底部导航、悬浮记账按钮
├── db.py                # SQLite 数据层（金额以"分"存储，避免浮点误差）
├── theme.py             # 配色 / 中文字体注册 / 尺寸常量
├── widgets.py           # 通用组件：圆角卡片、按钮、Toast、确认/输入弹窗
├── charts.py            # 环形图、柱状图（纯 Canvas 绘制，零第三方图表库）
├── editor.py            # 记账面板：分类选择、数字键盘、日期选择
├── record_row.py        # 明细行组件
├── screen_home.py       # 首页
├── screen_records.py    # 明细页
├── screen_stats.py      # 统计页
├── screen_settings.py   # 我的（初始金额/分类管理/导出/清空/关于）
├── assets/fonts/        # 中文字体（打包时自动下载，见下）
├── buildozer.spec       # 安卓打包配置
├── .github/workflows/build-apk.yml   # 云打包流水线
├── 打包指引-GitHub云打包.md          # 方式一的手把手教程
└── .gitignore
```

## 在电脑上先试运行

```bash
pip install kivy
python main.py
```

会弹出一个 390×800 的手机模拟窗口，可直接体验全部功能。

## 打包成安卓 APK

### 方式一：GitHub Actions 云打包（推荐，本地无需任何安卓环境）

**完整手把手步骤见：[`打包指引-GitHub云打包.md`](打包指引-GitHub云打包.md)**（含上传代码、触发构建、下载安装、常见报错排查）

速览：

1. 把整个 `ledger` 文件夹推送到你的 GitHub 仓库（**`.github/workflows/build-apk.yml` 必须一起传上去**）
2. 仓库 → **Actions** → 左侧 **Build Android APK** → **Run workflow**
3. 等待 40~70 分钟（首次要下载 Android SDK/NDK；之后有缓存约 15~25 分钟）
4. 运行记录页底部 **Artifacts** → 下载 `ledger-apk.zip` → 解压得到 `.apk`
5. 传到手机安装（需允许"安装未知应用"）

流水线会自动下载 Noto Sans CJK 中文字体再打包，APK 中文显示正常。
公开仓库的 Actions 分钟数完全免费；私有仓库每月 2000 分钟免费额度。

### 方式二：本地 Buildozer 打包（需要 Linux 或 WSL）

```bash
# WSL2 / Ubuntu 22.04
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk autoconf libtool pkg-config \
    zlib1g-dev libncurses-dev cmake libffi-dev libssl-dev
pip install cython==3.0.11 buildozer==1.5.0

# 先放入中文字体（约 16MB）
mkdir -p assets/fonts
curl -L -o assets/fonts/NotoSansCJKsc-Regular.otf \
  "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf"

buildozer android debug          # 首次运行会自动下载 Android SDK/NDK，耗时较长
# 产物在 bin/ 目录
```

### 方式三：手机上直接运行（Pydroid 3，最快验证）

1. 安卓安装 **Pydroid 3**（Play 商店或国内应用市场）
2. 把整个 `ledger` 文件夹拷贝到手机存储，如 `/storage/emulated/0/Pydroid3/ledger/`
3. Pydroid 3 内的 pip 安装 `kivy`（Pydroid 自带预编译仓库，无需编译）
4. 用 Pydroid 3 打开 `main.py` 运行
5. 想要更佳中文显示，可把任意中文 ttf/otf 字体放进 `assets/fonts/`

> Pydroid 方式无需打包即可日常使用，但界面顶部会保留 Pydroid 提示条；
> 长期使用建议用方式一/二打包成独立 APK。

## 数据与隐私

- 数据库文件：`/data/data/org.local.ledger/files/ledger.db`（应用私有目录）
- 记录、分类、初始金额全部在这一个 SQLite 文件里
- 卸载 App 会删除全部数据，**建议定期"导出账本"备份 CSV**
- 导出的 CSV 位于 Download 目录（或应用私有目录，弹窗会显示完整路径）

## 二次开发提示

- 金额一律用整数"分"存储（`db.py` 的 `parse_money` / `fmt_money` 负责换算）
- 内置分类在 `db.py` 顶部的 `EXPENSE_SEED` / `INCOME_SEED`，可自行增改
- 主题色集中在 `theme.py` 的 `PALETTE`
- 环形图刻意用 `Line(ellipse=...)` 粗弧线而非裸 `Mesh` 绘制——部分 GPU 上
  无索引的裸 Mesh 不可见（已在多台设备上踩坑验证）
- `_test_run.py` 是开发用的冒烟测试脚本：注入演示数据并截图六个界面，
  平时不参与打包，可随时删除
