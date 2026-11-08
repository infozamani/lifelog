# database.py
# لایه دیتابیس محلی اپلیکیشن LifeLog
# از SQLite استفاده می‌کنیم که داخل خود پایتون هست و نیازی به نصب جداگانه ندارد.
# داده‌ها در فایلی به نام lifelog.db کنار اپ ذخیره می‌شوند.

import sqlite3
import os
from datetime import datetime


# نام فایل دیتابیس
DB_NAME = "lifelog.db"


def get_connection():
    """
    یک اتصال به دیتابیس برمی‌گرداند.
    هر بار که لازم باشد با دیتابیس کار کنیم، این تابع را صدا می‌زنیم.
    """
    # مسیر فایل دیتابیس را کنار فایل اجرایی قرار می‌دهیم
    # (در موبایل، این مسیر به پوشه داده‌های اپ اشاره می‌کند)
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_NAME)
    conn = sqlite3.connect(db_path)
    # باعث می‌شود نتایج به صورت دیکشنری برگردند (دسترسی با نام ستون)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    جدول‌های دیتابیس را می‌سازد (اگر وجود نداشته باشند).
    این تابع را یک بار در شروع اپ صدا می‌زنیم.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # جدول تراکنش‌های مالی
    # type: "income" (درآمد) یا "expense" (هزینه)
    # category: دسته‌بندی مثل "کار" یا "شخصی"
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            note TEXT,
            created_at TEXT NOT NULL
        )
    """)
            # جدول ملاقات‌ها
    # meeting_at: زمان ملاقات به فرمت ISO
    # remind_at: زمان آلارم (معمولاً چند دقیقه قبل از ملاقات)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            note TEXT,
            meeting_at TEXT NOT NULL,
            remind_at TEXT,
            notified INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


def add_transaction(tx_type: str, amount: float, category: str, note: str = ""):
    """
    یک تراکنش جدید به دیتابیس اضافه می‌کند.
    tx_type: "income" یا "expense"
    amount: مبلغ
    category: دسته‌بندی
    note: توضیح اختیاری
    """
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat(timespec="seconds")
    cursor.execute(
        "INSERT INTO transactions (type, amount, category, note, created_at) VALUES (?, ?, ?, ?, ?)",
        (tx_type, amount, category, note, now),
    )
    conn.commit()
    conn.close()


def get_transactions(limit: int = 50):
    """
    آخرین تراکنش‌ها را برمی‌گرداند (جدیدترین اول).
    limit: حداکثر تعداد رکورد
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM transactions ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_summary():
    """
    خلاصه مالی را برمی‌گرداند: مجموع درآمد، مجموع هزینه و موجودی.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type = 'income'")
    total_income = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type = 'expense'")
    total_expense = cursor.fetchone()[0]

    conn.close()

    return {
        "income": total_income,
        "expense": total_expense,
        "balance": total_income - total_expense,
    }
# ============ توابع ملاقات‌ها ============

def add_meeting(title: str, meeting_at: str, note: str = "", remind_at: str = None):
    """
    یک ملاقات جدید اضافه می‌کند.
    meeting_at و remind_at به فرمت ISO هستند (مثلاً "2026-11-10T14:30:00")
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO meetings (title, note, meeting_at, remind_at) VALUES (?, ?, ?, ?)",
        (title, note, meeting_at, remind_at),
    )
    conn.commit()
    conn.close()


