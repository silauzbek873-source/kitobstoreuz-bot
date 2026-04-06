import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any

from aiogram import Bot, Dispatcher, Router, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardRemove,
)
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

logging.basicConfig(level=logging.INFO)

BASE_DIR = Path(__file__).resolve().parent
BOOKS_FILE = BASE_DIR / "books.json"
USERS_FILE = BASE_DIR / "users.json"
ORDERS_FILE = BASE_DIR / "orders.json"

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "abdullayevv_tm").lstrip("@").strip()
PAYMENT_CARD = os.getenv("PAYMENT_CARD", "5614 6814 0959 5364").strip()
CARD_HOLDER = os.getenv("CARD_HOLDER", "Abdullayev Saidaxmad").strip()
BRAND_NAME = os.getenv("BRAND_NAME", "KitobStoreUz").strip()

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN topilmadi. Railway Variables ichiga BOT_TOKEN qo'shing.")


def ensure_file(path: Path, default_data: Any):
    if not path.exists():
        path.write_text(json.dumps(default_data, ensure_ascii=False, indent=2), encoding="utf-8")


ensure_file(BOOKS_FILE, [])
ensure_file(USERS_FILE, {})
ensure_file(ORDERS_FILE, [])


def load_json(path: Path, default: Any):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, data: Any):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_books() -> List[Dict]:
    return load_json(BOOKS_FILE, [])


def save_books(data: List[Dict]):
    save_json(BOOKS_FILE, data)


def load_users() -> Dict[str, Dict]:
    return load_json(USERS_FILE, {})


def save_users(data: Dict[str, Dict]):
    save_json(USERS_FILE, data)


def load_orders() -> List[Dict]:
    return load_json(ORDERS_FILE, [])


def save_orders(data: List[Dict]):
    save_json(ORDERS_FILE, data)


