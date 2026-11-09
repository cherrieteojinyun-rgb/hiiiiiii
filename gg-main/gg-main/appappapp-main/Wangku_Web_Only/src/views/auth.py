import flet as ft

from components.brand import wordmark
from theme import INK, MUTED, PRIMARY, PURPLE_SOFT, card, label, primary_button, title


def welcome(username, password, message, on_login, on_register, on_demo):
    return ft.Column(
        controls=[
            wordmark(24),
            ft.Container(height=2),
            ft.Text("Wang anda. Masa depan anda.", size=30, weight=ft.FontWeight.BOLD, color=INK),
            label("Langkah kecil, masa depan gemilang.", color=MUTED),
            ft.Container(height=4),
            card(ft.Column([
                ft.Text("Selamat kembali", size=21, weight=ft.FontWeight.BOLD, color=INK),
                label("Langkah kewangan anda yang seterusnya bermula di sini.", size=13, color=MUTED),
                ft.Container(height=2),
                username,
                password,
                message,
                primary_button("Log masuk", on_login, icon=ft.Icons.ARROW_FORWARD),
                ft.Row([
                    label("Baharu di Wangku?", size=13, color=MUTED),
                    ft.TextButton("Cipta akaun", on_click=on_register, style=ft.ButtonStyle(color=PRIMARY)),
                ], alignment=ft.MainAxisAlignment.CENTER, wrap=True),
            ], spacing=9, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)),
            ft.Container(height=2),
            ft.Button(
                content=ft.Text("Lihat-lihat dahulu", weight=ft.FontWeight.BOLD),
                icon=ft.Icons.AUTO_AWESOME,
                on_click=on_demo,
                bgcolor=PURPLE_SOFT,
                color=PRIMARY,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=16), padding=ft.Padding.symmetric(horizontal=18, vertical=13)),
            ),
            ft.Row([ft.Icon(ft.Icons.LOCK_OUTLINE, size=14, color=MUTED), label("Prototaip mesra pelajar. Akaun bank sebenar tidak disambungkan.", size=11, color=MUTED)], spacing=7),
        ], spacing=9, horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )


def registration(username, password, message, on_back, on_create):
    return ft.Column([
        ft.TextButton("←  Kembali ke log masuk", on_click=on_back),
        wordmark(22),
        ft.Container(height=2),
        ft.Container(content=label("AKAUN PELAJAR", size=11, color=PRIMARY, weight=ft.FontWeight.BOLD), bgcolor=PURPLE_SOFT, padding=ft.Padding.symmetric(horizontal=12, vertical=8), border_radius=14, width=150),
        title("Mari mulakan", size=27),
        label("Pilih nama pengguna dan kata laluan untuk bermula.", color=MUTED),
        username,
        password,
        message,
        primary_button("Cipta akaun saya", on_create, icon=ft.Icons.ARROW_FORWARD),
    ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
