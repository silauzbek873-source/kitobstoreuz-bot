import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.types.input_file import FSInputFile

logging.basicConfig(level=logging.INFO)

BASE_DIR = Path(__file__).resolve().parent
BOOKS_FILE = BASE_DIR / "books.json"
USERS_FILE = BASE_DIR / "users.json"
ORDERS_FILE = BASE_DIR / "orders.json"

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "Abdullayevv_tm").lstrip("@").strip()
ADMIN_ID = int(os.getenv("ADMIN_ID", "7020576612"))
PAYMENT_CARD = os.getenv("PAYMENT_CARD", "5614 6814 0959 5364").strip()
CARD_HOLDER = os.getenv("CARD_HOLDER", "Abdullayev Saidaxmad").strip()
BRAND_NAME = os.getenv("BRAND_NAME", "KitobStoreUz").strip()

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN topilmadi. Railway Variables ichiga BOT_TOKEN qo'shing.")


def ensure_file(path: Path, default_data: Any) -> None:
    if not path.exists():
        path.write_text(
            json.dumps(default_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


ensure_file(BOOKS_FILE, [])
ensure_file(USERS_FILE, {})
ensure_file(ORDERS_FILE, [])


def load_books() -> List[Dict[str, Any]]:
    return json.loads(BOOKS_FILE.read_text(encoding="utf-8"))


def save_books(data: List[Dict[str, Any]]) -> None:
    BOOKS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_users() -> Dict[str, Any]:
    return json.loads(USERS_FILE.read_text(encoding="utf-8"))


def save_users(data: Dict[str, Any]) -> None:
    USERS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_orders() -> List[Dict[str, Any]]:
    return json.loads(ORDERS_FILE.read_text(encoding="utf-8"))


def save_orders(data: List[Dict[str, Any]]) -> None:
    ORDERS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


TEXTS = {
    "uz": {
        "choose_lang": "Tilni tanlang:",
        "welcome": "📚 Assalomu alaykum!\n\nSiz KitobStoreUz botidasiz 👋\n\nQuyidagi tugmalardan foydalaning:",
        "books": "📚 Kitoblar",
        "order": "🛒 Buyurtma",
        "payment": "💳 To'lov",
        "delivery": "🚚 Yetkazib berish",
        "contact": "☎️ Aloqa",
        "admin": "⚙️ Admin panel",
        "admin_not_allowed": "Siz admin emassiz.",
        "admin_panel": "⚙️ Admin panel",
        "add_book": "➕ Kitob qo'shish",
        "delete_book": "🗑 Kitob o'chirish",
        "book_list": "📚 Kitoblar ro'yxati",
        "orders": "📦 Buyurtmalar",
        "stats": "📊 Statistika",
        "ordinary_menu": "🏠 Oddiy menyu",
        "choose_book": "Quyidagi kitoblardan tanlang:",
        "book_empty": "Hozircha kitoblar yo'q.",
        "buy": "🛒 Buyurtma berish",
        "enter_name": "✍️ Ismingizni kiriting:",
        "send_phone": "📱 Telefon raqamingizni pastdagi tugma orqali yuboring:",
        "send_location": "📍 Joylashuvingizni pastdagi tugma orqali yuboring:",
        "choose_payment": "💳 To'lov turini tanlang:",
        "payme": "💳 Payme",
        "cash": "💵 Naqd",
        "order_saved": "✅ Buyurtmangiz qabul qilindi. Tez orada siz bilan bog'lanamiz.",
        "phone_wrong": "Iltimos, telefon raqamni tugma orqali yuboring.",
        "location_wrong": "Iltimos, joylashuvni tugma orqali yuboring.",
        "enter_book_name": "Yangi kitob nomini kiriting:",
        "enter_book_price": "Narxini kiriting (faqat raqam):",
        "enter_book_desc": "Qisqacha mazmunini kiriting:",
        "enter_book_photo": "Rasm yuboring:",
        "book_added": "✅ Kitob qo'shildi.",
        "book_deleted": "✅ Kitob o'chirildi.",
        "choose_delete_book": "O'chirish uchun kitobni tanlang:",
        "contact_text": "Admin: @{admin}\nKarta: {card}\nKarta egasi: {holder}",
        "delivery_text": "🚚 Yetkazib berish mavjud. Buyurtma paytida joylashuv yuborasiz.",
        "payment_text": "💳 To'lov turlari: Payme yoki Naqd.",
        "stats_text": "📊 Statistika:\n\n👥 Foydalanuvchilar: {users}\n📚 Kitoblar: {books}\n📦 Buyurtmalar: {orders}",
        "language_saved": "✅ Til saqlandi.",
        "back_admin": "Admin panelga qaytdingiz.",
    },
    "ru": {
        "choose_lang": "Выберите язык:",
        "welcome": "📚 Здравствуйте!\n\nВы в боте KitobStoreUz 👋\n\nИспользуйте кнопки ниже:",
        "books": "📚 Книги",
        "order": "🛒 Заказ",
        "payment": "💳 Оплата",
        "delivery": "🚚 Доставка",
        "contact": "☎️ Контакт",
        "admin": "⚙️ Админ панель",
        "admin_not_allowed": "Вы не админ.",
        "admin_panel": "⚙️ Админ панель",
        "add_book": "➕ Добавить книгу",
        "delete_book": "🗑 Удалить книгу",
        "book_list": "📚 Список книг",
        "orders": "📦 Заказы",
        "stats": "📊 Статистика",
        "ordinary_menu": "🏠 Обычное меню",
        "choose_book": "Выберите книгу:",
        "book_empty": "Пока книг нет.",
        "buy": "🛒 Заказать",
        "enter_name": "✍️ Введите имя:",
        "send_phone": "📱 Отправьте номер телефона кнопкой ниже:",
        "send_location": "📍 Отправьте локацию кнопкой ниже:",
        "choose_payment": "💳 Выберите способ оплаты:",
        "payme": "💳 Payme",
        "cash": "💵 Наличные",
        "order_saved": "✅ Ваш заказ принят. Скоро с вами свяжемся.",
        "phone_wrong": "Пожалуйста, отправьте номер телефона кнопкой.",
        "location_wrong": "Пожалуйста, отправьте локацию кнопкой.",
        "enter_book_name": "Введите название книги:",
        "enter_book_price": "Введите цену (только число):",
        "enter_book_desc": "Введите краткое описание:",
        "enter_book_photo": "Отправьте фото:",
        "book_added": "✅ Книга добавлена.",
        "book_deleted": "✅ Книга удалена.",
        "choose_delete_book": "Выберите книгу для удаления:",
        "contact_text": "Админ: @{admin}\nКарта: {card}\nВладелец карты: {holder}",
        "delivery_text": "🚚 Доставка доступна. При заказе отправьте локацию.",
        "payment_text": "💳 Виды оплаты: Payme или Наличные.",
        "stats_text": "📊 Статистика:\n\n👥 Пользователи: {users}\n📚 Книги: {books}\n📦 Заказы: {orders}",
        "language_saved": "✅ Язык сохранён.",
        "back_admin": "Возврат в админ панель.",
    },
}


def get_lang(user_id: int) -> str:
    users = load_users()
    return users.get(str(user_id), {}).get("lang", "uz")


def tr(user_id: int, key: str, **kwargs) -> str:
    lang = get_lang(user_id)
    text = TEXTS.get(lang, TEXTS["uz"]).get(key, key)
    return text.format(**kwargs)


def remember_user(message: Message) -> None:
    users = load_users()
    uid = str(message.from_user.id)
    users[uid] = {
        "tg_id": message.from_user.id,
        "username": message.from_user.username or "",
        "full_name": message.from_user.full_name or "",
        "lang": users.get(uid, {}).get("lang", "uz"),
    }
    save_users(users)


def is_admin(message: Message) -> bool:
    return (
        (message.from_user.username or "").lstrip("@").lower() == ADMIN_USERNAME.lower()
        or message.from_user.id == ADMIN_ID
    )


def language_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Uz O'zbekcha"), KeyboardButton(text="Ru Русский")]],
        resize_keyboard=True,
    )


def main_menu(user_id: int) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=tr(user_id, "books")), KeyboardButton(text=tr(user_id, "order"))],
            [KeyboardButton(text=tr(user_id, "payment")), KeyboardButton(text=tr(user_id, "delivery"))],
            [KeyboardButton(text=tr(user_id, "contact")), KeyboardButton(text=tr(user_id, "admin"))],
        ],
        resize_keyboard=True,
    )


