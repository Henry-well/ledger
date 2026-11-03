# 方式一：GitHub 云打包 APK —— 手把手操作指引

> **这条路适合谁**：手上只有一台 Windows 电脑（甚至只有手机），不想装 WSL、Android SDK、NDK 那一堆几 GB 的东西。
> 把代码放到 GitHub，让 GitHub 的服务器帮你编译，你只负责最后下载一个 APK 文件。
>
> **要花多久**：首次约 40~70 分钟（其中你只需要操作 10 分钟，剩下是机器在编译）。
> **要花多少钱**：0 元。公开仓库的 Actions 分钟数完全免费；私有仓库每月有 2000 分钟免费额度。

---

## 0. 先看全流程（心里有个数）

```
① 注册 GitHub 账号
      ↓
② 新建一个空仓库
      ↓
③ 把 ledger 文件夹里的代码传上去（关键：.github 目录不能漏）
      ↓
④ 在网页上点 "Run workflow"
      ↓
⑤ 等 40~70 分钟（可以去吃饭）
      ↓
⑥ 下载 ledger-apk.zip → 解压出 .apk
      ↓
⑦ 传到手机 → 允许"未知来源"→ 安装 → 开始记账
```

---

## 1. 准备工作

| 需要的东西 | 说明 |
|---|---|
| 一个邮箱 | 注册 GitHub 用，QQ 邮箱、163 邮箱都行 |
| 一个 GitHub 账号 | 没注册过就往下看第 1 步 |
| 能上网的电脑 | 上传代码、下载 APK 都在网页上完成 |
| 安卓手机 | Android 5.0 以上（本 App 最低支持 API 24 = Android 7.0） |

> 如果你的网络访问 GitHub 很慢，可以全程用手机流量热点，或者早晚时段操作。
> 上传代码和下载 APK 只有几十 MB，流量压力不大。

---

## 2. 注册 / 登录 GitHub

1. 浏览器打开 **https://github.com**
2. 点右上角 **Sign up**，按提示填邮箱、密码、用户名（用户名只能是英文+数字+连字符）
3. 邮箱会收到验证码，验证完就注册成功
4. 已有账号直接 **Sign in**

> 界面是英文的。看不懂没关系，下面每一步都会告诉你**点哪个位置的哪个词**。

---

## 3. 新建一个空仓库（Repository）

1. 登录后点右上角的 **`+`** 号 → 选 **New repository**
2. 按下表填写：

| 字段 | 填什么 | 说明 |
|---|---|---|
| **Repository name** | `ledger` | 仓库名，随便起，全英文 |
| **Description** | 留空或写"离线记账App" | 可选 |
| **Public / Private** | 建议选 **Public** | Public：Actions 分钟数无限免费<br>Private：每月 2000 分钟免费（一次构建约 40 分钟，够用 40 多次）<br>代码里没有任何隐私数据，选 Public 更省事 |
| **Add a README file** | **不要勾** | 勾了后面上传会冲突 |
| **.gitignore / license** | 都选 **None** | 我们自己的 `.gitignore` 已经写好了 |

3. 点绿色按钮 **Create repository**
4. 成功后你会看到一个空仓库页面，上面写着 "Quick setup — if you've done this kind of thing before"

**把这个页面地址记下来**，长这样：`https://github.com/你的用户名/ledger`

---

## 4. 把代码传到仓库（三种方式，选一种）

先说明要传哪些文件。你电脑上的 `ledger` 文件夹里应该是这样：

```
ledger/
├── .github/workflows/build-apk.yml   ← ⚠️ 最重要，少了它就没有构建按钮
├── .gitignore
├── assets/fonts/README.txt
├── buildozer.spec                     ← ⚠️ 打包配置
├── main.py                            ← ⚠️ 程序入口
├── db.py
├── theme.py
├── widgets.py
├── charts.py
├── editor.py
├── record_row.py
├── screen_home.py
├── screen_records.py
├── screen_stats.py
└── screen_settings.py
```

> `_test_run.py`、`_shots/`、`_demo.db`、`__pycache__` 这些是开发用的，**不用传**
> （`.gitignore` 已经把它们排除了）。
> `assets/fonts/` 里没有字体文件也没关系，流水线会自动下载中文字体。

---

### 方式 A：用 GitHub Desktop 上传（最省事，推荐新手）

1. 下载安装 **GitHub Desktop**：https://desktop.github.com
2. 打开后点 **Sign in to GitHub.com**，用刚注册的账号登录
3. 菜单栏 **File → Add local repository…**
4. **Local path** 选到你的 `ledger` 文件夹（就是有 `main.py` 的那一层）→ 点 **Add repository**
5. 如果提示 "This directory does not appear to be a Git repository"，点提示里的
   **create a repository** 链接 → 直接点 **Create repository**
6. 此时左侧会列出所有待提交文件，**检查列表里有没有 `.github/workflows/build-apk.yml`**
   - 有 → 继续第 7 步
   - 没有 → 说明文件夹里缺这个文件，回到方式 C 手动创建
7. 左下角 **Summary** 里随便写一句，比如 `init`，点 **Commit to main**
8. 点顶部 **Publish repository**
   - **Name** 填 `ledger`
   - **Keep this code private** 按你第 3 步的选择决定（取消勾选 = 公开）
   - 点 **Publish repository**
9. 完成，代码已上传

---

### 方式 B：网页拖拽上传（不用装任何软件）

1. 打开你的仓库页面，点 **Add file** → **Upload files**
2. 打开电脑上的 `ledger` 文件夹，**全选里面的所有文件和文件夹**（Ctrl+A），
   直接拖到网页的虚线框里
   - 也可以点 **choose your files** 后多选
   - Chrome / Edge 支持直接拖文件夹，会保留子目录结构
3. 等进度条走完，下方 **Commit changes** 里写 `init`，点 **Commit changes**
4. **关键检查**：回到仓库首页，看看文件列表里有没有 `.github` 这个文件夹
   - **有** → 太好了，直接跳到第 5 步
   - **没有**（Windows 默认隐藏以点开头的文件夹，很容易漏）→ 手动补一个：

   **补 `.github/workflows/build-apk.yml` 的步骤：**
   - 仓库首页点 **Add file** → **Create new file**
   - 在文件名输入框里**输入完整路径**：`.github/workflows/build-apk.yml`
     （输入 `/` 的时候 GitHub 会自动帮你建目录，看到路径分段显示就对了）
   - 打开你电脑上的 `ledger/.github/workflows/build-apk.yml`，用记事本打开，
     **全选复制**，粘贴到网页下方的大编辑框里
   - 拉到底点 **Commit changes** → 再点 **Commit changes** 确认

---

### 方式 C：命令行 Git（会用 Git 的人看这里）

在 `ledger` 文件夹里打开 Git Bash / 终端：

```bash
git init
git add .
git commit -m "init: 离线记账 App"
git branch -M main
git remote add origin https://github.com/你的用户名/ledger.git
git push -u origin main
```

> 推送时会要求登录。GitHub 从 2021 年起**不接受账号密码**，要用 Personal Access Token：
> GitHub 右上角头像 → **Settings** → 左侧最下 **Developer settings** →
> **Personal access tokens** → **Tokens (classic)** → **Generate new token (classic)** →
> 勾选 `repo` 和 `workflow` → 生成后复制那串 `ghp_xxxxx`，粘贴到密码位置。

---

## 5. 确认 Actions 已启用

1. 在仓库页面顶部标签栏点 **Actions**
2. 第一次进来如果看到绿色按钮 **I understand my workflows, go ahead and enable them**，点它
3. 左侧列表里应该能看到 **Build Android APK** 这一项
   - **看不到** → 99% 是 `.github/workflows/build-apk.yml` 没传上去，回到第 4 步补
   - 能看到但点进去提示 "Workflow does not have any runs" → 正常，还没跑过

> ⚠️ **重要**：`Run workflow` 按钮只有在**默认分支（main）上存在这个文件**时才会出现。
> 如果你把文件传到了别的分支，先把 main 分支设成默认分支
> （Settings → Branches → Default branch → 切换）。

---

## 6. 触发构建 🚀

1. 点 **Actions** → 左侧点 **Build Android APK**
2. 右侧会出现一条提示 "This workflow has a workflow_dispatch event trigger."，
   点右边的 **Run workflow** 按钮
3. 弹出小面板：
   - **Use workflow from**：选 `main`
   - 点绿色 **Run workflow**
4. 刷新页面（F5），列表里会出现一条新的运行记录，黄色圆点 = 正在跑，绿色勾 = 成功，红色叉 = 失败

**点进这条记录，你能看到实时日志**，一共 7 个步骤：

