import flet as ft

from finance import money, monthly_allowance, number
from theme import (BLUE, BLUE_SOFT, CORAL, INK, MINT, MINT_SOFT, MUTED,
                   PRIMARY, PURPLE_SOFT, SURFACE, YELLOW, YELLOW_SOFT, card,
                   label, primary_button, title)


def onboarding(step, values, on_back, on_next, on_frequency, on_finish):
    step_titles = ["Elaun saya", "Matlamat simpanan saya", "Impian yang ingin dibeli"]
    header = ft.Column([
        ft.TextButton("←  Kembali", on_click=on_back),
        ft.Row([ft.Text(f"{step + 1:02d}", size=13, color=PRIMARY, weight=ft.FontWeight.BOLD), label("  DARIPADA 03", size=12, color=MUTED)], spacing=2),
        ft.ProgressBar(value=(step + 1) / 3, color=PRIMARY, bgcolor=PURPLE_SOFT, border_radius=8),
        title(step_titles[step], size=27),
    ], spacing=10)

    if step == 0:
        amount = ft.TextField(
            label="Jumlah dalam RM", value=values.get("allowance", ""), prefix=ft.Text("RM "),
            keyboard_type=ft.KeyboardType.NUMBER, text_size=22, text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
            border_radius=16, on_change=lambda e: values.update({"allowance": e.control.value}),
        )
        frequency_controls = []
        for freq, caption in (("Weekly", "Mingguan"), ("Monthly", "Bulanan")):
            selected = values.get("frequency", "Weekly") == freq
            frequency_controls.append(ft.Button(
                content=ft.Text(caption, weight=ft.FontWeight.BOLD),
                on_click=lambda e, f=freq: on_frequency(f),
                bgcolor=PRIMARY if selected else ft.Colors.WHITE,
                color=ft.Colors.WHITE if selected else PRIMARY,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=14), padding=ft.Padding.symmetric(horizontal=22, vertical=13)),
            ))
        content = [
            label("Biasanya, berapa jumlah wang yang anda terima?", size=16),
            amount,
            label("Berapa kerap anda menerimanya?", size=13, color=MUTED),
            ft.Row(frequency_controls, spacing=10),
            card(ft.Row([ft.Icon(ft.Icons.TIPS_AND_UPDATES, color=YELLOW, size=20), label("Tiada penghakiman—ini cuma titik permulaan anda.", size=13)], spacing=10), color=YELLOW_SOFT, padding=13),
            primary_button("Seterusnya: matlamat simpanan", on_next, icon=ft.Icons.ARROW_FORWARD),
        ]
    elif step == 1:
        target = ft.TextField(
            label="Jumlah matlamat simpanan (RM)", value=values.get("savings_target", ""), prefix=ft.Text("RM "),
            keyboard_type=ft.KeyboardType.NUMBER, text_size=22, text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
            border_radius=16, on_change=lambda e: values.update({"savings_target": e.control.value}),
        )
        saved = ft.TextField(
            label="Jumlah yang sudah disimpan (RM)", value=values.get("saved", "0"), prefix=ft.Text("RM "),
            keyboard_type=ft.KeyboardType.NUMBER, border_radius=16,
            on_change=lambda e: values.update({"saved": e.control.value}),
        )
        content = [
            label("Berapakah jumlah yang ingin anda simpan?", size=16),
            target,
            saved,
            card(ft.Row([
                ft.Container(content=ft.Icon(ft.Icons.SAVINGS, color=PRIMARY, size=24), bgcolor=PURPLE_SOFT, padding=12, border_radius=16),
                ft.Column([label("Matlamat ialah garisan penamat.", weight=ft.FontWeight.BOLD), label("Simpanan sedia ada memberi anda permulaan—kedua-duanya penting.", size=12, color=MUTED)], spacing=4, expand=True),
            ], spacing=12), padding=14),
            ft.Row([ft.Container(width=22, height=22, bgcolor=PURPLE_SOFT, border_radius=8), ft.Container(width=44, height=22, bgcolor=ft.Colors.PURPLE_300, border_radius=8), ft.Container(width=72, height=22, bgcolor=PRIMARY, border_radius=8), ft.Icon(ft.Icons.FLAG, color=YELLOW)], spacing=8),
            primary_button("Seterusnya: impian saya", on_next, icon=ft.Icons.ARROW_FORWARD),
        ]
    else:
        item = ft.TextField(
            label="Apakah yang ingin anda simpan?", value=values.get("dream_item", ""), hint_text="cth. fon kepala baharu",
            border_radius=16, on_change=lambda e: values.update({"dream_item": e.control.value}),
        )
        price = ft.TextField(
            label="Anggaran harga (RM)", value=values.get("dream_price", ""), prefix=ft.Text("RM "),
            keyboard_type=ft.KeyboardType.NUMBER, border_radius=16,
            on_change=lambda e: values.update({"dream_price": e.control.value}),
        )
        months = ft.TextField(
            label="Saya ingin membelinya dalam (bulan)", value=values.get("months", "3"),
            keyboard_type=ft.KeyboardType.NUMBER, border_radius=16,
            on_change=lambda e: values.update({"months": e.control.value}),
        )
        allow = number(values.get("allowance")) or 0
        monthly = monthly_allowance(allow, values.get("frequency", "Weekly"))
        goal_price = number(values.get("dream_price")) or 0
        existing = number(values.get("saved")) or 0
        term = number(values.get("months")) or 0
        needed = max(goal_price - existing, 0) / term if term else 0
        note = None
        if term and monthly and needed > monthly * 0.75:
            note = card(ft.Row([
                ft.Icon(ft.Icons.FAVORITE, color=CORAL, size=20),
                ft.Column([label("Agak mencabar—dan itu tidak mengapa.", weight=ft.FontWeight.BOLD), label("Cuba tempoh lebih panjang atau simpan sedikit demi sedikit. Anda boleh mengubahnya bila-bila masa.", size=12, color=MUTED)], spacing=3, expand=True),
            ], spacing=10), color=ft.Colors.DEEP_ORANGE_50, padding=13)
        preview = card(ft.Row([
            ft.Container(content=ft.Icon(ft.Icons.STARS, color=YELLOW, size=25), bgcolor=YELLOW_SOFT, padding=12, border_radius=16),
            ft.Column([label(values.get("dream_item") or "Impian anda", weight=ft.FontWeight.BOLD), label(f"{money(goal_price)}  ·  {int(term) if term else 0} bulan", size=12, color=MUTED)], spacing=4, expand=True),
        ], spacing=12), color=ft.Colors.WHITE, padding=14)
        content = [
            label("Apakah satu perkara yang ingin anda simpan?", size=16),
            item, price, months, preview,
        ]
        if note:
            content.append(note)
        content.extend([
            card(ft.Row([ft.Icon(ft.Icons.AUTO_AWESOME, color=PRIMARY), label("Pelan anda, ikut kemampuan anda. Kami bantu anda kekal di landasan.", size=13)], spacing=8), color=ft.Colors.PURPLE_50, padding=13),
            primary_button("Mari mulakan", on_finish, icon=ft.Icons.ARROW_FORWARD),
        ])

    return ft.Column([header, *content], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
