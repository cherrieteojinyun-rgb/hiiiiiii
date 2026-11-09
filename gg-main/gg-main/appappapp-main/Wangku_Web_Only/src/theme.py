import flet as ft


BG = ft.Colors.WHITE
SURFACE = ft.Colors.WHITE
INK = ft.Colors.INDIGO_900
MUTED = ft.Colors.BLUE_GREY_500
PRIMARY = ft.Colors.PURPLE_700
PURPLE_SOFT = ft.Colors.PURPLE_100
LAVENDER = ft.Colors.PURPLE_50
BLUE = ft.Colors.BLUE_600
BLUE_SOFT = ft.Colors.BLUE_50
MINT = ft.Colors.GREEN_600
MINT_SOFT = ft.Colors.GREEN_50
YELLOW = ft.Colors.AMBER_400
YELLOW_SOFT = ft.Colors.AMBER_50
CORAL = ft.Colors.DEEP_ORANGE_400
CORAL_SOFT = ft.Colors.DEEP_ORANGE_50
BORDER = ft.Colors.BLUE_GREY_50
HEADING_FONT = "Roboto"
BODY_FONT = "Roboto"


def label(text, *, size=14, color=INK, weight=ft.FontWeight.NORMAL):
    return ft.Text(text, size=size, color=color, weight=weight, font_family=BODY_FONT)


def title(text, *, size=26, color=INK):
    return ft.Text(text, size=size, color=color, weight=ft.FontWeight.W_800, font_family=HEADING_FONT)


def card(content, *, color=SURFACE, padding=18, border_color=BORDER):
    return ft.Container(
        content=content,
        padding=padding,
        bgcolor=color,
        border_radius=22,
        border=ft.Border.all(1, border_color),
    )


def primary_button(text, on_click, *, icon=None):
    return ft.Button(
        content=ft.Text(text, weight=ft.FontWeight.BOLD),
        icon=icon,
        on_click=on_click,
        bgcolor=PRIMARY,
        color=ft.Colors.WHITE,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=16), padding=ft.Padding.symmetric(horizontal=22, vertical=15)),
    )