TEXTS = {
    "uz": {
        "choose_lang": "Tilni tanlang:",
        "lang_set": "✅ Til o‘rnatildi: O‘zbekcha",
        "welcome": (
            f"📚 Assalomu alaykum!\n\n"
            f"Siz {BRAND_NAME} botidasiz 👋\n\n"
            f"Bu yerda siz:\n"
            f"🧠 Fikrni o‘zgartiradigan kitoblar\n"
            f"💸 Qulay narxlar\n"
            f"🚚 Tez yetkazib berish\n\n"
            f"👇 Quyidagi tugmalardan foydalaning:"
        ),
        "books": "📚 Kitoblar",
        "order": "🛒 Buyurtma berish",
        "payment": "💳 To‘lov",
        "delivery": "🚚 Yetkazib berish",
        "contact": "📩 Murojaat",
        "admin": "👨‍💼 Admin",
        "no_books": "📚 Hozircha kitoblar qo‘shilmagan.",
        "choose_book": "Quyidagilardan birini tanlang:",
        "buy": "🛒 Sotib olish",
        "order_need_books": "🛒 Buyurtma uchun avval kitob qo‘shilishi kerak.",
        "payment_info": (
            "💳 To‘lov usullari:\n\n"
            "• Payme\n"
            "• Naqd\n\n"
            "Buyurtma jarayonida to‘lov turi tanlanadi."
        ),
        "delivery_info": "🚚 Yetkazib berish:\n\n📍 Toshkent: 1 kun\n📦 Viloyatlar: 1-3 kun",
        "contact_prompt": "✍️ Xabaringizni yuboring. Men uni adminga yetkazaman.",
        "contact_sent": "✅ Xabaringiz adminga yuborildi.",
        "admin_only": "⛔ Bu bo‘lim faqat admin uchun.",
        "admin_panel": "⚙️ Admin panel",
        "add_book": "➕ Kitob qo‘shish",
        "delete_book": "🗑 Kitob o‘chirish",
        "book_list": "📚 Kitoblar ro‘yxati",
        "orders": "📦 Buyurtmalar",
        "stats": "📊 Statistika",
        "normal_menu": "🏠 Oddiy menyu",
        "send_book_name": "Kitob nomini yuboring:",
        "send_book_price": "Narxini yuboring (faqat raqam):",
        "send_book_photo": "Endi kitob rasmini yuboring. Agar rasm bo‘lmasa /skip yozing.",
        "book_saved": "✅ Kitob qo‘shildi.",
        "bad_price": "❗ Narxni faqat raqam bilan yuboring. Masalan: 50000",
        "choose_delete_book": "O‘chirmoqchi bo‘lgan kitobni tanlang:",
        "book_deleted": "🗑 Kitob o‘chirildi.",
        "no_orders": "📦 Hozircha buyurtmalar yo‘q.",
        "stats_text": "📊 Statistika:\n\n👥 Foydalanuvchilar: {users}\n📚 Kitoblar: {books}\n📦 Buyurtmalar: {orders}",
        "enter_name": "👤 Ismingizni yuboring:",
        "enter_phone": "📞 Telefon raqamingizni yuboring:",
        "choose_payment": "💳 To‘lov turini tanlang:",
        "payme": "💳 Payme",
        "cash": "💵 Naqd",
        "order_confirmed": "✅ Buyurtmangiz qabul qilindi. Tez orada siz bilan bog‘lanamiz.",
        "payme_info": (
            "💳 Online to‘lov\n\n"
            f"Karta: {PAYMENT_CARD}\n"
            f"Qabul qiluvchi: {CARD_HOLDER}\n\n"
            "✅ To‘lov qilgandan keyin chek skrinshotini yuboring."
        ),
        "start_over": "🔄 Qayta boshlash uchun /start ni bosing.",
    },
    "ru": {
        "choose_lang": "Выберите язык:",
        "lang_set": "✅ Язык установлен: Русский",
        "welcome": (
            f"📚 Добро пожаловать!\n\n"
            f"Вы в боте {BRAND_NAME} 👋\n\n"
            f"Здесь вы найдете:\n"
            f"🧠 Книги, меняющие мышление\n"
            f"💸 Доступные цены\n"
            f"🚚 Быстрая доставка\n\n"
            f"👇 Используйте кнопки ниже:"
        ),
        "books": "📚 Книги",
        "order": "🛒 Заказать",
        "payment": "💳 Оплата",
        "delivery": "🚚 Доставка",
        "contact": "📩 Связаться",
        "admin": "👨‍💼 Админ",
        "no_books": "📚 Пока книги не добавлены.",
        "choose_book": "Выберите одну из книг:",
        "buy": "🛒 Купить",
        "order_need_books": "🛒 Сначала нужно добавить книги.",
        "payment_info": (
            "💳 Способы оплаты:\n\n"
            "• Payme\n"
            "• Наличные\n\n"
            "Способ оплаты выбирается во время заказа."
        ),
        "delivery_info": "🚚 Доставка:\n\n📍 Ташкент: 1 день\n📦 Регионы: 1-3 дня",
        "contact_prompt": "✍️ Отправьте ваше сообщение. Я передам его админу.",
        "contact_sent": "✅ Сообщение отправлено админу.",
        "admin_only": "⛔ Этот раздел только для администратора.",
        "admin_panel": "⚙️ Админ-панель",
        "add_book": "➕ Добавить книгу",
        "delete_book": "🗑 Удалить книгу",
        "book_list": "📚 Список книг",
        "orders": "📦 Заказы",
        "stats": "📊 Статистика",
        "normal_menu": "🏠 Обычное меню",
        "send_book_name": "Отправьте название книги:",
        "send_book_price": "Отправьте цену (только цифры):",
        "send_book_photo": "Теперь отправьте фото книги. Если фото нет, отправьте /skip.",
        "book_saved": "✅ Книга добавлена.",
        "bad_price": "❗ Отправьте цену только цифрами. Например: 50000",
        "choose_delete_book": "Выберите книгу для удаления:",
        "book_deleted": "🗑 Книга удалена.",
        "no_orders": "📦 Заказов пока нет.",
        "stats_text": "📊 Статистика:\n\n👥 Пользователи: {users}\n📚 Книги: {books}\n📦 Заказы: {orders}",
        "enter_name": "👤 Отправьте ваше имя:",
        "enter_phone": "📞 Отправьте номер телефона:",
        "choose_payment": "💳 Выберите способ оплаты:",
        "payme": "💳 Payme",
        "cash": "💵 Наличные",
        "order_confirmed": "✅ Ваш заказ принят. Мы скоро с вами свяжемся.",
        "payme_info": (
            "💳 Онлайн-оплата\n\n"
            f"Карта: {PAYMENT_CARD}\n"
            f"Получатель: {CARD_HOLDER}\n\n"
            "✅ После оплаты отправьте скриншот чека."
        ),
        "start_over": "🔄 Чтобы начать заново, нажмите /start.",
    },
}