def admin_menu(user_id: int) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=tr(user_id, "add_book")), KeyboardButton(text=tr(user_id, "delete_book"))],
            [KeyboardButton(text=tr(user_id, "book_list")), KeyboardButton(text=tr(user_id, "orders"))],
            [KeyboardButton(text=tr(user_id, "stats")), KeyboardButton(text=tr(user_id, "ordinary_menu"))],
        ],
        resize_keyboard=True,
    )


def contact_request_kb(user_id: int) -> ReplyKeyboardMarkup:
    text = "📱 Telefon raqam yuborish" if get_lang(user_id) == "uz" else "📱 Отправить номер телефона"
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=text, request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def location_request_kb(user_id: int) -> ReplyKeyboardMarkup:
    text = "📍 Joylashuvni yuborish" if get_lang(user_id) == "uz" else "📍 Отправить локацию"
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=text, request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def payment_choice_kb(user_id: int) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=tr(user_id, "payme")), KeyboardButton(text=tr(user_id, "cash"))]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def buy_inline_kb(book_id: int, user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=tr(user_id, "buy"), callback_data=f"buy:{book_id}")]
        ]
    )


class AddBookState(StatesGroup):
    waiting_name = State()
    waiting_price = State()
    waiting_desc = State()
    waiting_photo = State()


class OrderState(StatesGroup):
    waiting_name = State()
    waiting_phone = State()
    waiting_location = State()
    waiting_payment = State()


router = Router()
bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
dp.include_router(router)


@router.message(Command("start"))
async def start_cmd(message: Message, state: FSMContext) -> None:
    remember_user(message)
    await state.clear()
    await message.answer(
        f"{TEXTS['uz']['choose_lang']} / {TEXTS['ru']['choose_lang']}\n\n"
        f"🆔 TG ID avtomatik olindi: <code>{message.from_user.id}</code>",
        reply_markup=language_kb(),
    )


@router.message(F.text.in_(["Uz O'zbekcha", "Ru Русский"]))
async def set_language(message: Message) -> None:
    remember_user(message)
    users = load_users()
    uid = str(message.from_user.id)
    users.setdefault(uid, {})
    users[uid]["lang"] = "uz" if message.text == "Uz O'zbekcha" else "ru"
    save_users(users)
    await message.answer(tr(message.from_user.id, "welcome"), reply_markup=main_menu(message.from_user.id))


@router.message(F.text.in_([TEXTS["uz"]["books"], TEXTS["ru"]["books"], TEXTS["uz"]["order"], TEXTS["ru"]["order"]]))
async def show_books(message: Message) -> None:
    remember_user(message)
    books = load_books()
    if not books:
        await message.answer(tr(message.from_user.id, "book_empty"))
        return
    await message.answer(tr(message.from_user.id, "choose_book"))
    for book in books:
        caption = (
            f"📚 <b>{book['name']}</b>\n"
            f"💰 {book['price']} so'm\n\n"
            f"{book.get('desc', '')}"
        )
        photo = book.get("photo", "").strip()
        if photo and Path(photo).exists():
            await message.answer_photo(FSInputFile(photo), caption=caption, reply_markup=buy_inline_kb(book["id"], message.from_user.id))
        elif photo:
            await message.answer_photo(photo=photo, caption=caption, reply_markup=buy_inline_kb(book["id"], message.from_user.id))
        else:
            await message.answer(caption, reply_markup=buy_inline_kb(book["id"], message.from_user.id))


