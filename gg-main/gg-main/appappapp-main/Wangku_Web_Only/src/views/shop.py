import flet as ft

from finance import money
from shop_data import PRODUCTS
from theme import INK, MUTED, PRIMARY, PURPLE_SOFT, YELLOW_SOFT, card, label, title


def screen(on_back):
    products = []
    for product in PRODUCTS:
        products.append(card(ft.Row([
            ft.Image(src=product["image"], width=96, height=96, fit=ft.BoxFit.CONTAIN),
            ft.Column([
                ft.Container(content=label(product["tag"], size=10, color=PRIMARY, weight=ft.FontWeight.BOLD), bgcolor=PURPLE_SOFT, padding=ft.Padding.symmetric(horizontal=9, vertical=5), border_radius=12, width=110),
                label(product["name"], size=16, weight=ft.FontWeight.BOLD),
                label(product["description"], size=12, color=MUTED),
                ft.Row([
                    ft.Text(money(product["price"]), size=16, color=INK, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    ft.Button(content=ft.Text("Akan datang"), disabled=True, bgcolor=YELLOW_SOFT, color=PRIMARY, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=13), padding=ft.Padding.symmetric(horizontal=10, vertical=9))),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ], spacing=7, expand=True),
        ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER), padding=13))
    return ft.Column([
        ft.TextButton("←  Kembali ke Wangku", on_click=on_back),
        title("Keperluan sekolah", size=27),
        label("Alat kecil untuk hari pembelajaran yang hebat.", color=MUTED),
        card(ft.Row([
            ft.Icon(ft.Icons.SHOPPING_BAG_OUTLINED, color=PRIMARY, size=25),
            ft.Column([label("Kedai mesra pelajar", weight=ft.FontWeight.BOLD), label("Lihat pilihan kami. Pesanan akan tersedia tidak lama lagi.", size=12, color=MUTED)], spacing=4, expand=True),
        ], spacing=12), color=ft.Colors.PURPLE_50),
        *products,
    ], spacing=13, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