def users_db():
    return load_users()


def get_lang(user_id: int) -> str:
    users = users_db()
    return users.get(str(user_id), {}).get("lang", "uz")


def set_lang(user_id: int, lang: str):
    users = users_db()
    item = users.get(str(user_id), {})
    item["lang"] = lang
    users[str(user_id)] = item
    save_users(users)


def remember_user(message: Message):
    users = users_db()
    users[str(message.from_user.id)] = {
        "tg_id": message.from_user.id,
        "username": message.from_user.username or "",
        "full_name": message.from_user.full_name or "",
        "lang": users.get(str(message.from_user.id), {}).get("lang", "uz"),
    }
    save_users(users)


def tr(user_id: int, key: str, **kwargs) -> str:
    text = TEXTS[get_lang(user_id)][key]
    return text.format(**kwargs) if kwargs else text


def is_admin(message: Message) -> bool:
    return (message.from_user.username or "").lstrip("@").lower() == ADMIN_USERNAME.lower()


def language_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🇺🇿 O‘zbekcha"), KeyboardButton(text="🇷🇺 Русский")]],
        resize_keyboard=True
    )


def main_menu(user_id: int):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=tr(user_id, "books")), KeyboardButton(text=tr(user_id, "order"))],
            [KeyboardButton(text=tr(user_id, "payment")), KeyboardButton(text=tr(user_id, "delivery"))],
            [KeyboardButton(text=tr(user_id, "contact")), KeyboardButton(text=tr(user_id, "admin"))],
        ],
        resize_keyboard=True
    )


def admin_menu(user_id: int):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=tr(user_id, "add_book")), KeyboardButton(text=tr(user_id, "delete_book"))],
            [KeyboardButton(text=tr(user_id, "book_list")), KeyboardButton(text=tr(user_id, "orders"))],
            [KeyboardButton(text=tr(user_id, "stats")), KeyboardButton(text=tr(user_id, "normal_menu"))],
        ],
        resize_keyboard=True
    )


def payment_choice_kb(user_id: int):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=tr(user_id, "payme")), KeyboardButton(text=tr(user_id, "cash"))]],
        resize_keyboard=True, one_time_keyboard=True
    )


def phone_request_kb(user_id: int):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=tr(user_id, "enter_phone"), request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def location_request_kb(user_id: int):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=("📍 Joylashuvni yuborish" if get_lang(user_id) == "uz" else "📍 Отправить локацию"), request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def buy_inline_kb(book_id: int, user_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=tr(user_id, "buy"), callback_data=f"buy:{book_id}")]]
    )


class ContactState(StatesGroup):
    waiting_message = State()


class AddBookState(StatesGroup):
    waiting_name = State()
    waiting_price = State()
    waiting_photo = State()


class OrderState(StatesGroup):
    waiting_name = State()
    waiting_phone = State()
    waiting_location = State()


router = Router()
bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
dp.include_router(router)


@router.message(Command("start"))
async def start_cmd(message: Message, state: FSMContext):
    remember_user(message)
    await state.clear()
    await message.answer(
        f"🆔 Telegram ID avtomatik olindi: <code>{message.from_user.id}</code>\n"
        f"👤 Username: @{message.from_user.username or 'no_username'}\n\n"
        "Tilni tanlang / Выберите язык:",
        reply_markup=language_kb()
    )


@router.message(F.text.in_(["🇺🇿 O‘zbekcha", "🇷🇺 Русский"]))
async def choose_language(message: Message, state: FSMContext):
    remember_user(message)
    set_lang(message.from_user.id, "uz" if "O‘zbekcha" in message.text else "ru")
    await state.clear()
    await message.answer(
        tr(message.from_user.id, "lang_set") + "\n\n" + tr(message.from_user.id, "welcome"),
        reply_markup=main_menu(message.from_user.id)
    )


@router.message(Command("admin"))
async def admin_cmd(message: Message, state: FSMContext):
    remember_user(message)
    await state.clear()
    if not is_admin(message):
        await message.answer(tr(message.from_user.id, "admin_only"))
        return
    await message.answer(tr(message.from_user.id, "admin_panel"), reply_markup=admin_menu(message.from_user.id))


@router.message(F.text.func(lambda x: x in ["👨‍💼 Admin", "👨‍💼 Админ"]))
async def admin_menu_open(message: Message, state: FSMContext):
    await admin_cmd(message, state)


@router.message(F.text.func(lambda x: x in ["🏠 Oddiy menyu", "🏠 Обычное меню"]))
async def normal_menu_back(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(tr(message.from_user.id, "welcome"), reply_markup=main_menu(message.from_user.id))


@router.message(F.text.func(lambda x: x in ["📚 Kitoblar", "📚 Книги"]))
async def list_books(message: Message):
    remember_user(message)
    books = load_books()
    if not books:
        await message.answer(tr(message.from_user.id, "no_books"))
        return
    await message.answer(tr(message.from_user.id, "choose_book"))
    for book in books:
        caption = f"📚 <b>{book['name']}</b>\n💰 {book['price']} so‘m"
        if book.get("photo_file_id"):
            await message.answer_photo(photo=book["photo_file_id"], caption=caption, reply_markup=buy_inline_kb(book["id"], message.from_user.id))
        else:
            await message.answer(caption, reply_markup=buy_inline_kb(book["id"], message.from_user.id))


@router.message(F.text.func(lambda x: x in ["🛒 Buyurtma berish", "🛒 Заказать"]))
async def order_entry(message: Message):
    if not load_books():
        await message.answer(tr(message.from_user.id, "order_need_books"))
        return
    await list_books(message)


@router.callback_query(F.data.startswith("buy:"))
async def buy_callback(callback: CallbackQuery, state: FSMContext):
    book_id = int(callback.data.split(":")[1])
    book = next((b for b in load_books() if b["id"] == book_id), None)
    if not book:
        await callback.answer("Book not found", show_alert=True)
        return
    await state.set_state(OrderState.waiting_name)
    await state.update_data(book_id=book_id)
    await callback.message.answer(tr(callback.from_user.id, "enter_name"), reply_markup=ReplyKeyboardRemove())
    await callback.answer()


@router.message(OrderState.waiting_name)
async def order_name(message: Message, state: FSMContext):
    await state.update_data(customer_name=message.text.strip())
    await state.set_state(OrderState.waiting_phone)
    await message.answer(tr(message.from_user.id, "enter_phone"), reply_markup=phone_request_kb(message.from_user.id))


@router.message(OrderState.waiting_phone, F.contact)
async def order_phone_contact(message: Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await state.set_state(OrderState.waiting_location)
    prompt = "📍 Joylashuvingizni yuboring:" if get_lang(message.from_user.id) == "uz" else "📍 Отправьте вашу локацию:"
    await message.answer(prompt, reply_markup=location_request_kb(message.from_user.id))


@router.message(OrderState.waiting_phone)
async def order_phone_wrong(message: Message):
    await message.answer(tr(message.from_user.id, "enter_phone"), reply_markup=phone_request_kb(message.from_user.id))


@router.message(OrderState.waiting_location, F.location)
async def order_location(message: Message, state: FSMContext):
    data = await state.get_data()
    book = next((b for b in load_books() if b["id"] == data.get("book_id")), None)
    if not book:
        await state.clear()
        await message.answer(tr(message.from_user.id, "start_over"), reply_markup=main_menu(message.from_user.id))
        return

    latitude = message.location.latitude
    longitude = message.location.longitude

    order = {
        "user_id": message.from_user.id,
        "tg_id": message.from_user.id,
        "username": message.from_user.username or "",
        "full_name": message.from_user.full_name or "",
        "customer_name": data.get("customer_name", ""),
        "phone": data.get("phone", ""),
        "book_name": book["name"],
        "price": book["price"],
        "location": {"latitude": latitude, "longitude": longitude},
    }
    orders = load_orders()
    orders.append(order)
    save_orders(orders)

    admin_text = (
        f"📦 <b>Yangi buyurtma / Новый заказ</b>\n\n"
        f"📚 Kitob / Книга: <b>{book['name']}</b>\n"
        f"💰 Narx / Цена: <b>{book['price']} so‘m</b>\n"
        f"👤 Ism / Имя: <b>{data.get('customer_name', '')}</b>\n"
        f"📞 Telefon / Телефон: <b>{data.get('phone', '')}</b>\n"
        f"🆔 TG ID: <code>{message.from_user.id}</code>\n"
        f"👤 Username: @{message.from_user.username or 'no_username'}\n"
        f"📍 Lokatsiya / Локация: {latitude}, {longitude}\n"
        f"🗺 Xarita / Карта: https://maps.google.com/?q={latitude},{longitude}"
    )
    try:
        await bot.send_message(chat_id=f"@{ADMIN_USERNAME}", text=admin_text)
    except Exception:
        logging.exception("Admin username ga buyurtma yuborilmadi")

    await message.answer(tr(message.from_user.id, "order_confirmed"), reply_markup=main_menu(message.from_user.id))
    await state.clear()


@router.message(OrderState.waiting_location)
async def order_location_wrong(message: Message):
    prompt = "📍 Joylashuvingizni yuboring:" if get_lang(message.from_user.id) == "uz" else "📍 Отправьте вашу локацию:"
    await message.answer(prompt, reply_markup=location_request_kb(message.from_user.id))


@router.message(F.text.func(lambda x: x in ["💳 To‘lov", "💳 Оплата"]))
async def payment_info(message: Message):
    await message.answer(tr(message.from_user.id, "payment_info"))


@router.message(F.text.func(lambda x: x in ["🚚 Yetkazib berish", "🚚 Доставка"]))
async def delivery_info(message: Message):
    await message.answer(tr(message.from_user.id, "delivery_info"))


@router.message(F.text.func(lambda x: x in ["📩 Murojaat", "📩 Связаться"]))
async def contact_start(message: Message, state: FSMContext):
    await state.set_state(ContactState.waiting_message)
    await message.answer(tr(message.from_user.id, "contact_prompt"), reply_markup=ReplyKeyboardRemove())


@router.message(ContactState.waiting_message)
async def contact_send(message: Message, state: FSMContext):
    text = (
        f"📩 <b>Murojaat / Обращение</b>\n\n"
        f"👤 {message.from_user.full_name}\n"
        f"🆔 @{message.from_user.username or 'no_username'}\n\n"
        f"{message.text}"
    )
    try:
        await bot.send_message(chat_id=f"@{ADMIN_USERNAME}", text=text)
    except Exception:
        logging.exception("Admin username ga murojaat yuborilmadi")
    await message.answer(tr(message.from_user.id, "contact_sent"), reply_markup=main_menu(message.from_user.id))
    await state.clear()


@router.message(F.text.func(lambda x: x in ["➕ Kitob qo‘shish", "➕ Добавить книгу"]))
async def add_book_start(message: Message, state: FSMContext):
    if not is_admin(message):
        await message.answer(tr(message.from_user.id, "admin_only"))
        return
    await state.set_state(AddBookState.waiting_name)
    await message.answer(tr(message.from_user.id, "send_book_name"), reply_markup=ReplyKeyboardRemove())


@router.message(AddBookState.waiting_name)
async def add_book_name(message: Message, state: FSMContext):
    await state.update_data(book_name=message.text.strip())
    await state.set_state(AddBookState.waiting_price)
    await message.answer(tr(message.from_user.id, "send_book_price"))


@router.message(AddBookState.waiting_price)
async def add_book_price(message: Message, state: FSMContext):
    raw = message.text.strip().replace(" ", "")
    if not raw.isdigit():
        await message.answer(tr(message.from_user.id, "bad_price"))
        return
    await state.update_data(book_price=int(raw))
    await state.set_state(AddBookState.waiting_photo)
    await message.answer(tr(message.from_user.id, "send_book_photo"))


@router.message(AddBookState.waiting_photo, Command("skip"))
async def add_book_skip_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    books = load_books()
    new_id = max([b["id"] for b in books], default=0) + 1
    books.append({"id": new_id, "name": data["book_name"], "price": data["book_price"], "photo_file_id": None})
    save_books(books)
    await state.clear()
    await message.answer(tr(message.from_user.id, "book_saved"), reply_markup=admin_menu(message.from_user.id))


@router.message(AddBookState.waiting_photo, F.photo)
async def add_book_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    books = load_books()
    new_id = max([b["id"] for b in books], default=0) + 1
    books.append({"id": new_id, "name": data["book_name"], "price": data["book_price"], "photo_file_id": message.photo[-1].file_id})
    save_books(books)
    await state.clear()
    await message.answer(tr(message.from_user.id, "book_saved"), reply_markup=admin_menu(message.from_user.id))


@router.message(AddBookState.waiting_photo)
async def add_book_photo_invalid(message: Message):
    await message.answer("Rasm yuboring yoki /skip yozing." if get_lang(message.from_user.id) == "uz" else "Отправьте фото или напишите /skip.")


@router.message(F.text.func(lambda x: x in ["📚 Kitoblar ro‘yxati", "📚 Список книг"]))
async def admin_book_list(message: Message):
    if not is_admin(message):
        await message.answer(tr(message.from_user.id, "admin_only"))
        return
    books = load_books()
    if not books:
        await message.answer(tr(message.from_user.id, "no_books"))
        return
    await message.answer("\n".join([f"{b['id']}. {b['name']} — {b['price']} so‘m" for b in books]))


@router.message(F.text.func(lambda x: x in ["🗑 Kitob o‘chirish", "🗑 Удалить книгу"]))
async def delete_book_prompt(message: Message):
    if not is_admin(message):
        await message.answer(tr(message.from_user.id, "admin_only"))
        return
    books = load_books()
    if not books:
        await message.answer(tr(message.from_user.id, "no_books"))
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=f"{b['name']} ({b['price']})", callback_data=f"del:{b['id']}")] for b in books])
    await message.answer(tr(message.from_user.id, "choose_delete_book"), reply_markup=kb)


@router.callback_query(F.data.startswith("del:"))
async def delete_book_callback(callback: CallbackQuery):
    if (callback.from_user.username or "").lstrip("@").lower() != ADMIN_USERNAME.lower():
        await callback.answer("Not allowed", show_alert=True)
        return
    book_id = int(callback.data.split(":")[1])
    books = [b for b in load_books() if b["id"] != book_id]
    save_books(books)
    await callback.message.answer(tr(callback.from_user.id, "book_deleted"), reply_markup=admin_menu(callback.from_user.id))
    await callback.answer()


@router.message(F.text.func(lambda x: x in ["📦 Buyurtmalar", "📦 Заказы"]))
async def admin_orders(message: Message):
    if not is_admin(message):
        await message.answer(tr(message.from_user.id, "admin_only"))
        return
    orders = load_orders()
    if not orders:
        await message.answer(tr(message.from_user.id, "no_orders"))
        return
    parts = []
    for i, o in enumerate(orders[-20:], start=1):
        parts.append(
            f"{i}. 📚 {o['book_name']} | 💰 {o['price']} so‘m | 💳 {o['payment']}\n"
            f"👤 {o['customer_name']} | 📞 {o['phone']} | @{o['username'] or 'no_username'}"
        )
    await message.answer("\n\n".join(parts))


@router.message(F.text.func(lambda x: x in ["📊 Statistika", "📊 Статистика"]))
async def admin_stats(message: Message):
    if not is_admin(message):
        await message.answer(tr(message.from_user.id, "admin_only"))
        return
    await message.answer(
        tr(message.from_user.id, "stats_text", users=len(load_users()), books=len(load_books()), orders=len(load_orders()))
    )


@router.message()
async def fallback(message: Message):
    remember_user(message)
    lang = get_lang(message.from_user.id)
    if lang not in ("uz", "ru"):
        await message.answer("Tilni tanlang / Выберите язык:", reply_markup=language_kb())
        return
    await message.answer(tr(message.from_user.id, "welcome"), reply_markup=main_menu(message.from_user.id))


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())