@router.callback_query(F.data.startswith("buy:"))
async def buy_book(call: CallbackQuery, state: FSMContext) -> None:
    remember_user(call.message)
    try:
        book_id = int(call.data.split(":")[1])
    except Exception:
        await call.answer("Xato", show_alert=True)
        return

    books = load_books()
    book = next((b for b in books if b["id"] == book_id), None)
    if not book:
        await call.answer("Kitob topilmadi", show_alert=True)
        return

    await state.update_data(book_id=book_id)
    await state.set_state(OrderState.waiting_name)
    await call.message.answer(tr(call.from_user.id, "enter_name"), reply_markup=ReplyKeyboardRemove())
    await call.answer()


@router.message(OrderState.waiting_name)
async def order_name(message: Message, state: FSMContext) -> None:
    await state.update_data(customer_name=(message.text or "").strip())
    await state.set_state(OrderState.waiting_phone)
    await message.answer(tr(message.from_user.id, "send_phone"), reply_markup=contact_request_kb(message.from_user.id))


@router.message(OrderState.waiting_phone, F.contact)
async def order_phone(message: Message, state: FSMContext) -> None:
    await state.update_data(phone=message.contact.phone_number)
    await state.set_state(OrderState.waiting_location)
    await message.answer(tr(message.from_user.id, "send_location"), reply_markup=location_request_kb(message.from_user.id))


@router.message(OrderState.waiting_phone)
async def order_phone_wrong(message: Message) -> None:
    await message.answer(tr(message.from_user.id, "phone_wrong"), reply_markup=contact_request_kb(message.from_user.id))


@router.message(OrderState.waiting_location, F.location)
async def order_location(message: Message, state: FSMContext) -> None:
    await state.update_data(location_lat=message.location.latitude, location_lon=message.location.longitude)
    await state.set_state(OrderState.waiting_payment)
    await message.answer(tr(message.from_user.id, "choose_payment"), reply_markup=payment_choice_kb(message.from_user.id))


@router.message(OrderState.waiting_location)
async def order_location_wrong(message: Message) -> None:
    await message.answer(tr(message.from_user.id, "location_wrong"), reply_markup=location_request_kb(message.from_user.id))


@router.message(OrderState.waiting_payment)
async def order_payment(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    books = load_books()
    book = next((b for b in books if b["id"] == data.get("book_id")), None)
    if not book:
        await state.clear()
        await message.answer("Kitob topilmadi.", reply_markup=main_menu(message.from_user.id))
        return

    payment_type = "Payme" if "Payme" in (message.text or "") else ("Naqd" if get_lang(message.from_user.id) == "uz" else "Наличные")
    latitude = data.get("location_lat")
    longitude = data.get("location_lon")
    location_url = f"https://maps.google.com/?q={latitude},{longitude}" if latitude is not None and longitude is not None else ""

    order = {
        "user_id": message.from_user.id,
        "tg_id": message.from_user.id,
        "username": message.from_user.username or "",
        "full_name": message.from_user.full_name or "",
        "customer_name": data.get("customer_name", ""),
        "phone": data.get("phone", ""),
        "book_name": book["name"],
        "price": book["price"],
        "payment": payment_type,
        "location_lat": latitude,
        "location_lon": longitude,
        "location_url": location_url,
    }

    orders = load_orders()
    orders.append(order)
    save_orders(orders)

    username_text = f"@{message.from_user.username}" if message.from_user.username else "no_username"
    location_line = f"\n📍 Lokatsiya / Локация: <a href='{location_url}'>Google Maps</a>" if location_url else ""
    admin_text = (
        f"📦 <b>Yangi buyurtma / Новый заказ</b>\n\n"
        f"📚 Kitob / Книга: <b>{book['name']}</b>\n"
        f"💰 Narx / Цена: <b>{book['price']} so‘m</b>\n"
        f"💳 To‘lov / Оплата: <b>{payment_type}</b>\n"
        f"👤 Ism / Имя: <b>{data.get('customer_name', '')}</b>\n"
        f"📞 Telefon / Телефон: <b>{data.get('phone', '')}</b>\n"
        f"🆔 TG ID: <code>{message.from_user.id}</code>\n"
        f"👤 Username: {username_text}"
        f"{location_line}"
    )

    # Bot ichiga ham
    await message.answer(admin_text)
    # Shaxsiy admin chatga ham
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=admin_text)
    except Exception:
        logging.exception("Admin ID ga buyurtma yuborilmadi")

    await message.answer(tr(message.from_user.id, "order_saved"), reply_markup=main_menu(message.from_user.id))
    await state.clear()


