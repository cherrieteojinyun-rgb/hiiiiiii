import flet as ft
from flet_charts import PieChart, PieChartSection

from components.brand import badge, wordmark
from finance import category_totals, coach_allocation, goal_progress, money
from theme import (BLUE, BLUE_SOFT, CORAL, CORAL_SOFT, INK, MINT,
                   MINT_SOFT, MUTED, PRIMARY, PURPLE_SOFT, SURFACE, YELLOW,
                   YELLOW_SOFT, card, label, primary_button, title)


CATEGORY_STYLE = {
    "Food": (ft.Icons.RESTAURANT, CORAL, CORAL_SOFT),
    "Transport": (ft.Icons.DIRECTIONS_BUS, BLUE, BLUE_SOFT),
    "Fun": (ft.Icons.SENTIMENT_SATISFIED, PRIMARY, PURPLE_SOFT),
    "Books": (ft.Icons.MENU_BOOK, MINT, MINT_SOFT),
    "Other": (ft.Icons.CATEGORY, ft.Colors.BLUE_GREY_500, ft.Colors.BLUE_GREY_50),
}
CATEGORY_LABELS = {
    "Food": "Makanan", "Transport": "Pengangkutan", "Fun": "Hiburan",
    "Books": "Buku", "Other": "Lain-lain",
}
PLAN_STYLE = {
    "Savings goal": PRIMARY,
    "Flexible spend": BLUE,
    "Buffer": MINT,
}
PLAN_LABELS = {
    "Savings goal": "Matlamat simpanan",
    "Flexible spend": "Perbelanjaan fleksibel",
    "Buffer": "Dana kecemasan",
}


def transaction_row(item, on_delete=None):
    icon, color, tint = CATEGORY_STYLE.get(item.get("category", "Fun"), CATEGORY_STYLE["Fun"])
    controls = [
        ft.Container(content=ft.Icon(icon, color=color, size=21), bgcolor=tint, padding=11, border_radius=15),
        ft.Column([label(item.get("description", "Pembelian"), weight=ft.FontWeight.BOLD), label(item.get("date", "Hari ini"), size=12, color=MUTED)], spacing=4, expand=True),
        ft.Text(f"− {money(item.get('amount', 0))}", size=13, color=INK, weight=ft.FontWeight.BOLD),
    ]
    if on_delete:
        controls.append(ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color=CORAL, tooltip="Padam transaksi", on_click=on_delete))
    return ft.Row(controls, spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER)


def overview_card(heading, amount, icon, tint, color, footnote):
    return card(ft.Column([
        ft.Row([ft.Container(content=ft.Icon(icon, color=color, size=18), bgcolor=tint, padding=8, border_radius=12), label(heading, size=12, color=MUTED)], spacing=8),
        ft.Text(money(amount), size=19, color=INK, weight=ft.FontWeight.BOLD),
        label(footnote, size=11, color=MUTED),
    ], spacing=8), padding=13)


