# main.py
# اپلیکیشن LifeLog - نسخه با ظاهر بهبودیافته (راست‌چین، فونت وزیرمتن، تم نیلی)

import flet as ft
import database as db
import threading
import time
from datetime import datetime, timedelta


def main(page: ft.Page):
    page.title = "LifeLog"

    # ============ تنظیمات ظاهری ============
    # ثبت فونت فارسی وزیرمتن (فایل باید در assets/Vazirmatn-Regular.ttf باشد)
    page.fonts = {
        "Vazirmatn": "assets/Vazirmatn-Regular.ttf"
    }

    # تم سراسری: رنگ پایه نیلی + فونت وزیرمتن
    page.theme = ft.Theme(
        color_scheme_seed=ft.Colors.INDIGO,
        font_family="Vazirmatn",
    )

    # راست‌چین کردن کل صفحه (برای فارسی)
    page.rtl = True

    page.padding = 16
    page.scroll = ft.ScrollMode.AUTO
    page.bgcolor = ft.Colors.GREY_50

    db.init_db()

    # ============ تب مالی ============
    txt_income = ft.Text("0", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700)
    txt_expense = ft.Text("0", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_700)
    txt_balance = ft.Text("0", size=20, weight=ft.FontWeight.BOLD)

    summary_card = ft.Container(
        content=ft.Row(
            controls=[
                ft.Column([ft.Text("درآمد", size=12, color=ft.Colors.GREY_600), txt_income],
                          horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                ft.Column([ft.Text("هزینه", size=12, color=ft.Colors.GREY_600), txt_expense],
                          horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                ft.Column([ft.Text("موجودی", size=12, color=ft.Colors.GREY_600), txt_balance],
                          horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
            ],
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
        ),
        padding=16, border_radius=12, bgcolor=ft.Colors.BLUE_50,
        border=ft.Border.all(1, ft.Colors.BLUE_100),
    )

    type_dropdown = ft.Dropdown(
        label="نوع",
        options=[
            ft.dropdown.Option("income", "درآمد"),
            ft.dropdown.Option("expense", "هزینه"),
        ],
        value="expense", width=140,
    )
    amount_field = ft.TextField(label="مبلغ", keyboard_type=ft.KeyboardType.NUMBER, width=140)
    category_field = ft.TextField(label="دسته‌بندی", hint_text="مثلاً کار، شخصی", width=180)
    note_field = ft.TextField(label="توضیح (اختیاری)", width=340)
    tx_list = ft.Column(spacing=8)

    def refresh_summary():
        s = db.get_summary()
        txt_income.value = f"{s['income']:,.0f}"
        txt_expense.value = f"{s['expense']:,.0f}"
        txt_balance.value = f"{s['balance']:,.0f}"

    def refresh_transactions():
        tx_list.controls.clear()
        rows = db.get_transactions()
        if not rows:
            tx_list.controls.append(ft.Text("هنوز تراکنشی ثبت نشده است.", color=ft.Colors.GREY_500))
        else:
            for row in rows:
                is_income = row["type"] == "income"
                color = ft.Colors.GREEN_700 if is_income else ft.Colors.RED_700
                sign = "+" if is_income else "-"
                card = ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Column([
                                ft.Text(row["category"], weight=ft.FontWeight.BOLD, size=14),
                                ft.Text(row["note"] or "-", size=12, color=ft.Colors.GREY_600),
                                ft.Text(row["created_at"].replace("T", " "), size=10, color=ft.Colors.GREY_400),
                            ], spacing=2, expand=True),
                            ft.Text(f"{sign}{row['amount']:,.0f}", size=16, weight=ft.FontWeight.BOLD, color=color),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=12, border_radius=10, bgcolor=ft.Colors.WHITE,
                    border=ft.Border.all(1, ft.Colors.GREY_200),
                )
                tx_list.controls.append(card)

    def on_submit(e):
        if not amount_field.value:
            page.show_dialog(ft.SnackBar(ft.Text("لطفاً مبلغ را وارد کنید.")))
            return
        try:
            amount = float(amount_field.value.replace(",", ""))
        except ValueError:
            page.show_dialog(ft.SnackBar(ft.Text("مبلغ باید عدد باشد.")))
            return
        if not category_field.value:
            page.show_dialog(ft.SnackBar(ft.Text("لطفاً دسته‌بندی را وارد کنید.")))
            return
        db.add_transaction(type_dropdown.value, amount, category_field.value.strip(),
                           (note_field.value or "").strip())
        amount_field.value = ""
        category_field.value = ""
        note_field.value = ""
        refresh_summary()
        refresh_transactions()
        page.show_dialog(ft.SnackBar(ft.Text("✅ تراکنش ثبت شد."), bgcolor=ft.Colors.GREEN_400))
        page.update()

    submit_button = ft.FilledButton(content="ثبت تراکنش", icon=ft.Icons.SAVE, on_click=on_submit, width=340)

    refresh_summary()
    refresh_transactions()

    finance_tab = ft.Column([
        summary_card,
        ft.Divider(),
        ft.Text("ثبت تراکنش جدید", size=16, weight=ft.FontWeight.BOLD),
        ft.Row([type_dropdown, amount_field], alignment=ft.MainAxisAlignment.START),
        ft.Row([category_field, note_field], alignment=ft.MainAxisAlignment.START, wrap=True),
        submit_button,
        ft.Divider(),
        ft.Text("تراکنش‌های اخیر", size=16, weight=ft.FontWeight.BOLD),
        tx_list,
    ], spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

    # ============ تب ملاقات‌ها ============
    meeting_title = ft.TextField(label="عنوان ملاقات", width=340)
    meeting_date = ft.TextField(label="تاریخ (YYYY-MM-DD)", hint_text="2026-11-15", width=160)
    meeting_time = ft.TextField(label="ساعت (HH:MM)", hint_text="14:30", width=120)
    meeting_remind = ft.Dropdown(
        label="آلارم قبل از",
        options=[
            ft.dropdown.Option("0", "سر وقت"),
            ft.dropdown.Option("5", "۵ دقیقه قبل"),
            ft.dropdown.Option("15", "۱۵ دقیقه قبل"),
            ft.dropdown.Option("30", "۳۰ دقیقه قبل"),
            ft.dropdown.Option("60", "۱ ساعت قبل"),
        ],
        value="15", width=160,
    )
    meeting_list = ft.Column(spacing=8)

    def refresh_meetings():
        meeting_list.controls.clear()
        rows = db.get_meetings()
        if not rows:
            meeting_list.controls.append(ft.Text("هنوز ملاقاتی ثبت نشده است.", color=ft.Colors.GREY_500))
        else:
            for row in rows:
                is_past = row["meeting_at"] < datetime.now().isoformat(timespec="seconds")
                color = ft.Colors.GREY_500 if is_past else ft.Colors.BLUE_700
                card = ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Column([
                                ft.Text(row["title"], weight=ft.FontWeight.BOLD, size=14, color=color),
                                ft.Text(row["note"] or "-", size=12, color=ft.Colors.GREY_600),
                                ft.Text(row["meeting_at"].replace("T", " "), size=11,
                                        color=ft.Colors.GREY_400),
                            ], spacing=2, expand=True),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE,
                                icon_color=ft.Colors.RED_400,
                                tooltip="حذف",
                                on_click=lambda e, mid=row["id"]: delete_meeting_click(mid),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=12, border_radius=10, bgcolor=ft.Colors.WHITE,
                    border=ft.Border.all(1, ft.Colors.GREY_200),
                )
                meeting_list.controls.append(card)

    def delete_meeting_click(mid):
        db.delete_meeting(mid)
        refresh_meetings()
        page.update()

    def on_add_meeting(e):
        if not meeting_title.value:
            page.show_dialog(ft.SnackBar(ft.Text("عنوان ملاقات را وارد کنید.")))
            return
        if not meeting_date.value or not meeting_time.value:
            page.show_dialog(ft.SnackBar(ft.Text("تاریخ و ساعت را وارد کنید.")))
            return
        try:
            dt = datetime.strptime(f"{meeting_date.value} {meeting_time.value}", "%Y-%m-%d %H:%M")
        except ValueError:
            page.show_dialog(ft.SnackBar(ft.Text("فرمت تاریخ/ساعت اشتباه است. مثال: 2026-11-15 و 14:30")))
            return

        minutes_before = int(meeting_remind.value)
        remind_dt = dt - timedelta(minutes=minutes_before)
        remind_iso = remind_dt.isoformat(timespec="seconds")
        meeting_iso = dt.isoformat(timespec="seconds")

        db.add_meeting(meeting_title.value.strip(), meeting_iso, "", remind_iso)
        meeting_title.value = ""
        meeting_date.value = ""
        meeting_time.value = ""
        refresh_meetings()
        page.show_dialog(ft.SnackBar(ft.Text("✅ ملاقات ثبت شد."), bgcolor=ft.Colors.GREEN_400))
        page.update()

    add_meeting_btn = ft.FilledButton(content="ثبت ملاقات", icon=ft.Icons.EVENT, on_click=on_add_meeting, width=340)

    refresh_meetings()

    meetings_tab = ft.Column([
        ft.Text("ثبت ملاقات جدید", size=16, weight=ft.FontWeight.BOLD),
        meeting_title,
        ft.Row([meeting_date, meeting_time], alignment=ft.MainAxisAlignment.START),
        meeting_remind,
        add_meeting_btn,
        ft.Divider(),
        ft.Text("ملاقات‌های آینده", size=16, weight=ft.FontWeight.BOLD),
        meeting_list,
    ], spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

    # ============ حلقه بررسی آلارم‌ها ============
    def alarm_loop():
        while True:
            try:
                now_iso = datetime.now().isoformat(timespec="seconds")
                due = db.get_due_meetings(now_iso)
                for m in due:
                    db.mark_meeting_notified(m["id"])
                    page.show_dialog(ft.SnackBar(
                        ft.Text(f"⏰ یادآوری: {m['title']} - {m['meeting_at'].replace('T', ' ')}"),
                        bgcolor=ft.Colors.ORANGE_600,
                        duration=10000,
                    ))
                    page.update()
                time.sleep(30)
            except Exception as ex:
                print("Alarm loop error:", ex)
                time.sleep(30)

    threading.Thread(target=alarm_loop, daemon=True).start()

    # ============ تب گزارش‌ها ============
    import flet_charts as fch

    chart_container = ft.Column(spacing=10, expand=True)

    def refresh_reports():
        chart_container.controls.clear()

        # نمودار دایره‌ای
        cat_data = db.get_expense_by_category()
        if cat_data:
            palette = [
                ft.Colors.BLUE_400, ft.Colors.RED_400, ft.Colors.GREEN_400,
                ft.Colors.ORANGE_400, ft.Colors.PURPLE_400, ft.Colors.TEAL_400,
            ]
            total_expense = sum(c["total"] for c in cat_data)
            sections = []
            for i, c in enumerate(cat_data):
                percent = (c["total"] / total_expense * 100) if total_expense else 0
                sections.append(
                    fch.PieChartSection(
                        value=c["total"],
                        title=f"{percent:.0f}%",
                        color=palette[i % len(palette)],
                        radius=60,
                    )
                )
            pie = fch.PieChart(
                sections=sections,
                sections_space=2,
                center_space_radius=40,
                height=200,
            )
            legend = ft.Column([
                ft.Row([
                    ft.Container(width=12, height=12, bgcolor=palette[i % len(palette)], border_radius=3),
                    ft.Text(f"{c['category']}: {c['total']:,.0f}", size=12),
                ], spacing=6)
                for i, c in enumerate(cat_data)
            ], spacing=4)

            chart_container.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text("سهم دسته‌بندی‌ها از هزینه", size=14, weight=ft.FontWeight.BOLD),
                        ft.Row([pie, legend], alignment=ft.MainAxisAlignment.SPACE_AROUND, wrap=True),
                    ], spacing=8),
                    padding=12, border_radius=10, bgcolor=ft.Colors.WHITE,
                    border=ft.Border.all(1, ft.Colors.GREY_200),
                )
            )
        else:
            chart_container.controls.append(
                ft.Text("برای نمایش نمودار، ابتدا چند هزینه ثبت کنید.", color=ft.Colors.GREY_500)
            )

        # نمودار میله‌ای
        month_data = db.get_monthly_summary()
        if month_data:
            bar_groups = []
            max_val = max(max(m["income"], m["expense"]) for m in month_data) or 1
            for i, m in enumerate(month_data):
                bar_groups.append(
                    fch.BarChartGroup(
                        x=i,
                        rods=[
                            fch.BarChartRod(
                                from_y=0, to_y=m["income"],
                                width=12, color=ft.Colors.GREEN_400,
                                tooltip=f"درآمد: {m['income']:,.0f}",
                                border_radius=3,
                            ),
                            fch.BarChartRod(
                                from_y=0, to_y=m["expense"],
                                width=12, color=ft.Colors.RED_400,
                                tooltip=f"هزینه: {m['expense']:,.0f}",
                                border_radius=3,
                            ),
                        ],
                    )
                )
            bar = fch.BarChart(
                groups=bar_groups,
                group_spacing=20,
                bottom_axis=fch.ChartAxis(
                    labels=[
                        fch.ChartAxisLabel(
                            value=i,
                            label=ft.Text(m["month"][-2:], size=10),
                        )
                        for i, m in enumerate(month_data)
                    ],
                ),
                left_axis=fch.ChartAxis(label_size=50),
                horizontal_grid_lines=fch.ChartGridLines(interval=max_val / 4 if max_val else 1),
                height=220,
            )
            chart_container.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text("روند ماهانه (۶ ماه اخیر)", size=14, weight=ft.FontWeight.BOLD),
                        ft.Row([
                            ft.Row([ft.Container(width=10, height=10, bgcolor=ft.Colors.GREEN_400, border_radius=2),
                                    ft.Text("درآمد", size=11)], spacing=3),
                            ft.Row([ft.Container(width=10, height=10, bgcolor=ft.Colors.RED_400, border_radius=2),
                                    ft.Text("هزینه", size=11)], spacing=3),
                        ], spacing=15),
                        bar,
                    ], spacing=8),
                    padding=12, border_radius=10, bgcolor=ft.Colors.WHITE,
                    border=ft.Border.all(1, ft.Colors.GREY_200),
                )
            )
        else:
            chart_container.controls.append(
                ft.Text("برای نمایش روند، ابتدا تراکنش ثبت کنید.", color=ft.Colors.GREY_500)
            )

    refresh_button = ft.FilledButton(
        content="به‌روزرسانی نمودارها",
        icon=ft.Icons.REFRESH,
        on_click=lambda e: (refresh_reports(), page.update()),
    )

    refresh_reports()

    reports_tab = ft.Column([
        ft.Text("گزارش‌ها و نمودارها", size=16, weight=ft.FontWeight.BOLD),
        refresh_button,
        chart_container,
    ], spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

    # ============ تب آرشیو ============
    archive_keyword = ft.TextField(
        label="جستجو در دسته‌بندی و توضیح",
        prefix_icon=ft.Icons.SEARCH,
        width=340,
    )
    archive_type = ft.Dropdown(
        label="نوع",
        options=[
            ft.dropdown.Option("", "همه"),
            ft.dropdown.Option("income", "درآمد"),
            ft.dropdown.Option("expense", "هزینه"),
        ],
        value="", width=140,
    )
    archive_results = ft.Column(spacing=8)

    def run_archive_search(e=None):
        archive_results.controls.clear()
        rows = db.search_transactions(
            keyword=(archive_keyword.value or "").strip(),
            tx_type=(archive_type.value or None),
        )
        if not rows:
            archive_results.controls.append(ft.Text("نتیجه‌ای یافت نشد.", color=ft.Colors.GREY_500))
        else:
            archive_results.controls.append(
                ft.Text(f"{len(rows)} نتیجه", size=12, color=ft.Colors.GREY_600)
            )
            for row in rows:
                is_income = row["type"] == "income"
                color = ft.Colors.GREEN_700 if is_income else ft.Colors.RED_700
                sign = "+" if is_income else "-"
                card = ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(row["category"], weight=ft.FontWeight.BOLD, size=14),
                            ft.Text(row["note"] or "-", size=12, color=ft.Colors.GREY_600),
                            ft.Text(row["created_at"].replace("T", " "), size=10, color=ft.Colors.GREY_400),
                        ], spacing=2, expand=True),
                        ft.Text(f"{sign}{row['amount']:,.0f}", size=16,
                                weight=ft.FontWeight.BOLD, color=color),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=12, border_radius=10, bgcolor=ft.Colors.WHITE,
                    border=ft.Border.all(1, ft.Colors.GREY_200),
                )
                archive_results.controls.append(card)
        page.update()

    archive_button = ft.FilledButton(
        content="جستجو",
        icon=ft.Icons.SEARCH,
        on_click=run_archive_search,
        width=340,
    )

    run_archive_search()

    archive_tab = ft.Column([
        ft.Text("آرشیو تراکنش‌ها", size=16, weight=ft.FontWeight.BOLD),
        archive_keyword,
        ft.Row([archive_type], alignment=ft.MainAxisAlignment.START),
        archive_button,
        ft.Divider(),
        archive_results,
    ], spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

    # ============ تب یادداشت‌ها ============
    note_category = ft.TextField(
        label="دسته‌بندی",
        hint_text="مثلاً شعر، کامپیوتر، عرفان",
        width=200,
    )
    note_title = ft.TextField(label="عنوان", width=340)
    note_content = ft.TextField(
        label="متن",
        multiline=True,
        min_lines=4,
        max_lines=10,
        width=340,
    )
    note_editing_id = ft.Ref[ft.Text]()  # نگه‌داری شناسه یادداشت در حال ویرایش
    editing_id_value = {"id": None}  # چون Ref برای مقدار ساده مناسب نیست

    # فیلتر جستجو در تب یادداشت‌ها
    note_search = ft.TextField(
        label="جستجو در عنوان و متن",
        prefix_icon=ft.Icons.SEARCH,
        width=240,
    )
    note_filter_category = ft.Dropdown(
        label="دسته‌بندی",
        options=[ft.dropdown.Option("", "همه")],
        value="",
        width=160,
    )
    notes_list = ft.Column(spacing=8)

    def refresh_note_categories():
        """Dropdown دسته‌بندی‌ها را با مقادیر موجود به‌روز می‌کند."""
        cats = db.get_note_categories()
        note_filter_category.options = [ft.dropdown.Option("", "همه")] + [
            ft.dropdown.Option(c, c) for c in cats
        ]

    def refresh_notes(e=None):
        """لیست یادداشت‌ها را با فیلتر فعلی بازسازی می‌کند."""
        notes_list.controls.clear()
        rows = db.get_notes(
            category=(note_filter_category.value or None),
            keyword=(note_search.value or "").strip(),
        )
        if not rows:
            notes_list.controls.append(ft.Text("یادداشتی یافت نشد.", color=ft.Colors.GREY_500))
        else:
            for row in rows:
                card = ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Text(row["category"], size=11, color=ft.Colors.WHITE),
                                bgcolor=ft.Colors.INDIGO_400,
                                padding=ft.Padding.symmetric(vertical=6, horizontal=10),
                                border_radius=12,
                            ),
                            ft.Text(row["title"], weight=ft.FontWeight.BOLD, size=14, expand=True),
                            ft.IconButton(
                                icon=ft.Icons.EDIT_OUTLINED,
                                icon_color=ft.Colors.BLUE_400,
                                tooltip="ویرایش",
                                on_click=lambda e, r=row: load_note_for_edit(r),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE,
                                icon_color=ft.Colors.RED_400,
                                tooltip="حذف",
                                on_click=lambda e, nid=row["id"]: delete_note_click(nid),
                            ),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Text(row["content"], size=12, color=ft.Colors.GREY_700),
                        ft.Text(row["updated_at"].replace("T", " "), size=10, color=ft.Colors.GREY_400),
                    ], spacing=4),
                    padding=12, border_radius=10, bgcolor=ft.Colors.WHITE,
                    border=ft.Border.all(1, ft.Colors.GREY_200),
                )
                notes_list.controls.append(card)
        page.update()

    def load_note_for_edit(row):
        """یادداشت را برای ویرایش در فرم بارگذاری می‌کند."""
        editing_id_value["id"] = row["id"]
        note_category.value = row["category"]
        note_title.value = row["title"]
        note_content.value = row["content"]
        save_note_btn.content = "ذخیره ویرایش"
        save_note_btn.icon = ft.Icons.UPDATE
        page.update()

    def delete_note_click(nid):
        db.delete_note(nid)
        refresh_note_categories()
        refresh_notes()
        page.update()

    def on_save_note(e):
        if not note_category.value or not note_title.value or not note_content.value:
            page.show_dialog(ft.SnackBar(ft.Text("دسته‌بندی، عنوان و متن را پر کنید.")))
            return
        if editing_id_value["id"] is None:
            db.add_note(
                note_category.value.strip(),
                note_title.value.strip(),
                note_content.value.strip(),
            )
            msg = "✅ یادداشت ثبت شد."
        else:
            db.update_note(
                editing_id_value["id"],
                note_category.value.strip(),
                note_title.value.strip(),
                note_content.value.strip(),
            )
            editing_id_value["id"] = None
            msg = "✅ یادداشت ویرایش شد."

        # پاک کردن فرم
        note_category.value = ""
        note_title.value = ""
        note_content.value = ""
        save_note_btn.content = "ثبت یادداشت"
        save_note_btn.icon = ft.Icons.SAVE

        refresh_note_categories()
        refresh_notes()
        page.show_dialog(ft.SnackBar(ft.Text(msg), bgcolor=ft.Colors.GREEN_400))
        page.update()

    save_note_btn = ft.FilledButton(
        content="ثبت یادداشت",
        icon=ft.Icons.SAVE,
        on_click=on_save_note,
        width=340,
    )

    note_search.on_change = refresh_notes
    note_filter_category.on_change = refresh_notes

    refresh_note_categories()
    refresh_notes()

    notes_tab = ft.Column([
        ft.Text("ثبت یادداشت جدید", size=16, weight=ft.FontWeight.BOLD),
        note_category,
        note_title,
        note_content,
        save_note_btn,
        ft.Divider(),
        ft.Text("جستجو و مرور", size=16, weight=ft.FontWeight.BOLD),
        ft.Row([note_search, note_filter_category], alignment=ft.MainAxisAlignment.START, wrap=True),
        notes_list,
    ], spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    # ============ تب‌ها ============
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        length=5,
        content=ft.Column(
            controls=[
                ft.TabBar(
                    tabs=[
                        ft.Tab(label="مالی", icon=ft.Icons.ACCOUNT_BALANCE_WALLET),
                        ft.Tab(label="ملاقات‌ها", icon=ft.Icons.EVENT),
                        ft.Tab(label="یادداشت‌ها", icon=ft.Icons.NOTE_ALT_OUTLINED),
                        ft.Tab(label="گزارش‌ها", icon=ft.Icons.BAR_CHART),
                        ft.Tab(label="آرشیو", icon=ft.Icons.ARCHIVE),
                    ]
                ),
                ft.TabBarView(
                    controls=[
                        finance_tab,
                        meetings_tab,
                        notes_tab,
                        reports_tab,
                        archive_tab,
                    ],
                    expand=True,
                ),
            ],
            expand=True,
        ),
        expand=True,
    )

    page.add(tabs)


ft.run(main)