@router.message(F.text.in_([TEXTS["uz"]["payment"], TEXTS["ru"]["payment"]]))
async def payment_info(message: Message) -> None:
    await message.answer(tr(message.from_user.id, "payment_text"))


@router.message(F.text.in_([TEXTS["uz"]["delivery"], TEXTS["ru"]["delivery"]]))
async def delivery_info(message: Message) -> None:
    await message.answer(tr(message.from_user.id, "delivery_text"))


@router.message(F.text.in_([TEXTS["uz"]["contact"], TEXTS["ru"]["contact"]]))
async def contact_info(message: Message) -> None:
    text = tr(message.from_user.id, "contact_text", admin=ADMIN_USERNAME, card=PAYMENT_CARD, holder=CARD_HOLDER)
    await message.answer(text)
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=f"☎️ Murojaat / Обращение\n\n🆔 {message.from_user.id}\n👤 @{message.from_user.username or 'no_username'}")
    except Exception:
        logging.exception("Admin ID ga murojaat yuborilmadi")


@router.message(F.text.in_([TEXTS["uz"]["admin"], TEXTS["ru"]["admin"]]))
async def admin_panel(message: Message) -> None:
    if not is_admin(message):
        await message.answer(tr(message.from_user.id, "admin_not_allowed"))
        return
    await message.answer(tr(message.from_user.id, "admin_panel"), reply_markup=admin_menu(message.from_user.id))


@router.message(F.text.in_([TEXTS["uz"]["ordinary_menu"], TEXTS["ru"]["ordinary_menu"]]))
async def ordinary_menu(message: Message) -> None:
    await message.answer(tr(message.from_user.id, "welcome"), reply_markup=main_menu(message.from_user.id))


@router.message(F.text.in_([TEXTS["uz"]["stats"], TEXTS["ru"]["stats"]]))
async def admin_stats(message: Message) -> None:
    if not is_admin(message):
        await message.answer(tr(message.from_user.id, "admin_not_allowed"))
        return
    users_count = len(load_users())
    books_count = len(load_books())
    orders_count = len(load_orders())
    await message.answer(
        tr(message.from_user.id, "stats_text", users=users_count, books=books_count, orders=orders_count)
    )


@router.message(F.text.in_([TEXTS["uz"]["book_list"], TEXTS["ru"]["book_list"]]))
async def admin_book_list(message: Message) -> None:
    if not is_admin(message):
        await message.answer(tr(message.from_user.id, "admin_not_allowed"))
        return
    books = load_books()
    if not books:
        await message.answer(tr(message.from_user.id, "book_empty"))
        return
    lines = []
    for b in books:
        lines.append(f"{b['id']}. {b['name']} | {b['price']} so'm")
    await message.answer("\n".join(lines))


@router.message(F.text.in_([TEXTS["uz"]["orders"], TEXTS["ru"]["orders"]]))
async def admin_orders(message: Message) -> None:
    if not is_admin(message):
        await message.answer(tr(message.from_user.id, "admin_not_allowed"))
        return
    orders = load_orders()
    if not orders:
        await message.answer("Buyurtmalar yo'q.")
        return
    parts: List[str] = []
    for i, o in enumerate(orders[-20:], start=1):
        username_text = f"@{o['username']}" if o.get("username") else "no_username"
        location_text = o.get("location_url") or (
            f"https://maps.google.com/?q={o.get('location_lat')},{o.get('location_lon')}"
            if o.get("location_lat") is not None and o.get("location_lon") is not None else "yo'q"
        )
        parts.append(
            f"{i}. 📚 {o['book_name']} | 💰 {o['price']} so‘m | 💳 {o['payment']}\n"
            f"👤 {o['customer_name']} | 📞 {o['phone']}\n"
            f"🆔 {o.get('tg_id', o.get('user_id', ''))} | {username_text}\n"
            f"📍 {location_text}"
        )
    await message.answer("\n\n".join(parts))