def money_chart(mode, allowance, spent, balance, goal, transactions, on_mode):
    if mode == "spending":
        totals = category_totals(transactions)
        recorded = sum(totals.values())
        if spent > recorded:
            totals["Other"] = totals.get("Other", 0) + spent - recorded
        values = [(CATEGORY_LABELS.get(name, name), amount, CATEGORY_STYLE.get(name, CATEGORY_STYLE["Other"])[1]) for name, amount in totals.items() if amount > 0]
        heading = "Ke mana perbelanjaan anda?"
        footnote = "Berdasarkan perbelanjaan yang direkodkan bulan ini."
    else:
        totals = coach_allocation(balance)
        values = [(PLAN_LABELS.get(name, name), amount, PLAN_STYLE[name]) for name, amount in totals.items() if amount > 0]
        heading = "Cadangan pelan untuk baki wang anda"
        footnote = "Pembahagian asas 50 / 30 / 20 yang boleh diubah mengikut keperluan—bukan nasihat kewangan."

    mode_buttons = []
    for key, caption in (("spending", "Perbelanjaan"), ("plan", "Pelan jurulatih")):
        selected = mode == key
        mode_buttons.append(ft.Button(
            content=ft.Text(caption, size=12, weight=ft.FontWeight.BOLD),
            on_click=lambda e, chosen=key: on_mode(chosen),
            bgcolor=PRIMARY if selected else ft.Colors.WHITE,
            color=ft.Colors.WHITE if selected else PRIMARY,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=14), padding=ft.Padding.symmetric(horizontal=15, vertical=10)),
        ))

    if values:
        chart = PieChart(
            sections=[PieChartSection(value=value, color=color, radius=48) for _, value, color in values],
            sections_space=3,
            center_space_radius=34,
            center_space_color=ft.Colors.WHITE,
            width=170,
            height=170,
        )
        legend = ft.Column([
            ft.Row([
                ft.Container(width=10, height=10, bgcolor=color, border_radius=5),
                ft.Column([label(name, size=12, weight=ft.FontWeight.BOLD), label(money(value), size=11, color=MUTED)], spacing=2, expand=True),
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            for name, value, color in values
        ], spacing=8, expand=True)
        graph = ft.Row([chart, legend], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)
    else:
        graph = card(ft.Row([ft.Icon(ft.Icons.PIE_CHART_OUTLINE, color=PRIMARY), label("Tambah elaun atau perbelanjaan untuk melihat carta anda.", size=13, color=MUTED)], spacing=10), color=ft.Colors.PURPLE_50, padding=14)

    return card(ft.Column([
        ft.Row([label("RINGKASAN KEWANGAN ANDA", size=11, color=PRIMARY, weight=ft.FontWeight.BOLD), ft.Container(expand=True), ft.Icon(ft.Icons.PIE_CHART, color=PRIMARY)], spacing=5),
        title(heading, size=18),
        ft.Row(mode_buttons, spacing=8),
        graph,
        label(footnote, size=11, color=MUTED),
    ], spacing=12), color=ft.Colors.WHITE, padding=15)


def home(name, allowance, expenses_total, balance, goal, transactions, chart_mode,
         on_chart_mode, on_add_allowance, on_add, on_coach, on_transactions, on_savings, on_profile, on_shop):
    progress = goal_progress(goal.get("saved", 0), goal.get("target", 1))
    recent = transactions[:3]
    return ft.Column([
        ft.Row([
            wordmark(20),
            ft.Row([
                ft.IconButton(icon=ft.Icons.NOTIFICATIONS_NONE, tooltip="Pemberitahuan", on_click=lambda: None),
                ft.IconButton(icon=ft.Icons.ACCOUNT_CIRCLE, tooltip="Profil", on_click=on_profile),
            ], spacing=2),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ft.Column([
            label("SERONOK BERTEMU ANDA", size=11, color=PRIMARY, weight=ft.FontWeight.BOLD),
            title(f"Hai, {name} 👋", size=27),
            label("Bersedia untuk langkah kewangan seterusnya?", size=13, color=MUTED),
        ], spacing=4),
        ft.Row([
            ft.Container(content=overview_card("Elaun diterima", allowance, ft.Icons.SAVINGS, PURPLE_SOFT, PRIMARY, "bulan ini"), expand=True),
            ft.Container(content=overview_card("Dibelanjakan", expenses_total, ft.Icons.RECEIPT_LONG, CORAL_SOFT, CORAL, "bulan ini"), expand=True),
            ft.Container(content=overview_card("Baki tersedia", balance, ft.Icons.ACCOUNT_BALANCE_WALLET, MINT_SOFT, MINT, "untuk dirancang"), expand=True),
        ], spacing=9, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ft.Row([
            ft.Container(expand=True),
            ft.TextButton(content=ft.Text("Tambah elaun", weight=ft.FontWeight.BOLD), icon=ft.Icons.ADD_CIRCLE_OUTLINE, on_click=on_add_allowance, style=ft.ButtonStyle(color=PRIMARY)),
        ]),
        money_chart(chart_mode, allowance, expenses_total, balance, goal, transactions, on_chart_mode),
        card(ft.Column([
            ft.Row([label("MATLAMAT SIMPANAN SAYA", size=11, color=PRIMARY, weight=ft.FontWeight.BOLD), ft.Icon(ft.Icons.STARS, color=YELLOW, size=20)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Row([
                ft.Container(content=ft.Icon(ft.Icons.HEADPHONES, color=PRIMARY, size=26), bgcolor=PURPLE_SOFT, padding=14, border_radius=18),
                ft.Column([
                    label(goal.get("item", "Impian untuk dibeli"), size=17, weight=ft.FontWeight.BOLD),
                    label(f"{money(goal.get('saved', 0))} daripada {money(goal.get('target', 0))}", size=13, color=MUTED),
                ], spacing=5, expand=True),
                ft.Text(f"{int(progress * 100)}%", size=17, color=PRIMARY, weight=ft.FontWeight.BOLD),
            ], spacing=12),
            ft.ProgressBar(value=progress, color=PRIMARY, bgcolor=PURPLE_SOFT, bar_height=9, border_radius=8),
            ft.Row([label(f"Baki {money(max(goal.get('target', 0) - goal.get('saved', 0), 0))}", size=12, color=MUTED), label(goal.get("target_date", "Sasaran: dalam 3 bulan"), size=12, color=MUTED)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ], spacing=12), color=ft.Colors.WHITE, padding=16),
        ft.Row([
            ft.Text("Aktiviti terkini", size=18, weight=ft.FontWeight.BOLD, color=INK),
            ft.TextButton("Lihat semua", on_click=on_transactions),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        card(ft.Column([
            *[transaction_row(item) for item in recent],
            ft.Container(height=2),
            ft.Button(content=ft.Text("Tambah perbelanjaan", weight=ft.FontWeight.BOLD), icon=ft.Icons.ADD, on_click=on_add, bgcolor=PURPLE_SOFT, color=PRIMARY, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15), padding=ft.Padding.symmetric(horizontal=14, vertical=12))),
        ], spacing=13), padding=14),
        card(ft.Column([
            ft.Row([badge("Jurulatih Wangku"), ft.Container(expand=True), ft.Icon(ft.Icons.AUTO_AWESOME, color=YELLOW)], spacing=5),
            title("Terfikir untuk membeli sesuatu?", size=19),
            label("Ketahui tempoh untuk menggantikan wang yang dibelanjakan dan kembali kepada matlamat simpanan anda.", size=13, color=MUTED),
            primary_button("Tanya Wangku", on_coach, icon=ft.Icons.CHAT_BUBBLE_OUTLINE),
        ], spacing=11), color=ft.Colors.PURPLE_50, padding=16),
        card(ft.Row([
            ft.Container(content=ft.Icon(ft.Icons.SHOPPING_BAG_OUTLINED, color=PRIMARY, size=24), bgcolor=PURPLE_SOFT, padding=12, border_radius=16),
            ft.Column([label("Keperluan sekolah", weight=ft.FontWeight.BOLD), label("Lihat pilihan mesra pelajar.", size=12, color=MUTED)], spacing=4, expand=True),
            ft.TextButton("Lihat kedai", on_click=on_shop),
        ], spacing=10), color=ft.Colors.WHITE, padding=13),
        ft.Container(height=4),
    ], spacing=14, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)


def transactions(transactions_data, on_add, on_scan, on_delete, on_clear):
    rows = [
        transaction_row(item, on_delete=lambda e, i=i: on_delete(i))
        for i, item in enumerate(transactions_data)
    ]
    return ft.Column([
        ft.Button(
            content=ft.Row([
                ft.Container(content=ft.Icon(ft.Icons.CAMERA_ALT, color=PRIMARY, size=23), bgcolor=PURPLE_SOFT, padding=12, border_radius=15),
                ft.Column([label("Imbas resit atau tangkap layar", weight=ft.FontWeight.BOLD), label("Ambil gambar, semak dan kategorikannya.", size=12, color=MUTED)], spacing=4, expand=True),
                ft.Icon(ft.Icons.ARROW_FORWARD_IOS, size=15, color=MUTED),
            ], spacing=12),
            on_click=on_scan,
            bgcolor=ft.Colors.WHITE,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20), padding=ft.Padding.all(12)),
        ),
        ft.Row([
            title("Aktiviti anda", size=28),
            ft.Container(expand=True),
            ft.TextButton("Kosongkan semua", on_click=on_clear, disabled=not rows),
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
        label("Setiap pilihan kecil membawa perubahan.", color=MUTED),
        card(ft.Row([label(f"{len(rows)} transaksi", weight=ft.FontWeight.BOLD), ft.Container(expand=True), label("Bulan ini", size=12, color=MUTED)], spacing=4), padding=14),
        card(ft.Column(rows, spacing=12) if rows else ft.Column([label("Belum ada perbelanjaan—langkah kewangan anda bermula di sini.", color=MUTED)], spacing=10), padding=16),
        primary_button("Tambah perbelanjaan", on_add, icon=ft.Icons.ADD),
    ], spacing=14, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)


def savings(goals, active_index, on_select, on_add, on_edit, on_delete, on_contribute):
    goal_cards = []
    for index, goal in enumerate(goals):
        progress = goal_progress(goal.get("saved", 0), goal.get("target", 1))
        remaining = max(goal.get("target", 0) - goal.get("saved", 0), 0)
        active = index == active_index
        goal_cards.append(card(ft.Column([
            ft.Row([
                ft.Container(content=ft.Icon(ft.Icons.STARS if active else ft.Icons.SAVINGS, size=24, color=PRIMARY), bgcolor=PURPLE_SOFT, padding=11, border_radius=15),
                ft.Column([
                    label(goal.get("item", "Matlamat simpanan"), size=17, weight=ft.FontWeight.BOLD),
                    label(f"{money(goal.get('saved', 0))} disimpan · sasaran {money(goal.get('target', 0))}", size=12, color=MUTED),
                ], spacing=4, expand=True),
                ft.IconButton(icon=ft.Icons.EDIT_OUTLINED, tooltip="Edit matlamat", on_click=lambda e, i=index: on_edit(i)),
                ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color=CORAL, tooltip="Padam matlamat", on_click=lambda e, i=index: on_delete(i)),
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.ProgressBar(value=progress, color=PRIMARY, bgcolor=PURPLE_SOFT, bar_height=10, border_radius=9),
            ft.Row([
                label(f"Baki {money(remaining)}", size=12, color=MUTED),
                ft.Container(expand=True),
                label(goal.get("target_date", "Teruskan usaha"), size=12, color=MUTED),
            ]),
            ft.Button(
                content=ft.Text("Matlamat pilihan" if active else "Jadikan matlamat utama", weight=ft.FontWeight.BOLD),
                disabled=active,
                on_click=lambda e, i=index: on_select(i),
                bgcolor=PURPLE_SOFT if active else ft.Colors.WHITE,
                color=PRIMARY,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=14), padding=ft.Padding.symmetric(horizontal=14, vertical=10)),
            ),
        ], spacing=11), color=ft.Colors.WHITE, padding=16))

    content = goal_cards or [card(ft.Column([
        ft.Container(content=ft.Icon(ft.Icons.SAVINGS, size=32, color=PRIMARY), bgcolor=PURPLE_SOFT, padding=14, border_radius=18),
        label("Belum ada matlamat simpanan", size=17, weight=ft.FontWeight.BOLD),
        label("Tambah matlamat supaya simpanan anda ada tujuan.", size=13, color=MUTED),
    ], spacing=9), color=ft.Colors.WHITE, padding=18)]
    return ft.Column([
        title("Simpanan anda", size=28),
        label("Tambah simpanan dan jumlahnya akan dibahagi sama rata antara matlamat yang belum dicapai.", color=MUTED),
        *content,
        primary_button("Tambah simpanan", on_contribute, icon=ft.Icons.ADD),
        ft.OutlinedButton(content=ft.Text("Cipta matlamat baharu"), icon=ft.Icons.ADD_CIRCLE_OUTLINE, on_click=on_add),
        card(ft.Row([ft.Icon(ft.Icons.LIGHTBULB, color=YELLOW, size=24), ft.Column([label("Tip ringkas", weight=ft.FontWeight.BOLD), label("Cuba asingkan sedikit wang sebaik sahaja elaun diterima.", size=13, color=MUTED)], spacing=4, expand=True)], spacing=12), color=YELLOW_SOFT),
    ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)


def coach(messages, prompt, on_send, name, busy=False, error="", on_settings=None):
    async def ask_purchase(e):
        await on_send(suggested="Mampukah saya membeli sesuatu? Bantu saya menilai kemampuan saya.")

    async def ask_savings(e):
        await on_send(suggested="Bantu saya merancang simpanan berdasarkan kedudukan kewangan saya.")

    if not messages:
        messages = [("coach", f"Hai {name}! Saya sedia membantu anda membuat keputusan pembelian atau merancang simpanan. Apa yang bermain di fikiran anda?")]
    message_controls = []
    for sender, text in messages:
        mine = sender == "you"
        message_controls.append(ft.Row([
            ft.Container(content=ft.Text(text, size=14, color=ft.Colors.WHITE if mine else INK), bgcolor=PRIMARY if mine else ft.Colors.WHITE, padding=14, border_radius=18, width=290),
        ], alignment=ft.MainAxisAlignment.END if mine else ft.MainAxisAlignment.START))
    return ft.Column([
        ft.Row([wordmark(18), badge("sedia membantu")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        title("Jurulatih Wangku", size=27),
        ft.TextButton("Tetapan AI", on_click=on_settings, disabled=busy),
        label("Ruang selesa untuk memikirkan keputusan kewangan anda.", size=13, color=MUTED),
        card(ft.Column(message_controls, spacing=12), color=ft.Colors.PURPLE_50, padding=14),
        label("Cuba tanya", size=12, color=MUTED, weight=ft.FontWeight.BOLD),
        ft.Row([
            ft.OutlinedButton(content=ft.Text("Mampukah saya membelinya?"), on_click=ask_purchase, disabled=busy),
            ft.OutlinedButton(content=ft.Text("Bantu saya menyimpan"), on_click=ask_savings, disabled=busy),
        ], wrap=True, spacing=8),
        ft.Text("Wangku sedang menyediakan jawapan…", visible=busy, color=PRIMARY),
        ft.ProgressBar(visible=busy, color=PRIMARY),
        ft.Text(error, visible=bool(error), color=CORAL),
        ft.Row([prompt, ft.IconButton(icon=ft.Icons.SEND, icon_color=PRIMARY, tooltip="Hantar", on_click=on_send, disabled=busy)], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        label("Soalan dan ringkasan kewangan dihantar kepada Google Gemini. Elakkan maklumat peribadi. Jawapan AI mungkin tersilap; semak pengiraan penting.", size=11, color=MUTED),
    ], spacing=13, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)


def profile(name, role, on_logout, on_reset):
    role_label = "Pentadbir" if role == "Admin" else "Pelajar"
    return ft.Column([
        title("Profil anda", size=28),
        label("Ruang Wangku anda.", color=MUTED),
        card(ft.Column([
            ft.Container(content=ft.Icon(ft.Icons.PERSON, size=34, color=PRIMARY), bgcolor=PURPLE_SOFT, padding=16, border_radius=50),
            title(name, size=22),
            label(f"Akaun {role_label}", size=13, color=MUTED),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8), color=ft.Colors.WHITE, padding=22),
        card(ft.Column([
            ft.ListTile(title=label("Keutamaan kewangan saya"), leading=ft.Icon(ft.Icons.TUNE, color=PRIMARY), trailing=ft.Icon(ft.Icons.ARROW_FORWARD_IOS, size=14, color=MUTED)),
            ft.ListTile(title=label("Privasi dan keselamatan"), leading=ft.Icon(ft.Icons.SHIELD_OUTLINED, color=MINT), trailing=ft.Icon(ft.Icons.ARROW_FORWARD_IOS, size=14, color=MUTED)),
            ft.ListTile(title=label("Tentang Wangku"), leading=ft.Icon(ft.Icons.INFO_OUTLINE, color=BLUE), trailing=ft.Icon(ft.Icons.ARROW_FORWARD_IOS, size=14, color=MUTED)),
        ], spacing=0), padding=8),
        ft.TextButton("Mulakan semula panduan awal", on_click=on_reset),
        ft.OutlinedButton(content=ft.Text("Log keluar"), icon=ft.Icons.LOGOUT, on_click=on_logout),
    ], spacing=14, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)


def admin_home(name, on_logout):
    return ft.Column([
        wordmark(22),
        title(f"Helo, {name}", size=27),
        label("Pratonton pentadbir", color=MUTED),
        card(ft.Column([
            ft.Container(content=ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS, color=BLUE, size=30), bgcolor=BLUE_SOFT, padding=14, border_radius=18),
            title("Alatan komuniti", size=20),
            label("Pratonton ini mengehadkan akses pentadbir. Sambungkan pelayan backend yang disahkan sebelum mengaktifkan pengurusan pengguna atau data kewangan.", size=13, color=MUTED),
        ], spacing=12), color=ft.Colors.WHITE),
        ft.OutlinedButton(content=ft.Text("Log keluar"), icon=ft.Icons.LOGOUT, on_click=on_logout),
    ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