def get_meetings(limit: int = 50):
    """آخرین ملاقات‌ها را برمی‌گرداند (نزدیک‌ترین زمان اول)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM meetings ORDER BY meeting_at ASC LIMIT ?",
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_due_meetings(now_iso: str):
    """
    ملاقات‌هایی که زمان آلارمشان رسیده و هنوز notified نشده‌اند را برمی‌گرداند.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM meetings WHERE remind_at <= ? AND notified = 0 AND remind_at IS NOT NULL",
        (now_iso,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def mark_meeting_notified(meeting_id: int):
    """یک ملاقات را به عنوان آلارم‌داده‌شده علامت می‌زند."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE meetings SET notified = 1 WHERE id = ?", (meeting_id,))
    conn.commit()
    conn.close()


def delete_meeting(meeting_id: int):
    """یک ملاقات را حذف می‌کند."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))
    conn.commit()
    conn.close()
 
# ============ توابع ملاقات‌ها ============

def add_meeting(title: str, meeting_at: str, note: str = "", remind_at: str = None):
    """
    یک ملاقات جدید اضافه می‌کند.
    meeting_at و remind_at به فرمت ISO هستند (مثلاً "2026-11-10T14:30:00")
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO meetings (title, note, meeting_at, remind_at) VALUES (?, ?, ?, ?)",
        (title, note, meeting_at, remind_at),
    )
    conn.commit()
    conn.close()


def get_meetings(limit: int = 50):
    """آخرین ملاقات‌ها را برمی‌گرداند (نزدیک‌ترین زمان اول)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM meetings ORDER BY meeting_at ASC LIMIT ?",
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_due_meetings(now_iso: str):
    """
    ملاقات‌هایی که زمان آلارمشان رسیده و هنوز notified نشده‌اند را برمی‌گرداند.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM meetings WHERE remind_at <= ? AND notified = 0 AND remind_at IS NOT NULL",
        (now_iso,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def mark_meeting_notified(meeting_id: int):
    """یک ملاقات را به عنوان آلارم‌داده‌شده علامت می‌زند."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE meetings SET notified = 1 WHERE id = ?", (meeting_id,))
    conn.commit()
    conn.close()


def delete_meeting(meeting_id: int):
    """یک ملاقات را حذف می‌کند."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))
    conn.commit()
    conn.close()

# ============ توابع گزارش‌گیری ============

def get_expense_by_category():
    """
    مجموع هزینه‌ها را به تفکیک دسته‌بندی برمی‌گرداند.
    خروجی: لیستی از دیکشنری‌ها مثل [{"category": "کار", "total": 150000}, ...]
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT category, SUM(amount) as total
        FROM transactions
        WHERE type = 'expense'
        GROUP BY category
        ORDER BY total DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [{"category": r["category"], "total": r["total"]} for r in rows]


def get_monthly_summary():
    """
    خلاصه درآمد و هزینه را به تفکیک ماه برمی‌گرداند (۶ ماه اخیر).
    خروجی: لیستی از دیکشنری‌ها با کلیدهای month, income, expense
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            substr(created_at, 1, 7) as month,
            SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
            SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expense
        FROM transactions
        GROUP BY month
        ORDER BY month DESC
        LIMIT 6
    """)
    rows = cursor.fetchall()
    conn.close()
    # برعکس می‌کنیم تا قدیمی‌ترین ماه اول باشد (برای نمودار)
    return [{"month": r["month"], "income": r["income"], "expense": r["expense"]} for r in reversed(rows)]
# ============ توابع آرشیو و جستجو ============

def search_transactions(keyword: str = "", tx_type: str = None, limit: int = 100):
    """
    تراکنش‌ها را با فیلتر جستجو می‌کند.
    keyword: در دسته‌بندی و توضیح جستجو می‌کند
    tx_type: "income" یا "expense" یا None (همه)
    """
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM transactions WHERE 1=1"
    params = []

    if keyword:
        query += " AND (category LIKE ? OR note LIKE ?)"
        params.extend([f"%{keyword}%", f"%{keyword}%"])
    if tx_type:
        query += " AND type = ?"
        params.append(tx_type)

    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


def search_meetings(keyword: str = "", only_future: bool = False, limit: int = 100):
    """
    ملاقات‌ها را جستجو می‌کند.
    only_future: فقط ملاقات‌های آینده
    """
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM meetings WHERE 1=1"
    params = []

    if keyword:
        query += " AND (title LIKE ? OR note LIKE ?)"
        params.extend([f"%{keyword}%", f"%{keyword}%"])
    if only_future:
        query += " AND meeting_at >= ?"
        params.append(datetime.now().isoformat(timespec="seconds"))

    query += " ORDER BY meeting_at ASC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows
