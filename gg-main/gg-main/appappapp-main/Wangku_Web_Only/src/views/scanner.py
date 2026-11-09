import flet as ft

from theme import (
    CORAL,
    CORAL_SOFT,
    MUTED,
    PRIMARY,
    PURPLE_SOFT,
    card,
    label,
    primary_button,
    title,
)


def live(camera, status, on_capture, on_cancel):
    return ft.Column(
        [
            ft.TextButton("←  Kembali ke transaksi", on_click=on_cancel),
            title("Imbas resit", size=27),
            label(
                "Halakan kamera ke resit atau tangkap skrin pembelian anda.",
                color=MUTED,
            ),
            card(ft.Column([camera, status], spacing=10), padding=10),
            card(
                ft.Row(
                    [
                        ft.Icon(ft.Icons.INFO_OUTLINE, color=PRIMARY),
                        label(
                            "Gambar resit dihantar kepada Gemini untuk analisis automatik. "
                            "Semak cadangan sebelum menyimpan.",
                            size=12,
                            color=MUTED,
                        ),
                    ],
                    spacing=9,
                ),
                color=PURPLE_SOFT,
                padding=12,
            ),
            primary_button("Ambil gambar", on_capture, icon=ft.Icons.CAMERA_ALT),
        ],
        spacing=14,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )


def review(
    photo,
    items,
    message,
    on_add_item,
    on_save,
    on_retake,
    on_cancel,
    busy=False,
):
    if busy:
        return ft.Column(
            [
                ft.TextButton("←  Kembali ke transaksi", on_click=on_cancel),
                title("Analisis resit", size=27),
                message,
                ft.ProgressBar(),
            ],
            spacing=14,
        )

    item_cards = []
    for index, item in enumerate(items):
        fields = [item["description"], item["amount"], item["category"]]
        item_cards.append(
            card(
                ft.Column(
                    [
                        label(
                            f"Butiran {index + 1}",
                            size=15,
                            weight=ft.FontWeight.BOLD,
                        ),
                        *fields,
                    ],
                    spacing=10,
                ),
                color=ft.Colors.WHITE,
                padding=14,
            )
        )

    return ft.Column(
        [
            ft.TextButton("←  Kembali ke transaksi", on_click=on_cancel),
            title("Semak pembelian anda", size=27),
            label(
                "Semak keterangan, jumlah dan kategori sebelum menyimpan.",
                color=MUTED,
            ),
            card(
                ft.Image(
                    src=photo,
                    height=185,
                    fit=ft.BoxFit.CONTAIN,
                    border_radius=16,
                ),
                color=ft.Colors.WHITE,
                padding=10,
            ),
            ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.EDIT_NOTE, color=CORAL),
                        label(
                            "Gambar berjaya diambil. Sila isi atau betulkan "
                            "butiran di bawah.",
                            size=12,
                            color=CORAL,
                        ),
                    ],
                    spacing=8,
                ),
                bgcolor=CORAL_SOFT,
                padding=12,
                border_radius=16,
            ),
            card(
                ft.Column(
                    [
                        label("Butiran transaksi", size=16, weight=ft.FontWeight.BOLD),
                        *item_cards,
                        message,
                    ],
                    spacing=12,
                ),
                color=ft.Colors.WHITE,
                padding=16,
            ),
            ft.OutlinedButton(
                content=ft.Text("Tambah butiran transaksi"),
                icon=ft.Icons.ADD,
                on_click=on_add_item,
            ),
            ft.Row(
                [
                    ft.OutlinedButton(
                        content=ft.Text("Ambil semula"),
                        icon=ft.Icons.CAMERA_ALT,
                        on_click=on_retake,
                    ),
                    ft.Container(expand=True),
                    primary_button(
                        "Simpan transaksi",
                        on_save,
                        icon=ft.Icons.CHECK,
                    ),
                ],
                wrap=True,
                spacing=8,
            ),
        ],
        spacing=13,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )
