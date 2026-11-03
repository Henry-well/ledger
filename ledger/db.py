# -*- coding: utf-8 -*-
"""
数据层：本地 SQLite，纯离线，不发起任何网络请求。

设计要点
--------
* 金额一律用「分」为单位的整数存储，避免浮点误差（1234 表示 12.34 元）。
* 记录时间以 'YYYY-MM-DD HH:MM' 文本存储，按月份查询直接用 LIKE 前缀，简单可靠。
* 分类表支持用户自定义，内置分类带 builtin=1 标记。
"""

import os
import sqlite3
import datetime

# ---------------------------------------------------------------- 内置分类
EXPENSE_SEED = [
    ("餐饮", "餐", "#FF7A45"),
    ("交通", "行", "#40A9FF"),
    ("购物", "购", "#B37FEB"),
    ("居住", "住", "#8C7B70"),
    ("娱乐", "娱", "#36CFC9"),
    ("医疗", "医", "#FF7875"),
    ("学习", "学", "#597EF7"),
    ("通讯", "讯", "#7A8FA6"),
    ("人情", "礼", "#F759AB"),
    ("其他", "他", "#A0AEC0"),
]

INCOME_SEED = [
    ("工资", "薪", "#52C41A"),
    ("奖金", "奖", "#13C2C2"),
    ("理财", "利", "#FAAD14"),
    ("兼职", "兼", "#40A9FF"),
    ("红包", "包", "#FF7875"),
    ("其他", "他", "#A0AEC0"),
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    k TEXT PRIMARY KEY,
    v TEXT
);
CREATE TABLE IF NOT EXISTS category (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name     TEXT    NOT NULL,
    glyph    TEXT    NOT NULL DEFAULT '',
    color    TEXT    NOT NULL DEFAULT '#A0AEC0',
    type     TEXT    NOT NULL,
    sort     INTEGER NOT NULL DEFAULT 0,
    builtin  INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS record (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    type        TEXT    NOT NULL,
    amount      INTEGER NOT NULL,
    category_id INTEGER,
    note        TEXT    NOT NULL DEFAULT '',
    ts          TEXT    NOT NULL,
    created     TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_record_ts ON record(ts);
"""


def today_str():
    return datetime.date.today().strftime("%Y-%m-%d")


def now_str():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def ym_add(ym, delta):
    """'2026-11' + 1 -> '2026-12'"""
    y, m = int(ym[:4]), int(ym[5:7])
    m += delta
    while m > 12:
        m -= 12
        y += 1
    while m < 1:
        m += 12
        y -= 1
    return "%04d-%02d" % (y, m)


def fmt_money(cents, grouping=True):
    """12345 -> '123.45'；-680 -> '-6.80'"""
    cents = int(cents or 0)
    neg = cents < 0
    cents = abs(cents)
    s = "%d.%02d" % (cents // 100, cents % 100)
    if grouping:
        head, _, tail = s.partition(".")
        out = []
        while len(head) > 3:
            out.insert(0, head[-3:])
            head = head[:-3]
        out.insert(0, head)
        s = ",".join(out) + "." + tail
    return ("-" if neg else "") + s


def parse_money(text):
    """'12.3' -> 1230；非法返回 None"""
    if text is None:
        return None
    t = str(text).strip().replace(",", "").replace("，", "")
    if not t:
        return None
    try:
        return int(round(float(t) * 100))
    except ValueError:
        return None


class Database(object):
    def __init__(self, path):
        self.path = path
        folder = os.path.dirname(path)
        if folder and not os.path.isdir(folder):
            try:
                os.makedirs(folder, exist_ok=True)
            except OSError:
                pass
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._init()

    # ------------------------------------------------------------ 初始化
    def _init(self):
        c = self.conn.cursor()
        c.executescript(SCHEMA)
        n = c.execute("SELECT COUNT(*) FROM category").fetchone()[0]
        if n == 0:
            for i, (name, glyph, color) in enumerate(EXPENSE_SEED):
                c.execute(
                    "INSERT INTO category(name,glyph,color,type,sort,builtin)"
                    " VALUES(?,?,?,?,?,1)", (name, glyph, color, "expense", i))
            for i, (name, glyph, color) in enumerate(INCOME_SEED):
                c.execute(
                    "INSERT INTO category(name,glyph,color,type,sort,builtin)"
                    " VALUES(?,?,?,?,?,1)", (name, glyph, color, "income", i))
        if c.execute("SELECT COUNT(*) FROM meta WHERE k='initial_balance'").fetchone()[0] == 0:
            c.execute("INSERT INTO meta(k,v) VALUES('initial_balance','0')")
        self.conn.commit()

    # ------------------------------------------------------------ meta
    def get_meta(self, key, default=None):
        row = self.conn.execute("SELECT v FROM meta WHERE k=?", (key,)).fetchone()
        return row[0] if row else default

    def set_meta(self, key, value):
        self.conn.execute(
            "INSERT INTO meta(k,v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v",
            (key, str(value)))
        self.conn.commit()

    # ------------------------------------------------------------ 余额
    @property
    def initial_balance(self):
        return int(self.get_meta("initial_balance", "0") or 0)

    @initial_balance.setter
    def initial_balance(self, cents):
        self.set_meta("initial_balance", int(cents))

    def total_income(self):
        r = self.conn.execute(
            "SELECT COALESCE(SUM(amount),0) FROM record WHERE type='income'").fetchone()
        return r[0]

    def total_expense(self):
        r = self.conn.execute(
            "SELECT COALESCE(SUM(amount),0) FROM record WHERE type='expense'").fetchone()
        return r[0]

    def balance(self):
        return self.initial_balance + self.total_income() - self.total_expense()

    # ------------------------------------------------------------ 分类
    def categories(self, type_):
        rows = self.conn.execute(
            "SELECT * FROM category WHERE type=? ORDER BY sort, id", (type_,)).fetchall()
        return [dict(r) for r in rows]

    def category(self, cid):
        row = self.conn.execute("SELECT * FROM category WHERE id=?", (cid,)).fetchone()
        return dict(row) if row else None

    def add_category(self, name, type_, glyph=None, color="#A0AEC0"):
        name = (name or "").strip()
        if not name:
            return None
        glyph = (glyph or name[0])[:1]
        row = self.conn.execute(
            "SELECT COALESCE(MAX(sort),0)+1 FROM category WHERE type=?", (type_,)).fetchone()
        cur = self.conn.execute(
            "INSERT INTO category(name,glyph,color,type,sort,builtin) VALUES(?,?,?,?,?,0)",
            (name, glyph, color, type_, row[0]))
        self.conn.commit()
        return cur.lastrowid

    def update_category(self, cid, name=None, glyph=None, color=None):
        cat = self.category(cid)
        if not cat:
            return
        self.conn.execute(
            "UPDATE category SET name=?, glyph=?, color=? WHERE id=?",
            (name if name is not None else cat["name"],
             glyph if glyph is not None else cat["glyph"],
             color if color is not None else cat["color"], cid))
        self.conn.commit()

    def category_record_count(self, cid):
        r = self.conn.execute(
            "SELECT COUNT(*) FROM record WHERE category_id=?", (cid,)).fetchone()
        return r[0]

    def delete_category(self, cid):
        """删除分类；该分类下的记账记录转到同类型「其他」，没有则置空。"""
        cat = self.category(cid)
        if not cat:
            return 0
        other = self.conn.execute(
            "SELECT id FROM category WHERE type=? AND name='其他' AND id<>? LIMIT 1",
            (cat["type"], cid)).fetchone()
        target = other[0] if other else None
        n = self.category_record_count(cid)
        self.conn.execute("UPDATE record SET category_id=? WHERE category_id=?", (target, cid))
        self.conn.execute("DELETE FROM category WHERE id=?", (cid,))
        self.conn.commit()
        return n

    # ------------------------------------------------------------ 记账
    def add_record(self, type_, amount, category_id, note="", ts=None):
        ts = ts or now_str()
        cur = self.conn.execute(
            "INSERT INTO record(type,amount,category_id,note,ts,created) VALUES(?,?,?,?,?,?)",
            (type_, int(amount), category_id, note or "", ts, now_str()))
        self.conn.commit()
        return cur.lastrowid

    def update_record(self, rid, type_, amount, category_id, note="", ts=None):
        old = self.conn.execute("SELECT ts FROM record WHERE id=?", (rid,)).fetchone()
        ts = ts or (old[0] if old else now_str())
        self.conn.execute(
            "UPDATE record SET type=?, amount=?, category_id=?, note=?, ts=? WHERE id=?",
            (type_, int(amount), category_id, note or "", ts, rid))
        self.conn.commit()

    def delete_record(self, rid):
        self.conn.execute("DELETE FROM record WHERE id=?", (rid,))
        self.conn.commit()

    def records(self, ym=None, type_=None, limit=None, offset=0):
        sql = ("SELECT r.*, c.name AS cat_name, c.glyph AS cat_glyph, c.color AS cat_color"
               " FROM record r LEFT JOIN category c ON c.id = r.category_id WHERE 1=1")
        args = []
        if ym:
            sql += " AND r.ts LIKE ?"
            args.append(ym + "%")
        if type_:
            sql += " AND r.type = ?"
            args.append(type_)
        sql += " ORDER BY r.ts DESC, r.id DESC"
        if limit:
            sql += " LIMIT ? OFFSET ?"
            args += [int(limit), int(offset)]
        rows = self.conn.execute(sql, args).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            if not d.get("cat_name"):
                d["cat_name"] = "未分类"
                d["cat_glyph"] = "?"
                d["cat_color"] = "#A0AEC0"
            out.append(d)
        return out

    def record(self, rid):
        rows = self.conn.execute(
            "SELECT r.*, c.name AS cat_name, c.glyph AS cat_glyph, c.color AS cat_color"
            " FROM record r LEFT JOIN category c ON c.id = r.category_id WHERE r.id=?",
            (rid,)).fetchall()
        return dict(rows[0]) if rows else None

    # ------------------------------------------------------------ 统计
    def summary(self, ym):
        """返回 (收入分, 支出分)"""
        inc = self.conn.execute(
            "SELECT COALESCE(SUM(amount),0) FROM record WHERE type='income' AND ts LIKE ?",
            (ym + "%",)).fetchone()[0]
        exp = self.conn.execute(
            "SELECT COALESCE(SUM(amount),0) FROM record WHERE type='expense' AND ts LIKE ?",
            (ym + "%",)).fetchone()[0]
        return inc, exp

    def breakdown(self, ym, type_="expense"):
        rows = self.conn.execute(
            "SELECT COALESCE(c.name,'未分类') AS name, COALESCE(c.glyph,'?') AS glyph,"
            " COALESCE(c.color,'#A0AEC0') AS color, SUM(r.amount) AS total, COUNT(*) AS cnt"
            " FROM record r LEFT JOIN category c ON c.id=r.category_id"
            " WHERE r.type=? AND r.ts LIKE ?"
            " GROUP BY r.category_id ORDER BY total DESC",
            (type_, ym + "%")).fetchall()
        return [dict(r) for r in rows]

    def daily_totals(self, ym):
        rows = self.conn.execute(
            "SELECT substr(ts,1,10) AS d,"
            " SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) AS exp,"
            " SUM(CASE WHEN type='income'  THEN amount ELSE 0 END) AS inc"
            " FROM record WHERE ts LIKE ? GROUP BY d ORDER BY d", (ym + "%",)).fetchall()
        return {r["d"]: (r["inc"], r["exp"]) for r in rows}

    def trend(self, months):
        """按给定月份列表返回 [(ym, inc, exp)]"""
        out = []
        for ym in months:
            inc, exp = self.summary(ym)
            out.append((ym, inc, exp))
        return out

    def months_with_data(self):
        rows = self.conn.execute(
            "SELECT DISTINCT substr(ts,1,7) AS ym FROM record ORDER BY ym DESC").fetchall()
        return [r["ym"] for r in rows]

    def first_record_month(self):
        row = self.conn.execute(
            "SELECT MIN(substr(ts,1,7)) FROM record").fetchone()
        return row[0] if row and row[0] else None

    # ------------------------------------------------------------ 导出 / 清空
    def export_csv(self, path):
        import csv
        rows = self.records()
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["日期", "类型", "分类", "金额(元)", "备注"])
            for r in rows:
                w.writerow([
                    r["ts"],
                    "收入" if r["type"] == "income" else "支出",
                    r["cat_name"],
                    fmt_money(r["amount"], grouping=False),
                    r["note"],
                ])
        return path

    def clear_records(self):
        self.conn.execute("DELETE FROM record")
        self.conn.commit()

    def record_count(self):
        return self.conn.execute("SELECT COUNT(*) FROM record").fetchone()[0]

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass
