import flet as ft

from theme import INK, PRIMARY, label


def wordmark(size=23, color=INK):
    return ft.Row(
        controls=[
            ft.Image(src="money_mark.svg", width=42, height=42),
            ft.Text("Wangku", size=size, weight=ft.FontWeight.BOLD, color=color),
        ],
        spacing=9,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


def mascot(size=150):
    return ft.Image(src="mind_mascot.svg", width=size, height=size, fit=ft.BoxFit.CONTAIN)


def badge(text="Jurulatih Wangku"):
    return ft.Container(
        content=ft.Row(
            controls=[ft.Icon(ft.Icons.AUTO_AWESOME, color=PRIMARY, size=16), label(text, size=12, color=PRIMARY, weight=ft.FontWeight.BOLD)],
            spacing=6,
            tight=True,
        ),
        padding=ft.Padding.symmetric(horizontal=12, vertical=7),
        bgcolor=ft.Colors.PURPLE_50,
        border_radius=20,
    )
