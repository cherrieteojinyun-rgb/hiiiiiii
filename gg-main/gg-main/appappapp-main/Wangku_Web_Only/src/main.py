import asyncio
import math
import hashlib
import json
import logging

import flet as ft
import flet_camera as fcam

from ai_coach import CoachError, analyze_receipt, check_backend, reply
from components.brand import mascot, wordmark
from finance import distribute_savings, money, number
from storage import LocalStore
from theme import BG, INK, MUTED, PRIMARY, PURPLE_SOFT, SURFACE, label
from views import auth, dashboard, onboarding, scanner, shop

LOG_LEVEL = logging.INFO
logging.basicConfig(format="%(levelname)s %(name)s: %(message)s")
logging.getLogger("app").setLevel(LOG_LEVEL)
log = logging.getLogger("app.main")

CATEGORY_OPTIONS = {
    "Makanan": "Food",
    "Pengangkutan": "Transport",
    "Hiburan": "Fun",
    "Buku": "Books",
    "Lain-lain": "Other",
}
DEFAULT_BACKEND_URL = "https://appappapp-3.onrender.com"


async def main(page: ft.Page):
    page.title = "Wangku"
    page.bgcolor = BG
    page.padding = 18
    page.spacing = 0
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    store = LocalStore()

    state = {
        "route": "welcome",
        "role": "Student",
        "name": "Pelajar",
        "tab": "Home",
        "allowance": 600.0,
        "allowance_additions": 0.0,
        "spent": 284.50,
        "balance": 315.50,
        "frequency": "Monthly",
        "goal": {"item": "Fon kepala tanpa wayar", "saved": 360.0, "target": 1200.0, "target_date": "Sasaran: dalam 3 bulan"},
        "transactions": [
            {"description": "Nasi ayam", "category": "Food", "date": "Hari ini · 12:40", "amount": 12.50},
            {"description": "Tambah nilai bas", "category": "Transport", "date": "Semalam", "amount": 8.00},
            {"description": "Barang kelab seni", "category": "Books", "date": "Isn, 18 Mac", "amount": 24.90},
            {"description": "Matcha ais", "category": "Food", "date": "Aha, 17 Mac", "amount": 9.50},
            {"description": "Tonton wayang", "category": "Fun", "date": "Jum, 15 Mac", "amount": 22.00},
            {"description": "Barang dapur", "category": "Food", "date": "Kha, 14 Mac", "amount": 80.00},
            {"description": "Buku ulang kaji peperiksaan", "category": "Books", "date": "Rab, 13 Mac", "amount": 38.00},
            {"description": "Tambang kereta api", "category": "Transport", "date": "Sel, 12 Mac", "amount": 30.00},
            {"description": "Snek belajar", "category": "Food", "date": "Isn, 11 Mac", "amount": 25.00},
            {"description": "Lawatan kelab", "category": "Fun", "date": "Sab, 9 Mac", "amount": 34.60},
        ],
        "chat": [],
        "backend_url": DEFAULT_BACKEND_URL,
        "backend_token": "",
        "coach_busy": False,
        "coach_error": "",
        "coach_session": 0,
        "chart_mode": "spending",
        "camera": None,
        "camera_ready": False,
        "camera_status": None,
        "receipt_photo": None,
        "receipt_message": None,
        "onboarding": {"allowance": "", "frequency": "Weekly", "savings_target": "", "saved": "0", "dream_item": "", "dream_price": "", "months": "3"},
    }
    state["goals"] = [dict(state["goal"])]
    state["active_goal_index"] = 0

    username_field = ft.TextField(label="Nama pengguna", prefix_icon=ft.Icons.PERSON_OUTLINE, border_radius=15, text_size=15, autofocus=False)
    login_password = ft.TextField(label="Kata laluan", prefix_icon=ft.Icons.LOCK_OUTLINE, password=True, can_reveal_password=True, border_radius=15, text_size=15, on_submit=lambda e: asyncio.create_task(login()))
    login_message = ft.Text("", color=ft.Colors.ERROR, size=13, visible=False)
    register_user = ft.TextField(label="Pilih nama pengguna", prefix_icon=ft.Icons.PERSON_OUTLINE, border_radius=15, text_size=15)
    register_password = ft.TextField(label="Cipta kata laluan (sekurang-kurangnya 6 aksara)", prefix_icon=ft.Icons.LOCK_OUTLINE, password=True, can_reveal_password=True, border_radius=15, text_size=15)
    register_message = ft.Text("", color=ft.Colors.ERROR, size=13, visible=False)
    onboard_fields = {}
    logged_in = False

    def allowance_additions_key():
        username = (state.get("name") or "demo").strip().casefold()
        return f"allowance_additions_{username}"

    def content_width():
        available = page.width or 440
        max_width = 720 if state["route"] == "app" else 520
        return max(290, min(available - 36, max_width))

    def nav_bar():
        tabs = [
            ("Home", "Utama", ft.Icons.HOME_OUTLINED),
            ("Transactions", "Transaksi", ft.Icons.RECEIPT_LONG),
            ("Savings", "Simpanan", ft.Icons.SAVINGS),
            ("Coach", "Jurulatih", ft.Icons.AUTO_AWESOME),
            ("Shop", "Kedai", ft.Icons.STORE),
            ("Profile", "Profil", ft.Icons.ACCOUNT_CIRCLE_OUTLINED),
        ]
        buttons = []
        for tab, caption, icon in tabs:
            selected = state["tab"] == tab
            buttons.append(ft.Container(
                content=ft.Column([
                    ft.Icon(icon, size=20, color=PRIMARY if selected else MUTED),
                    ft.Text(caption, size=10, color=PRIMARY if selected else MUTED, weight=ft.FontWeight.BOLD if selected else ft.FontWeight.NORMAL),
                ], spacing=3, horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True),
                bgcolor=PURPLE_SOFT if selected else ft.Colors.TRANSPARENT,
                padding=ft.Padding.symmetric(horizontal=10, vertical=8),
                border_radius=16,
                on_click=lambda e, chosen=tab: select_tab(chosen),
                expand=True,
            ))
        return ft.Container(content=ft.Row(buttons, alignment=ft.MainAxisAlignment.SPACE_AROUND), padding=ft.Padding.symmetric(vertical=5), bgcolor=ft.Colors.WHITE, border=ft.Border.only(top=ft.BorderSide(1, ft.Colors.BLUE_GREY_50)))

    def page_wrapper(view, width=None, include_nav=False):
        screen_width = width if width else content_width()
        if isinstance(view, ft.Column):
            content = ft.Column(
                controls=view.controls,
                spacing=view.spacing,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                tight=True,
            )
        else:
            content = ft.Column([view], spacing=0, tight=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
        body = ft.ListView(
            controls=[ft.Container(content=content, width=screen_width)],
            spacing=0,
            expand=True,
        )
        elements = [body]
        if include_nav:
            elements.append(nav_bar())
        viewport_height = max((page.height or 620) - 36, 320)
        return ft.Row([
            ft.Container(
                content=ft.Column(elements, spacing=8, expand=True),
                width=screen_width,
                height=viewport_height,
                bgcolor=ft.Colors.WHITE,
            ),
        ], alignment=ft.MainAxisAlignment.CENTER, expand=True, vertical_alignment=ft.CrossAxisAlignment.STRETCH)

    def render():
        page.clean()
        route = state["route"]
        page.bgcolor = ft.Colors.WHITE
        log.debug("Rendering route=%s tab=%s viewport=%sx%s", route, state.get("tab"), page.width, page.height)
        if route == "welcome":
            view = auth.welcome(username_field, login_password, login_message, login, begin_registration, demo)
            page.add(page_wrapper(view))
        elif route == "register":
            page.add(page_wrapper(auth.registration(register_user, register_password, register_message, back_to_welcome, create_account)))
        elif route == "onboarding":
            page.add(page_wrapper(onboarding.onboarding(
                state["onboarding_step"], state["onboarding"], onboarding_back, onboarding_next,
                set_frequency, finish_onboarding,
            )))
        elif route == "admin":
            page.add(page_wrapper(dashboard.admin_home(state["name"], logout)))
        elif route == "scanner":
            view = scanner.live(state["camera"], state["camera_status"], capture_photo, close_scanner)
            page.add(page_wrapper(view, width=content_width()))
        elif route == "receipt_review":
            view = scanner.review(
                state["receipt_photo"],
                state["receipt_items"],
                state["receipt_message"],
                add_receipt_item,
                save_receipt,
                retake_receipt,
                close_scanner,
                state.get("receipt_busy", False),
            )
            page.add(page_wrapper(view, width=content_width()))
        elif route == "app":
            tab = state["tab"]
            if tab == "Home":
                view = dashboard.home(
                    state["name"], state["allowance"], state["spent"], state["balance"],
                    state["goal"], state["transactions"], state["chart_mode"], set_chart_mode,
                    add_allowance, add_expense, open_coach, lambda: select_tab("Transactions"),
                    lambda: select_tab("Savings"), lambda: select_tab("Profile"), lambda: select_tab("Shop"),
                )
            elif tab == "Transactions":
                view = dashboard.transactions(
                    state["transactions"], add_expense, open_scanner,
                    delete_transaction, clear_transactions,
                )
            elif tab == "Savings":
                view = dashboard.savings(
                    state["goals"], state["active_goal_index"], select_goal,
                    add_goal, edit_goal, delete_goal, add_savings_contribution,
                )
            elif tab == "Coach":
                prompt = ft.TextField(hint_text="Tanya tentang pembelian atau matlamat…", border_radius=18, expand=True, on_submit=send_message, disabled=state["coach_busy"])
                view = dashboard.coach(state["chat"], prompt, send_message, state["name"], state["coach_busy"], state["coach_error"], configure_ai)
                state["coach_prompt"] = prompt
            elif tab == "Shop":
                view = shop.screen(lambda: select_tab("Home"))
            else:
                view = dashboard.profile(state["name"], state["role"], logout, restart_onboarding)
            page.add(page_wrapper(view, width=content_width(), include_nav=True))
        page.update()

    def begin_registration():
        log.debug("Create account selected; opening student registration")
        login_message.value = ""
        login_message.visible = False
        state["role"] = "Student"
        state["route"] = "register"
        register_message.value = ""
        register_message.visible = False
        render()

    def back_to_welcome():
        state["route"] = "welcome"
        render()

    def password_hash(value):
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    async def create_account():
        username = (register_user.value or "").strip()
        password = register_password.value or ""
        if len(username) < 3:
            register_message.value = "Nama pengguna mestilah sekurang-kurangnya 3 aksara."
            register_message.visible = True
            render()
            return
        if len(password) < 6:
            register_message.value = "Kata laluan mestilah sekurang-kurangnya 6 aksara."
            register_message.visible = True
            render()
            return
        await store.set("username", username)
        await store.set("password_hash", password_hash(password))
        await store.set("role", state["role"])
        state["name"] = username
        log.info("Created local demo account for role %s", state["role"])
        if state["role"] == "Student":
            state["onboarding_step"] = 0
            state["route"] = "onboarding"
        else:
            state["route"] = "admin"
        render()

    async def login():
        username = (username_field.value or "").strip()
        password = login_password.value or ""
        if not username or not password:
            login_message.value = "Masukkan nama pengguna dan kata laluan untuk meneruskan."
            login_message.visible = True
            render()
            return
        saved_user = await store.get("username")
        saved_hash = await store.get("password_hash")
        if username != saved_user or password_hash(password) != saved_hash:
            login_message.value = "Nama pengguna atau kata laluan tidak sepadan. Cuba lagi atau cipta akaun."
            login_message.visible = True
            render()
            return
        state["name"] = username
        state["role"] = await store.get("role", "Student")
        login_message.value = ""
        login_message.visible = False
        if state["role"] == "Admin":
            state["route"] = "admin"
        elif await store.get("onboarding_done", False):
            await load_onboarding()
            state["route"] = "app"
            state["tab"] = "Home"
        else:
            state["onboarding_step"] = 0
            state["route"] = "onboarding"
        render()

    async def load_onboarding():
        for key in ("allowance", "frequency", "savings_target", "saved", "dream_item", "dream_price", "months"):
            state["onboarding"][key] = await store.get(f"onboarding_{key}", state["onboarding"].get(key, ""))
        allowance = number(state["onboarding"].get("allowance")) or 600
        frequency = state["onboarding"].get("frequency", "Monthly")
        base_allowance = allowance * 4.33 if frequency == "Weekly" else allowance
        state["allowance_additions"] = number(await store.get(allowance_additions_key(), 0)) or 0
        state["allowance"] = round(base_allowance + state["allowance_additions"], 2)
        log.debug("Allowance loaded for %s: base=%s extras=%s frequency=%s", state["name"], base_allowance, state["allowance_additions"], frequency)
        state["frequency"] = frequency
        saved = number(state["onboarding"].get("saved")) or 0
        price = number(state["onboarding"].get("dream_price")) or 1200
        first_goal = {
            "item": state["onboarding"].get("dream_item") or "Impian untuk dibeli",
            "saved": saved,
            "target": price,
            "target_date": f"Sasaran: dalam {state['onboarding'].get('months', '3')} bulan",
        }
        saved_goals = await store.get("savings_goals_json")
        try:
            goals = json.loads(saved_goals) if saved_goals else [first_goal]
            if not isinstance(goals, list):
                goals = [first_goal]
            goals = [goal for goal in goals if isinstance(goal, dict) and goal.get("item")]
        except (TypeError, json.JSONDecodeError):
            goals = [first_goal]
        state["goals"] = goals
        try:
            active_index = int(await store.get("active_savings_goal", 0))
        except (TypeError, ValueError):
            active_index = 0
        state["active_goal_index"] = active_index if 0 <= active_index < len(goals) else (0 if goals else -1)
        sync_active_goal()

        saved_transactions = await store.get("transactions_json")
        if saved_transactions is not None:
            try:
                transactions = json.loads(saved_transactions)
                if isinstance(transactions, list):
                    state["transactions"] = [item for item in transactions if isinstance(item, dict)]
            except (TypeError, json.JSONDecodeError):
                log.warning("Saved transaction history could not be read")
        state["spent"] = round(sum(number(item.get("amount")) or 0 for item in state["transactions"]), 2)
        state["balance"] = max(state["allowance"] - state["spent"], 0)

    def demo():
        state["name"] = "Pelajar"
        state["role"] = "Student"
        state["route"] = "app"
        state["tab"] = "Home"
        render()

    def select_tab(tab):
        state["tab"] = tab
        render()

    def open_coach():
        state["tab"] = "Coach"
        render()

    def set_chart_mode(mode):
        state["chart_mode"] = mode
        render()

    def sync_active_goal():
        index = state.get("active_goal_index", -1)
        goals = state.get("goals", [])
        if 0 <= index < len(goals):
            state["goal"] = goals[index]
        else:
            state["goal"] = {"item": "Matlamat seterusnya", "saved": 0, "target": 0, "target_date": "Tambah matlamat untuk bermula"}

    async def persist_goals():
        await store.set("savings_goals_json", json.dumps(state["goals"]))
        await store.set("active_savings_goal", state["active_goal_index"])

    async def persist_transactions():
        await store.set("transactions_json", json.dumps(state["transactions"]))
        state["spent"] = round(sum(number(item.get("amount")) or 0 for item in state["transactions"]), 2)
        state["balance"] = max(state["allowance"] - state["spent"], 0)

    def select_goal(index):
        state["active_goal_index"] = index
        sync_active_goal()
        asyncio.create_task(persist_goals())
        render()

    def set_frequency(freq):
        state["onboarding"]["frequency"] = freq
        render()

    def onboarding_back():
        if state["onboarding_step"] == 0:
            state["route"] = "welcome"
        else:
            state["onboarding_step"] -= 1
        render()

    def onboarding_next():
        values = state["onboarding"]
        if state["onboarding_step"] == 0:
            if (number(values.get("allowance")) or 0) <= 0:
                show_message("Masukkan jumlah elaun yang melebihi RM 0.")
                return
        elif state["onboarding_step"] == 1:
            target = number(values.get("savings_target"))
            saved = number(values.get("saved"))
            if target is None or target <= 0 or saved is None:
                show_message("Masukkan matlamat simpanan dan jumlah simpanan sedia ada yang sah.")
                return
        state["onboarding_step"] += 1
        render()

    async def finish_onboarding():
        values = state["onboarding"]
        if not (values.get("dream_item") or "").strip() or (number(values.get("dream_price")) or 0) <= 0 or (number(values.get("months")) or 0) <= 0:
            show_message("Masukkan impian pembelian, harga dan tempoh untuk meneruskan.")
            return
        for key, value in values.items():
            await store.set(f"onboarding_{key}", str(value))
        await store.set("onboarding_done", True)
        await load_onboarding()
        state["route"] = "app"
        state["tab"] = "Home"
        render()

    def restart_onboarding():
        state["onboarding_step"] = 0
        state["route"] = "onboarding"
        render()

    async def logout():
        state["coach_session"] += 1
        state["chat"] = []
        state["coach_busy"] = False
        state["coach_error"] = ""
        state["route"] = "welcome"
        username_field.value = ""
        login_password.value = ""
        login_message.value = ""
        render()

    def show_message(text):
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Semakan ringkas"),
            content=ft.Text(text),
            actions=[ft.TextButton("Faham", on_click=lambda e: page.pop_dialog())],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.show_dialog(dialog)

    def open_scanner():
        state["route"] = "scanner"
        camera = fcam.Camera(width=content_width() - 36, height=320, preview_enabled=True)
        state["camera"] = camera
        state["camera_ready"] = False
        state["camera_status"] = ft.Text("Meminta akses kamera…", size=13, color=MUTED)
        state["route"] = "scanner"
        render()
        asyncio.create_task(initialize_camera(camera))

    async def initialize_camera(camera):
        try:
            cameras = await camera.get_available_cameras()
            if not cameras:
                raise RuntimeError("Kamera tidak tersedia pada peranti ini.")
            back_camera = next((item for item in cameras if item.lens_direction == fcam.CameraLensDirection.BACK), cameras[0])
            await camera.initialize(back_camera, resolution_preset=fcam.ResolutionPreset.MEDIUM)
            state["camera_ready"] = True
            state["camera_status"].value = "Kamera sedia. Letakkan resit di tengah dan ambil gambar."
            state["camera_status"].color = ft.Colors.GREEN_700
            state["camera_status"].update()
        except Exception as error:
            log.warning("Camera setup failed: %s", error)
            state["camera_ready"] = False
            state["camera_status"].value = "Kamera tidak tersedia. Semak kebenaran pelayar atau cuba telefon yang mempunyai kamera."
            state["camera_status"].color = ft.Colors.ERROR
            state["camera_status"].update()

    async def capture_photo():
        if not state["camera_ready"]:
            state["camera_status"].value = "Benarkan akses kamera dan tunggu pratonton bermula."
            state["camera_status"].update()
            return
        camera = state["camera"]
        state["camera_ready"] = False
        state["camera_status"].value = "Sedang mengambil gambar…"
        state["camera_status"].update()
        log.info("Receipt capture started")
        try:
            photo = await asyncio.wait_for(camera.take_picture(), timeout=20)
            if not photo:
                raise ValueError("Camera returned no photo")
            log.info("Receipt photo captured")
            try:
                await asyncio.wait_for(camera.pause_preview(), timeout=2)
            except Exception as error:
                log.warning("Receipt preview pause skipped: %s", type(error).__name__)
            camera.preview_enabled = False
            camera.visible = False
            camera.update()
        except Exception as error:
            log.warning("Camera capture failed: %s", type(error).__name__)
            if state["camera"] is camera and state["route"] == "scanner":
                state["camera_status"].value = "Gambar tidak dapat diambil. Cuba lagi atau semak kebenaran kamera."
                state["camera_status"].color = ft.Colors.ERROR
                state["camera_status"].update()
            return
        finally:
            if state["camera"] is camera:
                state["camera_ready"] = True
        if state["camera"] is not camera or state["route"] != "scanner":
            return

        state["receipt_photo"] = photo
        receipt_field_style = {
            "filled": True,
            "fill_color": ft.Colors.WHITE,
            "border_color": ft.Colors.BLUE_GREY_100,
            "focused_border_color": PRIMARY,
            "border_radius": 14,
            "content_padding": 14,
        }
        state["receipt_field_style"] = receipt_field_style
        state["receipt_items"] = [new_receipt_item()]
        state["receipt_message"] = ft.Text("Sedang menganalisis resit…", size=12, color=MUTED)
        review_message = state["receipt_message"]
        state["route"] = "receipt_review"
        state["receipt_busy"] = True
        render()

        try:
            log.info("Receipt analysis started")
            result = await analyze_receipt(state, photo)
            log.info("Receipt analysis response received")
            if state["route"] != "receipt_review" or state["receipt_message"] is not review_message:
                return
items = result.get("items", [])

state["receipt_items"] = [
    new_receipt_item() for _ in items
]

for receipt_item, item in zip(state["receipt_items"], items):
    description = item.get("description")
    amount = item.get("amount")
    category = item.get("category")

    if isinstance(description, str):
        receipt_item["description"].value = description

    if isinstance(amount, (int, float)) and not isinstance(amount, bool):
        receipt_item["amount"].value = f"{amount:.2f}"

    if isinstance(category, str) and category in CATEGORY_OPTIONS:
        receipt_item["category"].value = category

review_message.value = (
    f"AI menemui {len(items)} butiran pembelian. "
    "Semak dan betulkan sebelum menyimpan."
)
            if isinstance(description, str):
                receipt_item["description"].value = description.strip()[:200]
            if type(amount) in (int, float) and 0 < amount <= 1_000_000_000 and math.isfinite(amount):
                receipt_item["amount"].value = f"{amount:.2f}"
            if isinstance(category, str) and category in CATEGORY_OPTIONS:
                receipt_item["category"].value = category
            review_message.value = "Semak cadangan AI dan isi butiran yang masih kosong."
        except CoachError as error:
            log.warning("Receipt analysis: %s", error)
            review_message.value = f"{error} Anda boleh isi butiran secara manual."
        except Exception:
            log.exception("Unexpected receipt analysis failure")
            review_message.value = "Analisis resit gagal. Sila isi butiran secara manual."
        finally:
            if state["route"] == "receipt_review" and state["receipt_message"] is review_message:
                state["receipt_busy"] = False
                render()

    def new_receipt_item():
        field_style = state["receipt_field_style"]
        return {
            "description": ft.TextField(
                label="Apa yang dibeli?", **field_style,
            ),
            "amount": ft.TextField(
                label="Jumlah (RM)",
                prefix=ft.Text("RM "),
                keyboard_type=ft.KeyboardType.NUMBER,
                **field_style,
            ),
            "category": ft.Dropdown(
                value="Lain-lain",
                label="Kategori",
                options=[ft.DropdownOption(text=item) for item in CATEGORY_OPTIONS],
                filled=True,
                fill_color=ft.Colors.WHITE,
                border_color=ft.Colors.BLUE_GREY_100,
                focused_border_color=PRIMARY,
                border_radius=14,
                content_padding=14,
            ),
        }

    def add_receipt_item():
        state["receipt_items"].append(new_receipt_item())
        render()

    async def close_scanner():
        camera = state.get("camera")
        if camera and state.get("camera_ready"):
            try:
                await camera.pause_preview()
            except Exception:
                pass
        state["camera"] = None
        state["camera_ready"] = False
        state["route"] = "app"
        state["tab"] = "Transactions"
        render()

    async def retake_receipt():
        camera = state.get("camera")
        if not camera:
            open_scanner()
            return
        camera.visible = True
        camera.preview_enabled = True
        state["route"] = "scanner"
        render()
        try:
            await camera.resume_preview()
        except Exception as error:
            log.warning("Camera preview could not resume: %s", error)

    async def save_receipt():
        entries = []
        for index, item in enumerate(state["receipt_items"], start=1):
            description = (item["description"].value or "").strip()
            amount = number(item["amount"].value)
            if not description and amount is None:
                continue
            if not description or amount is None or amount <= 0:
                state["receipt_message"].value = (
                    f"Lengkapkan keterangan dan jumlah melebihi RM 0 "
                    f"untuk butiran {index}, atau biarkan kedua-dua medan kosong."
                )
                page.update()
                return
            category = CATEGORY_OPTIONS.get(item["category"].value, "Other")
            entries.append({
                "description": description,
                "category": category,
                "date": "Sebentar tadi · imbasan",
                "amount": amount,
            })
        if not entries:
            state["receipt_message"].value = "Isi sekurang-kurangnya satu butiran transaksi sebelum menyimpan."
            page.update()
            return
        state["transactions"][0:0] = entries
        await persist_transactions()
        state["camera"] = None
        state["camera_ready"] = False
        state["receipt_photo"] = None
        state["route"] = "app"
        state["tab"] = "Transactions"
        render()

    def add_allowance():
        amount = ft.TextField(
            label="Jumlah elaun (RM)",
            prefix=ft.Text("RM "),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=14,
            autofocus=True,
        )
        error = ft.Text("", size=12, color=ft.Colors.ERROR)

        async def save_allowance():
            value = number(amount.value)
            if value is None or value <= 0:
                error.value = "Masukkan jumlah elaun yang melebihi RM 0."
                page.update()
                return
            state["allowance_additions"] = round(state.get("allowance_additions", 0) + value, 2)
            state["allowance"] = round(state["allowance"] + value, 2)
            state["balance"] = max(round(state["allowance"] - state["spent"], 2), 0)
            await store.set(allowance_additions_key(), state["allowance_additions"])
            page.pop_dialog()
            render()
            show_message(f"{money(value)} ditambah kepada elaun bulan ini.")

        page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text("Tambah elaun"),
            content=ft.Column([
                amount,
                label("Ini menambah jumlah elaun diterima dan baki tersedia. Ia tidak dikira sebagai perbelanjaan.", size=12, color=MUTED),
                error,
            ], tight=True, spacing=10, width=330),
            actions=[
                ft.TextButton("Batal", on_click=lambda e: page.pop_dialog()),
                ft.Button(content=ft.Text("Tambah elaun"), on_click=save_allowance, bgcolor=PRIMARY, color=ft.Colors.WHITE),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        ))

    def add_expense():
        description = ft.TextField(label="Apakah yang dibeli?", hint_text="cth. makan tengah hari", border_radius=14)
        amount = ft.TextField(label="Jumlah (RM)", prefix=ft.Text("RM "), keyboard_type=ft.KeyboardType.NUMBER, border_radius=14)
        category_labels = tuple(item for item in CATEGORY_OPTIONS if item != "Lain-lain")
        category = ft.Dropdown(value="Makanan", label="Kategori", options=[ft.DropdownOption(text=item) for item in category_labels], border_radius=14)
        error = ft.Text("", size=12, color=ft.Colors.ERROR)

        async def save_expense():
            value = number(amount.value)
            name = (description.value or "").strip()
            if not name or value is None or value <= 0:
                error.value = "Masukkan keterangan dan jumlah yang melebihi RM 0."
                page.update()
                return
            state["transactions"].insert(0, {"description": name, "category": CATEGORY_OPTIONS.get(category.value, "Fun"), "date": "Sebentar tadi", "amount": value})
            await persist_transactions()
            page.pop_dialog()
            render()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Tambah perbelanjaan", weight=ft.FontWeight.BOLD),
            content=ft.Column([description, amount, category, error], tight=True, spacing=10, width=330),
            actions=[ft.TextButton("Batal", on_click=lambda e: page.pop_dialog()), ft.Button(content=ft.Text("Simpan perbelanjaan"), on_click=save_expense, bgcolor=PRIMARY, color=ft.Colors.WHITE)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.show_dialog(dialog)

    def delete_transaction(index):
        if not 0 <= index < len(state["transactions"]):
            return

        async def confirm_delete():
            state["transactions"].pop(index)
            await persist_transactions()
            page.pop_dialog()
            render()

        page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text("Padam transaksi ini?"),
            content=ft.Text("Perbelanjaan ini akan dibuang daripada aktiviti dan jumlah keseluruhan anda."),
            actions=[
                ft.TextButton("Batal", on_click=lambda e: page.pop_dialog()),
                ft.TextButton("Padam", on_click=confirm_delete),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        ))

    def clear_transactions():
        if not state["transactions"]:
            return

        async def confirm_clear():
            state["transactions"] = []
            await persist_transactions()
            page.pop_dialog()
            render()

        page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text("Kosongkan semua transaksi?"),
            content=ft.Text("Sejarah transaksi anda akan dipadam dan jumlah perbelanjaan bulan ini ditetapkan semula."),
            actions=[
                ft.TextButton("Batal", on_click=lambda e: page.pop_dialog()),
                ft.TextButton("Kosongkan semua", on_click=confirm_clear),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        ))

    def show_goal_celebration(completed_names, credited=None, unallocated=0):
        names = ", ".join(completed_names)
        count = len(completed_names)
        detail = f"Anda mencapai sasaran untuk {names}. "
        detail += "Matlamat yang selesai telah dikeluarkan daripada senarai aktif." if count == 1 else "Matlamat yang selesai telah dikeluarkan daripada senarai aktif."
        detail += " Anda boleh memilih sama ada ingin mencipta matlamat baharu."
        if credited is not None:
            detail += f" {money(credited)} telah dibahagikan antara matlamat yang belum selesai."
        if unallocated > 0:
            detail += f" {money(unallocated)} tidak diagihkan kerana semua sasaran yang tinggal telah dicapai."

        def create_another_goal():
            page.pop_dialog()
            add_goal()

        celebration_icon = ft.Container(
            content=ft.Icon(ft.Icons.CELEBRATION, color=ft.Colors.AMBER_700, size=32),
            bgcolor=ft.Colors.AMBER_50,
            padding=14,
            border_radius=30,
            scale=0.75,
            animate_scale=ft.Animation(duration=420, curve=ft.AnimationCurve.BOUNCE_OUT),
        )
        page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text("Matlamat tercapai! 🎉"),
            content=ft.Column([
                ft.Row([celebration_icon], alignment=ft.MainAxisAlignment.CENTER),
                ft.Text("Satu pencapaian kewangan yang membanggakan!"),
                ft.Text(detail, size=13, color=MUTED),
            ], tight=True, spacing=9, width=340, horizontal_alignment=ft.CrossAxisAlignment.STRETCH),
            actions=[
                ft.TextButton("Bukan sekarang", on_click=lambda e: page.pop_dialog()),
                ft.Button(content=ft.Text("Cipta matlamat baharu"), on_click=lambda e: create_another_goal(), bgcolor=PRIMARY, color=ft.Colors.WHITE),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        ))
        celebration_icon.scale = 1
        page.update()

    def add_savings_contribution():
        if not state["goals"]:
            show_message("Cipta matlamat simpanan sebelum menambah simpanan.")
            return
        if all(
            (number(goal.get("saved")) or 0) >= (number(goal.get("target")) or 0)
            for goal in state["goals"]
        ):
            completed_names = [goal.get("item", "Matlamat simpanan") for goal in state["goals"]]
            state["goals"] = []
            state["active_goal_index"] = -1
            sync_active_goal()
            asyncio.create_task(persist_goals())
            render()
            show_goal_celebration(completed_names)
            return

        amount = ft.TextField(
            label="Jumlah untuk disimpan (RM)",
            prefix=ft.Text("RM "),
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=14,
            autofocus=True,
        )
        error = ft.Text("", size=12, color=ft.Colors.ERROR)

        async def save_contribution():
            value = number(amount.value)
            if value is None or value <= 0:
                error.value = "Masukkan jumlah yang melebihi RM 0."
                page.update()
                return
            original_goals = [dict(goal) for goal in state["goals"]]
            updated_goals, unallocated = distribute_savings(original_goals, value)
            credited = round(value - unallocated, 2)
            if credited <= 0:
                error.value = "Tiada baki sasaran untuk diagihkan."
                page.update()
                return

            completed_indices = []
            completed_names = []
            for index, goal in enumerate(updated_goals):
                target_cents = int(round((number(goal.get("target")) or 0) * 100))
                saved_cents = int(round((number(goal.get("saved")) or 0) * 100))
                if target_cents > 0 and saved_cents >= target_cents:
                    completed_indices.append(index)
                    completed_names.append(goal.get("item", "Matlamat simpanan"))

            old_active = state["active_goal_index"]
            state["goals"] = [
                goal for index, goal in enumerate(updated_goals)
                if index not in completed_indices
            ]
            if not state["goals"]:
                state["active_goal_index"] = -1
            else:
                removed_before_active = sum(index < old_active for index in completed_indices)
                new_active = old_active - removed_before_active
                if old_active in completed_indices:
                    new_active = min(new_active, len(state["goals"]) - 1)
                state["active_goal_index"] = min(max(new_active, 0), len(state["goals"]) - 1)

            sync_active_goal()
            await persist_goals()
            page.pop_dialog()
            render()
            if completed_names:
                show_goal_celebration(completed_names, credited, unallocated)
            else:
                show_message(f"{money(credited)} telah dibahagikan sama rata antara matlamat yang belum selesai.")

        page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text("Tambah simpanan"),
            content=ft.Column([
                amount,
                label("Jumlah ini dibahagi sama rata antara matlamat yang belum selesai. Apabila matlamat dicapai, kami akan meraikannya dan mengeluarkannya daripada senarai aktif.", size=12, color=MUTED),
                error,
            ], tight=True, spacing=10, width=330),
            actions=[
                ft.TextButton("Batal", on_click=lambda e: page.pop_dialog()),
                ft.Button(content=ft.Text("Bahagi dan simpan"), on_click=save_contribution, bgcolor=PRIMARY, color=ft.Colors.WHITE),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        ))

    def add_goal():
        edit_goal()

    def edit_goal(goal_index=None):
        is_editing = goal_index is not None and 0 <= goal_index < len(state["goals"])
        existing = dict(state["goals"][goal_index]) if is_editing else {
            "item": "", "saved": 0, "target": 0, "target_date": "Belum ada tarikh sasaran",
        }
        item = ft.TextField(label="Nama matlamat", value=existing.get("item", ""), hint_text="cth. komputer riba baharu", border_radius=14)
        target = ft.TextField(label="Jumlah sasaran (RM)", value=str(existing.get("target", "")), prefix=ft.Text("RM "), keyboard_type=ft.KeyboardType.NUMBER, border_radius=14)
        saved = ft.TextField(label="Jumlah yang sudah disimpan (RM)", value=str(existing.get("saved", 0)), prefix=ft.Text("RM "), keyboard_type=ft.KeyboardType.NUMBER, border_radius=14)
        target_date = ft.TextField(label="Tarikh atau tempoh sasaran", value=existing.get("target_date", ""), hint_text="cth. Dalam 4 bulan", border_radius=14)
        error = ft.Text("", size=12, color=ft.Colors.ERROR)

        async def save_goal():
            target_value = number(target.value)
            saved_value = number(saved.value)
            goal_name = (item.value or "").strip()
            if not goal_name or target_value is None or target_value <= 0 or saved_value is None or saved_value < 0:
                error.value = "Masukkan nama, sasaran melebihi RM 0 dan simpanan RM 0 atau lebih."
                page.update()
                return
            updated = {
                "item": goal_name,
                "saved": saved_value,
                "target": target_value,
                "target_date": (target_date.value or "").strip() or "Belum ada tarikh sasaran",
            }
            completed_now = saved_value >= target_value
            completed_index = goal_index if is_editing else len(state["goals"])
            previous_active = state["active_goal_index"]
            if is_editing:
                state["goals"][goal_index] = updated
                state["active_goal_index"] = goal_index
            else:
                state["goals"].append(updated)
                state["active_goal_index"] = len(state["goals"]) - 1

            if completed_now:
                state["goals"].pop(completed_index)
                if not state["goals"]:
                    state["active_goal_index"] = -1
                elif previous_active == completed_index:
                    state["active_goal_index"] = min(completed_index, len(state["goals"]) - 1)
                elif previous_active > completed_index:
                    state["active_goal_index"] = previous_active - 1
                else:
                    state["active_goal_index"] = previous_active if previous_active >= 0 else 0

            sync_active_goal()
            await persist_goals()
            page.pop_dialog()
            render()
            if completed_now:
                show_goal_celebration([goal_name])

        page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text("Edit matlamat simpanan" if is_editing else "Tambah matlamat simpanan"),
            content=ft.Column([item, target, saved, target_date, error], tight=True, spacing=10, width=330),
            actions=[
                ft.TextButton("Batal", on_click=lambda e: page.pop_dialog()),
                ft.Button(content=ft.Text("Simpan matlamat"), on_click=save_goal, bgcolor=PRIMARY, color=ft.Colors.WHITE),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        ))

    def delete_goal(goal_index):
        if not 0 <= goal_index < len(state["goals"]):
            return

        async def confirm_delete():
            state["goals"].pop(goal_index)
            if not state["goals"]:
                state["active_goal_index"] = -1
            elif goal_index < state["active_goal_index"]:
                state["active_goal_index"] -= 1
            elif goal_index == state["active_goal_index"]:
                state["active_goal_index"] = min(goal_index, len(state["goals"]) - 1)
            sync_active_goal()
            await persist_goals()
            page.pop_dialog()
            render()

        page.show_dialog(ft.AlertDialog(
            modal=True,
            title=ft.Text("Padam matlamat simpanan ini?"),
            content=ft.Text("Anda boleh menciptanya semula kemudian, tetapi kemajuan simpanan akan dipadam."),
            actions=[
                ft.TextButton("Batal", on_click=lambda e: page.pop_dialog()),
                ft.TextButton("Padam", on_click=confirm_delete),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        ))

    def configure_ai(event=None):
        url = ft.TextField(label="Alamat HTTPS pelayan Wangku", value=state["backend_url"], hint_text="https://pelayan-anda.example", border_radius=14)
        connection_status = ft.Text("", size=12, color=MUTED)
        token = ft.TextField(label="Kod akses pelayan (bukan kunci Gemini)", value=state["backend_token"], password=True, can_reveal_password=True, border_radius=14)
        async def test_backend(event=None):
            connection_status.value = "Sedang menguji sambungan…"
            connection_status.color = MUTED
            page.update()
            try:
                connection_status.value = await check_backend((url.value or "").strip().rstrip("/"))
                connection_status.color = ft.Colors.GREEN_700
            except CoachError as error:
                connection_status.value = str(error)
                connection_status.color = ft.Colors.ERROR
            page.update()

        async def save_settings(event=None):
            state["backend_url"] = (url.value or "").strip().rstrip("/")
            state["backend_token"] = (token.value or "").strip()
            await store.set("backend_url", state["backend_url"])
            page.pop_dialog()
            render()
        page.show_dialog(ft.AlertDialog(
            modal=True, title=ft.Text("Tetapan AI"),
            content=ft.Column([url, token, ft.Text("Kod akses disimpan untuk sesi ini sahaja. Jangan masukkan kunci Gemini di sini.", size=12), connection_status], tight=True, width=330),
            actions=[
                ft.TextButton("Uji sambungan", on_click=test_backend),
                ft.TextButton("Batal", on_click=lambda e: page.pop_dialog()),
                ft.TextButton("Simpan", on_click=save_settings),
            ],
        ))

    async def send_message(event=None, suggested=None):
        if state["coach_busy"]:
            return
        prompt = state.get("coach_prompt")
        text = suggested if suggested is not None else ((prompt.value or "").strip() if prompt else "")
        if not text:
            return
        if len(text) > 2000:
            state["coach_error"] = "Sila ringkaskan soalan kepada 2,000 aksara atau kurang."
            render()
            return
        state["chat"].append(("you", text))
        state["coach_busy"] = True
        state["coach_error"] = ""
        session = state["coach_session"]
        if prompt:
            prompt.value = ""
        render()
        try:
            answer = await reply(state, list(state["chat"]))
            if session == state["coach_session"]:
                state["chat"].append(("coach", answer))
        except CoachError as error:
            if session == state["coach_session"]:
                state["coach_error"] = str(error)
        except Exception:
            if session == state["coach_session"]:
                state["coach_error"] = "Ralat berlaku semasa mendapatkan jawapan. Sila cuba lagi."
        finally:
            if session == state["coach_session"]:
                state["coach_busy"] = False
                if state["route"] == "app" and state["tab"] == "Coach":
                    render()

    async def start():
        state["backend_url"] = await store.get("backend_url") or DEFAULT_BACKEND_URL
        username = await store.get("username")
        if username:
            log.info("Found a saved local demo account")

        page.add(
            ft.Container(
                content=ft.Column(
                    [
                        mascot(150),
                        ft.Row(
                            [wordmark(25)],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        label(
                            "Wang anda. Masa depan anda.",
                            size=14,
                            color=MUTED,
                        ),
                    ],
                    spacing=12,
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                alignment=ft.Alignment.CENTER,
                expand=True,
                opacity=0.25,
                scale=0.76,
                animate_opacity=ft.Animation(
                    duration=850,
                    curve=ft.AnimationCurve.EASE_OUT,
                ),
                animate_scale=ft.Animation(
                    duration=850,
                    curve=ft.AnimationCurve.EASE_OUT_BACK,
                ),
            )
        )
        page.update()

        page.controls[0].opacity = 1
        page.controls[0].scale = 1
        page.update()

        await asyncio.sleep(1.05)
        state["route"] = "welcome"
        render()

    await start()


ft.run(main)