@router.message(F.text.in_([TEXTS["uz"]["add_book"], TEXTS["ru"]["add_book"]]))
async def add_book_start(message: Message, state: FSMContext) -> None:
    if not is_admin(message):
        await message.answer(tr(message.from_user.id, "admin_not_allowed"))
        return
    await state.set_state(AddBookState.waiting_name)
    await message.answer(tr(message.from_user.id, "enter_book_name"), reply_markup=ReplyKeyboardRemove())


@router.message(AddBookState.waiting_name)
async def add_book_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=(message.text or "").strip())
    await state.set_state(AddBookState.waiting_price)
    await message.answer(tr(message.from_user.id, "enter_book_price"))


@router.message(AddBookState.waiting_price)
async def add_book_price(message: Message, state: FSMContext) -> None:
    price = "".join(ch for ch in (message.text or "") if ch.isdigit())
    if not price:
        await message.answer(tr(message.from_user.id, "enter_book_price"))
        return
    await state.update_data(price=price)
    await state.set_state(AddBookState.waiting_desc)
    await message.answer(tr(message.from_user.id, "enter_book_desc"))


@router.message(AddBookState.waiting_desc)
async def add_book_desc(message: Message, state: FSMContext) -> None:
    await state.update_data(desc=(message.text or "").strip())
    await state.set_state(AddBookState.waiting_photo)
    await message.answer(tr(message.from_user.id, "enter_book_photo"))


@router.message(AddBookState.waiting_photo, F.photo)
async def add_book_photo(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    books = load_books()
    new_id = max([b.get("id", 0) for b in books], default=0) + 1

    photo_dir = BASE_DIR / "uploads"
    photo_dir.mkdir(exist_ok=True)
    file_path = photo_dir / f"book_{new_id}.jpg"
    await bot.download(message.photo[-1], destination=file_path)

    books.append(
        {
            "id": new_id,
            "name": data.get("name", ""),
            "price": data.get("price", ""),
            "desc": data.get("desc", ""),
            "photo": str(file_path),
        }
    )
    save_books(books)
    await state.clear()
    await message.answer(tr(message.from_user.id, "book_added"), reply_markup=admin_menu(message.from_user.id))


@router.message(AddBookState.waiting_photo)
async def add_book_photo_wrong(message: Message) -> None:
    await message.answer("Rasm yuboring.")


@router.message(F.text.in_([TEXTS["uz"]["delete_book"], TEXTS["ru"]["delete_book"]]))
async def delete_book_menu(message: Message) -> None:
    if not is_admin(message):
        await message.answer(tr(message.from_user.id, "admin_not_allowed"))
        return
    books = load_books()
    if not books:
        await message.answer(tr(message.from_user.id, "book_empty"))
        return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{b['name']} ({b['price']})", callback_data=f"del:{b['id']}")]
            for b in books
        ]
    )
    await message.answer(tr(message.from_user.id, "choose_delete_book"), reply_markup=kb)


@router.callback_query(F.data.startswith("del:"))
async def delete_book(call: CallbackQuery) -> None:
    if not is_admin(call.message):
        await call.answer("No admin", show_alert=True)
        return
    try:
        book_id = int(call.data.split(":")[1])
    except Exception:
        await call.answer("Xato", show_alert=True)
        return

    books = load_books()
    new_books = [b for b in books if b["id"] != book_id]
    save_books(new_books)
    await call.message.answer(tr(call.from_user.id, "book_deleted"))
    await call.answer()


async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