| 步骤名 | 大概耗时 | 在干什么 |
|---|---|---|
| Checkout source | 5 秒 | 下载你的代码 |
| Cache buildozer | 10 秒 | 恢复上次的编译缓存（首次为空） |
| Set up Python 3.11 | 15 秒 | 装 Python |
| Install system dependencies | 1~2 分钟 | 装 Java 17、编译工具链 |
| Download Chinese font | 10 秒 | 下载 Noto Sans CJK 中文字体（约 16MB） |
| Install buildozer | 30 秒 | 装打包工具 |
| **Build APK (debug)** | **30~60 分钟** | 下载 Android SDK/NDK 并编译，**这一步最慢，别慌** |
| Upload APK | 10 秒 | 把成品上传成可下载的文件 |

> **首次构建特别慢是正常的**：要从 Google 服务器下载 Android SDK + NDK（约 2GB），
> 还要现场编译 Python 解释器和 Kivy。第二次起有缓存，一般 15~25 分钟。

---

## 7. 下载 APK

构建成功（绿色勾）后：

1. 点进这次运行记录，页面往下拉到底
2. 找到 **Artifacts** 区域，点 **ledger-apk**
3. 浏览器会下载一个 `ledger-apk.zip`（约 30~45MB）
4. 解压，里面是一个 `.apk` 文件，名字类似：
   `ledger-1.0.0-arm64-v8a_armeabi-v7a-debug.apk`
5. **这就是安装包**，改个短名字（比如 `记账本.apk`）方便传输

> ⚠️ Artifacts 默认**保留 30 天**，过期就没了。下载后请自己存好。

---

## 8. 装到手机上

### 8.1 把 APK 传到手机（任选一种）

| 方式 | 操作 |
|---|---|
| **微信** | 电脑微信 → 文件传输助手 → 发送 APK → 手机微信打开 → 下载 → 点"用其他应用打开"→ 安装 |
| **QQ** | 同上，QQ 对 APK 支持更好，可以直接点安装 |
| **数据线** | 手机连电脑 → 选"传输文件"→ 把 APK 拖到手机 `Download` 文件夹 → 手机上用文件管理器点开 |
| **网盘** | 上传到百度网盘 / 阿里云盘，手机端下载后点开 |

### 8.2 允许"安装未知来源应用"

第一次装会提示"为了安全，你的手机不允许安装此来源的应用"，按下面操作：

- **小米 / Redmi（MIUI / HyperOS）**：
  设置 → 应用设置 → 应用管理 → 右上角 ⋮ → 特殊权限 → 安装未知应用 → 找到你用来打开 APK 的 App（比如"文件管理"或"微信"）→ 允许。
  **另外必须关闭"纯净模式"**：设置 → 应用设置 → 右上角 ⋮ → 纯净模式 → 关闭。
  不关的话会一直提示"该应用未经安全检测"。
- **华为 / 荣耀（HarmonyOS / EMUI）**：
  设置 → 安全 → 更多安全设置 → 外部来源应用下载 → 允许。
  如果提示"应用未经华为安全检测"，点"继续安装"或"仍然安装"。
- **OPPO / vivo / 一加**：
  安装时直接点"继续安装"/"仍然安装"，按提示开启对应权限即可。
- **三星 / 原生 Android**：
  设置 → 应用 → 特殊应用权限 → 安装未知应用 → 允许对应来源。

### 8.3 安装并首次打开

1. 点开 APK → **安装** → 等待几秒 → **打开**
2. 首次启动会申请"存储权限"，**要点允许**（导出 CSV 需要）
3. 进入首页后，第一件事：**底部「我的」→ 初始金额 → 输入你现在手上的总钱数**
   （比如银行卡+微信+支付宝一共 8642.00 元，就填 `8642`）
   之后每笔收支都会自动加减，首页蓝卡显示的就是实时总资产。

---

## 9. 装好之后怎么用

| 想做的事 | 操作 |
|---|---|
| 记一笔 | 点右下角蓝色 **+** → 选支出/收入 → 点分类 → 数字键盘输入金额 → 可选填备注、改日期 → 点右上/底部保存 |
| 看这个月花了多少 | 底部 **明细**，顶部切换月份，按天分组，每天有小计 |
| 看花在哪了 | 底部 **统计**：环形图看占比、排行榜看分类金额、柱状图看近半年趋势 |
| 改初始金额 | 底部 **我的** → 初始金额 |
| 加自己的分类 | 底部 **我的** → 分类管理 → 选支出/收入 → 新增 → 填名字、选颜色 |
| 备份数据 | 底部 **我的** → 导出账本 → 生成 CSV（Excel/WPS 直接打开），文件在 Download 目录 |
| 换手机 / 重装 | 先导出 CSV 存到网盘，再重装 |

> ⚠️ **数据只存在本机**，卸载 App 会把记录一起删掉。建议每月导出一次 CSV 备份。

---

## 10. 常见问题排查

### 构建相关

**Q1：Actions 页面看不到 "Build Android APK"**
→ `.github/workflows/build-apk.yml` 没传到仓库。用"方式 B"里手动 Create new file 的办法补上，路径必须一字不差：`.github/workflows/build-apk.yml`

**Q2：有 workflow 但没有 "Run workflow" 按钮**
→ 文件不在默认分支上。Settings → Branches → Default branch 看是不是 `main`；或者文件只存在于其他分支。

**Q3：构建卡在 "Build APK" 一小时以上**
→ 首次构建正常。可以点开日志看当前在做什么，出现 `Downloading Android SDK` / `Building Cython` / `Compiling Python` 都属于正常进度。超过 120 分钟会被自动超时终止（workflow 里设的上限），这种情况重跑一次通常就能过（有缓存了）。

**Q4：构建失败，日志里有 `command failed` / `Aidl` / `licenses`**
→ 十有八九是 Android SDK license 没接受。检查 `buildozer.spec` 里有没有这一行：
`android.accept_sdk_license = True`。有的话重跑一次（SDK 下载偶尔网络抖动）。

**Q5：日志报 `Cython` 版本错误 / `cython_sources` 相关**
→ workflow 里已经固定 `cython==3.0.11`。如果你改过，改回去。

**Q6：日志报 `recipe 'sqlite3' not found`**
→ `requirements` 里不能写 `sqlite3`（p4a 内置支持）。确认 `buildozer.spec` 里是：
`requirements = python3,kivy==2.3.1,android`

**Q7：构建成功但 APK 只有几 MB，装上去打开就闪退**
→ 说明 Kivy 没编进去。检查 `requirements` 里 `kivy==2.3.1` 是否拼对（不能写 `Kivy`）。

**Q8：私有仓库提示 "The job was not started because ... spending limit"**
→ 免费额度用完了，或账号需要绑定支付方式才能用私有仓库的 Actions。
解决办法：把仓库改成 Public（Settings → 最下面 Danger Zone → Change visibility → Make public），公开仓库不限分钟数。

### 安装相关

**Q9：手机提示"解析包错误" / "应用未安装"**
→ 两种可能：
① 下载的 zip 没解压，你直接拿 `.zip` 去装了 —— 要解压出 `.apk` 再装；
② 手机 Android 版本低于 7.0（API 24），不支持。

**Q10：提示"应用签名不一致"**
→ 手机上已装过同包名（`org.local.ledger`）的其他版本。先把旧版卸载再装。

**Q11：装好了，但界面全是方块 / 中文变问号**
→ 中文字体没打进去。检查构建日志里 "Download Chinese font" 这一步有没有成功，以及 APK 体积是否大于 25MB。如果字体下载失败，重跑一次构建。

**Q12：能打开但点"导出账本"没反应**
→ 没给存储权限。设置 → 应用管理 → 记账本 → 权限 → 允许存储。

### 使用相关

**Q13：换手机数据怎么迁移**
→ 老手机"我的 → 导出账本"得到 CSV → 传到新手机。目前版本不支持导入 CSV 自动恢复，需要手工补录（这是后续可以加的功能）。

**Q14：能不能不要"DEBUG"字样 / 上架应用商店**
→ 现在打的是 debug 包，可以直接日常用，但体积偏大、不能上架。要上架需要 release 签名：
在 `buildozer.spec` 里配 `android.release_artifact = apk`，生成 keystore，然后
`buildozer android release`。需要的话告诉我，我再补一套签名流程。

---

## 11. 后续改动代码怎么办

改完 `ledger` 里的代码，重新上传（GitHub Desktop 里会自动显示改动 → 写说明 → **Commit to main** → **Push origin**），
然后去 Actions 页面再点一次 **Run workflow** 就行。
因为有缓存，第二次起一般 15~25 分钟出包。

如果你让仓库绑定了标签触发（workflow 里已经配好），也可以直接推一个标签：

```bash
git tag v1.0.1
git push origin v1.0.1
```

会自动开始构建。

---

## 附：一张图记住关键路径

```
https://github.com/你的用户名/ledger          ← 你的仓库
        └── Actions 标签页
              └── Build Android APK
                    └── Run workflow  ← 点这里开始构建
                          └── 等 40~70 分钟
                                └── 页面底部 Artifacts → ledger-apk  ← 点这里下载
                                      └── 解压得到 .apk → 传手机 → 安装
```

---

有任何一步卡住，把 GitHub Actions 的**报错日志最后 50 行**贴给我，我直接告诉你改哪里。
