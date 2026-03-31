import asyncio
import json
import logging
import os
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any, Optional

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatType, ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "bot.db"
BOOKS_PATH = BASE_DIR / "books.json"

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "abdullayevv_tm").lstrip("@")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0") or 0)
BRAND_NAME = os.getenv("BRAND_NAME", "KitobStoreUz")
PAYMENT_CARD = os.getenv("PAYMENT_CARD", "5614 6814 0959 5364")
PAYMENT_OWNER = os.getenv("PAYMENT_OWNER", "Abdullayev Saidaxmad")
PAYMENT_METHOD_NAME = os.getenv("PAYMENT_METHOD_NAME", "Payme")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
router = Router()


class OrderStates(StatesGroup):
    waiting_name = State()
    waiting_phone = State()
    waiting_address = State()
    waiting_payment = State()
    waiting_receipt = State()


class ContactStates(StatesGroup):
    waiting_message = State()


class AdminAddBookStates(StatesGroup):
    waiting_photo = State()
    waiting_title = State()
    waiting_price = State()
    waiting_description = State()


class AdminDeleteBookStates(StatesGroup):
    waiting_book_id = State()


KEYWORDS = {"narx", "bormi", "buyurtma", "yetkazib", "admin", "kitob kerak", "olmoqchi", "sotib", "payme"}


def init_db() -> None:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                tg_name TEXT,
                book_id INTEGER,
                book_title TEXT NOT NULL,
                price INTEGER NOT NULL,
                customer_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                address TEXT NOT NULL,
                payment_type TEXT NOT NULL,
                receipt_file_id TEXT,
                status TEXT NOT NULL DEFAULT 'new',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                last_seen TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def track_user(message: Message) -> None:
    user = message.from_user
    if not user:
        return
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            """
            INSERT INTO users(user_id, username, full_name, last_seen)
            VALUES(?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
              username=excluded.username,
              full_name=excluded.full_name,
              last_seen=CURRENT_TIMESTAMP
            """,
            (user.id, user.username, user.full_name),
        )
        conn.commit()


def set_setting(key: str, value: str) -> None:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.execute(
            "INSERT INTO settings(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        conn.commit()


def get_setting(key: str) -> Optional[str]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row[0] if row else None


def load_books() -> list[dict[str, Any]]:
    if not BOOKS_PATH.exists():
        return []
    with open(BOOKS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        return []
    return data


def save_books(books: list[dict[str, Any]]) -> None:
    with open(BOOKS_PATH, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)


def next_book_id(books: list[dict[str, Any]]) -> int:
    return max((int(book.get("id", 0)) for book in books), default=0) + 1


def get_book(book_id: int) -> Optional[dict[str, Any]]:
    for book in load_books():
        if int(book.get("id", 0)) == book_id:
            return book
    return None


def delete_book(book_id: int) -> bool:
    books = load_books()
    new_books = [b for b in books if int(b.get("id", 0)) != book_id]
    if len(new_books) == len(books):
        return False
    save_books(new_books)
    return True


def is_admin(message: Message) -> bool:
    username_ok = bool(message.from_user.username and message.from_user.username.lower() == ADMIN_USERNAME.lower())
    id_ok = bool(ADMIN_USER_ID and message.from_user.id == ADMIN_USER_ID)
    return username_ok or id_ok


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 Kitoblar"), KeyboardButton(text="🛒 Buyurtma berish")],
            [KeyboardButton(text="💳 To'lov"), KeyboardButton(text="📩 Murojaat")],
            [KeyboardButton(text="🚚 Yetkazib berish"), KeyboardButton(text="👨‍💼 Admin bilan bog'lanish")],
        ],
        resize_keyboard=True,
    )


def admin_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Kitob qo'shish"), KeyboardButton(text="🗑 Kitob o'chirish")],
            [KeyboardButton(text="📚 Kitoblar ro'yxati"), KeyboardButton(text="📦 Buyurtmalar")],
            [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="🏠 Oddiy menyu")],
        ],
        resize_keyboard=True,
    )


def books_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for book in load_books():
        kb.button(text=f"📖 {book['title']}", callback_data=f"view_book:{book['id']}")
    kb.adjust(1)
    return kb.as_markup()


def book_card_keyboard(book_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🛒 Sotib olish", callback_data=f"buy:{book_id}")
    kb.button(text="⬅️ Orqaga", callback_data="books_back")
    kb.adjust(1)
    return kb.as_markup()


def payment_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💳 Payme"), KeyboardButton(text="💵 Naqd")],
            [KeyboardButton(text="❌ Bekor qilish")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def format_money(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def payment_text(total: int) -> str:
    return (
        f"💳 Online to'lov\n\n"
        f"To'lov usuli: {PAYMENT_METHOD_NAME}\n"
        f"Karta: {PAYMENT_CARD}\n"
        f"Qabul qiluvchi: {PAYMENT_OWNER}\n"
        f"Jami: {format_money(total)} so'm\n\n"
        f"✅ To'lov qilgandan keyin chek skrinshotini shu botga yuboring."
    )


def save_order(data: dict[str, Any], message: Message) -> int:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO orders(
                user_id, username, tg_name, book_id, book_title, price,
                customer_name, phone, address, payment_type, receipt_file_id, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message.from_user.id,
                message.from_user.username,
                message.from_user.full_name,
                data["book_id"],
                data["book_title"],
                data["price"],
                data["customer_name"],
                data["phone"],
                data["address"],
                data["payment_type"],
                data.get("receipt_file_id"),
                data.get("status", "new"),
            ),
        )
        conn.commit()
        return int(cur.lastrowid)


def order_count() -> int:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        row = conn.execute("SELECT COUNT(*) FROM orders").fetchone()
        return int(row[0] if row else 0)


def user_count() -> int:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        row = conn.execute("SELECT COUNT(*) FROM users").fetchone()
        return int(row[0] if row else 0)


def latest_orders(limit: int = 10) -> list[tuple]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        return conn.execute(
            """
            SELECT id, book_title, customer_name, phone, address, payment_type, status, created_at
            FROM orders ORDER BY id DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()


async def notify_admin(bot: Bot, text: str) -> None:
    admin_chat_id = get_setting("admin_chat_id")
    if admin_chat_id:
        try:
            await bot.send_message(int(admin_chat_id), text)
            return
        except Exception as e:
            logger.warning("Admin xabar yuborilmadi: %s", e)
    if ADMIN_USER_ID:
        try:
            await bot.send_message(ADMIN_USER_ID, text)
        except Exception as e:
            logger.warning("Fallback admin xabar yuborilmadi: %s", e)


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    track_user(message)
    if is_admin(message):
        set_setting("admin_chat_id", str(message.from_user.id))

    text = (
        f"Assalomu alaykum! {BRAND_NAME} botiga xush kelibsiz. 📚\n\n"
        "Bu yerda siz:\n"
        "• kitoblarni rasm va narxi bilan ko'rasiz\n"
        "• sotib olish uchun buyurtma qoldirasiz\n"
        "• murojaat yuborasiz\n\n"
        f"Admin: @{ADMIN_USERNAME}"
    )
    await message.answer(text, reply_markup=main_menu())


@router.message(Command("admin"))
async def admin_handler(message: Message) -> None:
    track_user(message)
    if not is_admin(message):
        await message.answer("Bu buyruq faqat admin uchun.")
        return
    set_setting("admin_chat_id", str(message.from_user.id))
    await message.answer("👨‍💼 Admin panel ochildi.", reply_markup=admin_menu())


@router.message(F.text == "🏠 Oddiy menyu")
async def back_user_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Oddiy menyuga qaytdingiz.", reply_markup=main_menu())


@router.message(F.text == "📚 Kitoblar")
async def show_books(message: Message) -> None:
    track_user(message)
    books = load_books()
    if not books:
        await message.answer("Hozircha kitoblar qo'shilmagan.")
        return
    await message.answer("📚 Mavjud kitoblar:", reply_markup=books_keyboard())


@router.callback_query(F.data == "books_back")
async def books_back(callback: CallbackQuery) -> None:
    await callback.message.answer("📚 Mavjud kitoblar:", reply_markup=books_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("view_book:"))
async def view_book(callback: CallbackQuery) -> None:
    book_id = int(callback.data.split(":", 1)[1])
    book = get_book(book_id)
    if not book:
        await callback.answer("Kitob topilmadi", show_alert=True)
        return

    text = (
        f"📚 <b>{book['title']}</b>\n"
        f"💰 Narxi: <b>{format_money(int(book['price']))} so'm</b>\n\n"
        f"{book.get('description') or 'Izoh kiritilmagan.'}"
    )
    if book.get("photo_file_id"):
        await callback.message.answer_photo(
            photo=book["photo_file_id"],
            caption=text,
            reply_markup=book_card_keyboard(book_id),
        )
    else:
        await callback.message.answer(text, reply_markup=book_card_keyboard(book_id))
    await callback.answer()


@router.message(F.text == "🛒 Buyurtma berish")
async def buy_entry(message: Message) -> None:
    track_user(message)
    books = load_books()
    if not books:
        await message.answer("Hozircha buyurtma uchun kitoblar qo'shilmagan.")
        return
    await message.answer("Quyidagi kitoblardan birini tanlang:", reply_markup=books_keyboard())


async def start_buy_flow(target: Message, state: FSMContext, book_id: int) -> None:
    book = get_book(book_id)
    if not book:
        await target.answer("Kitob topilmadi.")
        return
    await state.clear()
    await state.update_data(book_id=book_id, book_title=book["title"], price=int(book["price"]))
    await state.set_state(OrderStates.waiting_name)
    await target.answer(
        f"🛒 Buyurtma boshladi\n\n📚 Kitob: {book['title']}\n💰 Narx: {format_money(int(book['price']))} so'm\n\nIsm va familiyangizni kiriting:",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.callback_query(F.data.startswith("buy:"))
async def buy_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await start_buy_flow(callback.message, state, int(callback.data.split(":", 1)[1]))
    await callback.answer()


@router.message(OrderStates.waiting_name)
async def order_name(message: Message, state: FSMContext) -> None:
    await state.update_data(customer_name=message.text.strip())
    phone_kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Telefon yuborish", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await state.set_state(OrderStates.waiting_phone)
    await message.answer("Telefon raqamingizni yuboring yoki yozib kiriting:", reply_markup=phone_kb)


@router.message(OrderStates.waiting_phone, F.contact)
async def order_phone_contact(message: Message, state: FSMContext) -> None:
    await state.update_data(phone=message.contact.phone_number)
    await state.set_state(OrderStates.waiting_address)
    await message.answer("Yetkazib berish manzilini kiriting:", reply_markup=ReplyKeyboardRemove())


@router.message(OrderStates.waiting_phone)
async def order_phone_text(message: Message, state: FSMContext) -> None:
    await state.update_data(phone=message.text.strip())
    await state.set_state(OrderStates.waiting_address)
    await message.answer("Yetkazib berish manzilini kiriting:", reply_markup=ReplyKeyboardRemove())


@router.message(OrderStates.waiting_address)
async def order_address(message: Message, state: FSMContext) -> None:
    await state.update_data(address=message.text.strip())
    await state.set_state(OrderStates.waiting_payment)
    await message.answer("To'lov turini tanlang:", reply_markup=payment_keyboard())


@router.message(OrderStates.waiting_payment)
async def order_payment(message: Message, state: FSMContext, bot: Bot) -> None:
    payment = message.text.strip()
    if payment == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Jarayon bekor qilindi.", reply_markup=main_menu())
        return
    if payment not in {"💳 Payme", "💵 Naqd"}:
        await message.answer("Iltimos, 💳 Payme yoki 💵 Naqd ni tanlang.", reply_markup=payment_keyboard())
        return

    await state.update_data(payment_type="Payme" if payment == "💳 Payme" else "Naqd")
    data = await state.get_data()

    if payment == "💳 Payme":
        await state.set_state(OrderStates.waiting_receipt)
        await message.answer(payment_text(int(data["price"])), reply_markup=ReplyKeyboardRemove())
        pre_notice = (
            "🟡 Yangi Payme buyurtma boshlandi\n\n"
            f"📚 Kitob: {data['book_title']}\n"
            f"👤 Mijoz: {data['customer_name']}\n"
            f"📞 Telefon: {data['phone']}\n"
            f"📍 Manzil: {data['address']}\n"
            f"🔗 Username: @{message.from_user.username or 'yoq'}"
        )
        await notify_admin(bot, pre_notice)
        return

    data["status"] = "new"
    order_id = save_order(data, message)
    admin_text = (
        f"📦 Yangi buyurtma #{order_id}\n\n"
        f"📚 Kitob: {data['book_title']}\n"
        f"💰 Narx: {format_money(int(data['price']))} so'm\n"
        f"👤 Mijoz: {data['customer_name']}\n"
        f"📞 Telefon: {data['phone']}\n"
        f"📍 Manzil: {data['address']}\n"
        f"💳 To'lov: Naqd\n"
        f"🔗 Username: @{message.from_user.username or 'yoq'}"
    )
    await notify_admin(bot, admin_text)
    await message.answer(
        "✅ Buyurtmangiz qabul qilindi. Admin tez orada siz bilan bog'lanadi.",
        reply_markup=main_menu(),
    )
    await state.clear()


@router.message(OrderStates.waiting_receipt, F.photo)
async def order_receipt_photo(message: Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    data["receipt_file_id"] = message.photo[-1].file_id
    data["status"] = "paid_check_sent"
    order_id = save_order(data, message)

    admin_text = (
        f"✅ To'lov cheki bilan yangi buyurtma #{order_id}\n\n"
        f"📚 Kitob: {data['book_title']}\n"
        f"💰 Narx: {format_money(int(data['price']))} so'm\n"
        f"👤 Mijoz: {data['customer_name']}\n"
        f"📞 Telefon: {data['phone']}\n"
        f"📍 Manzil: {data['address']}\n"
        f"💳 To'lov: Payme\n"
        f"🔗 Username: @{message.from_user.username or 'yoq'}\n\n"
        "Chek rasmi pastda yuborildi."
    )
    await notify_admin(bot, admin_text)
    admin_chat_id = get_setting("admin_chat_id")
    if admin_chat_id:
        try:
            await bot.send_photo(int(admin_chat_id), data["receipt_file_id"], caption=f"Chek #{order_id}")
        except Exception as e:
            logger.warning("Admin chek rasmi yuborilmadi: %s", e)

    await message.answer(
        "✅ To'lov cheki qabul qilindi. Admin tekshiradi va siz bilan bog'lanadi.",
        reply_markup=main_menu(),
    )
    await state.clear()


@router.message(OrderStates.waiting_receipt)
async def order_receipt_need_photo(message: Message) -> None:
    await message.answer("Iltimos, to'lov chekini rasm sifatida yuboring.")


@router.message(F.text == "💳 To'lov")
async def payment_info(message: Message) -> None:
    await message.answer(
        "💳 Onlayn to'lov mavjud.\n"
        "Buyurtma jarayonida Payme tanlasangiz, bot karta ma'lumotini chiqaradi."
    )


@router.message(F.text == "🚚 Yetkazib berish")
async def delivery_info(message: Message) -> None:
    await message.answer(
        "🚚 Yetkazib berish:\n\n"
        "• Toshkent bo'ylab: 1 kun\n"
        "• Viloyatlarga: 1-3 kun\n"
        "• Buyurtma bo'yicha admin bog'lanadi"
    )


@router.message(F.text == "👨‍💼 Admin bilan bog'lanish")
async def direct_admin(message: Message) -> None:
    await message.answer(f"Admin bilan bog'lanish: @{ADMIN_USERNAME}")


@router.message(F.text == "📩 Murojaat")
async def contact_start(message: Message, state: FSMContext) -> None:
    track_user(message)
    await state.set_state(ContactStates.waiting_message)
    await message.answer("Murojaatingizni yozing. Men uni adminga yuboraman.", reply_markup=ReplyKeyboardRemove())


@router.message(ContactStates.waiting_message)
async def contact_receive(message: Message, state: FSMContext, bot: Bot) -> None:
    text = (
        "📩 Yangi murojaat\n\n"
        f"👤 Ism: {message.from_user.full_name}\n"
        f"🆔 ID: {message.from_user.id}\n"
        f"🔗 Username: @{message.from_user.username or 'yoq'}\n"
        f"💬 Xabar: {message.text}"
    )
    await notify_admin(bot, text)
    await message.answer("✅ Murojaatingiz adminga yuborildi.", reply_markup=main_menu())
    await state.clear()


@router.message(F.text == "➕ Kitob qo'shish")
async def admin_add_book_start(message: Message, state: FSMContext) -> None:
    if not is_admin(message):
        return
    await state.set_state(AdminAddBookStates.waiting_photo)
    await message.answer(
        "Kitob rasmini yuboring. Agar rasm bo'lmasa, /skip deb yozing.",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(AdminAddBookStates.waiting_photo, Command("skip"))
async def admin_skip_photo(message: Message, state: FSMContext) -> None:
    await state.update_data(photo_file_id="")
    await state.set_state(AdminAddBookStates.waiting_title)
    await message.answer("Kitob nomini kiriting:")


@router.message(AdminAddBookStates.waiting_photo, F.photo)
async def admin_add_photo(message: Message, state: FSMContext) -> None:
    await state.update_data(photo_file_id=message.photo[-1].file_id)
    await state.set_state(AdminAddBookStates.waiting_title)
    await message.answer("Kitob nomini kiriting:")


@router.message(AdminAddBookStates.waiting_photo)
async def admin_photo_required(message: Message) -> None:
    await message.answer("Rasm yuboring yoki /skip deb yozing.")


@router.message(AdminAddBookStates.waiting_title)
async def admin_add_title(message: Message, state: FSMContext) -> None:
    await state.update_data(title=message.text.strip())
    await state.set_state(AdminAddBookStates.waiting_price)
    await message.answer("Kitob narxini kiriting. Masalan: 45000")


@router.message(AdminAddBookStates.waiting_price)
async def admin_add_price(message: Message, state: FSMContext) -> None:
    price_text = message.text.strip().replace(" ", "")
    if not price_text.isdigit():
        await message.answer("Narxni faqat raqam bilan kiriting. Masalan: 45000")
        return
    await state.update_data(price=int(price_text))
    await state.set_state(AdminAddBookStates.waiting_description)
    await message.answer("Qisqa izoh kiriting. Agar kerak bo'lmasa /skip deb yozing.")


@router.message(AdminAddBookStates.waiting_description, Command("skip"))
async def admin_skip_description(message: Message, state: FSMContext) -> None:
    await save_admin_book(message, state, "")


@router.message(AdminAddBookStates.waiting_description)
async def admin_add_description(message: Message, state: FSMContext) -> None:
    await save_admin_book(message, state, message.text.strip())


async def save_admin_book(message: Message, state: FSMContext, description: str) -> None:
    data = await state.get_data()
    books = load_books()
    book = {
        "id": next_book_id(books),
        "title": data["title"],
        "price": int(data["price"]),
        "description": description,
        "photo_file_id": data.get("photo_file_id", ""),
    }
    books.append(book)
    save_books(books)
    await state.clear()
    await message.answer(
        f"✅ Kitob qo'shildi:\n\n📚 {book['title']}\n💰 {format_money(book['price'])} so'm",
        reply_markup=admin_menu(),
    )


@router.message(F.text == "📚 Kitoblar ro'yxati")
async def admin_books_list(message: Message) -> None:
    if not is_admin(message):
        return
    books = load_books()
    if not books:
        await message.answer("Hozircha kitoblar yo'q.", reply_markup=admin_menu())
        return
    lines = ["📚 Kitoblar ro'yxati:\n"]
    for book in books:
        lines.append(f"ID {book['id']} — {book['title']} — {format_money(int(book['price']))} so'm")
    await message.answer("\n".join(lines), reply_markup=admin_menu())


@router.message(F.text == "🗑 Kitob o'chirish")
async def admin_delete_start(message: Message, state: FSMContext) -> None:
    if not is_admin(message):
        return
    books = load_books()
    if not books:
        await message.answer("O'chirish uchun kitob yo'q.", reply_markup=admin_menu())
        return
    lines = ["O'chirish uchun ID ni yuboring:\n"]
    for book in books:
        lines.append(f"ID {book['id']} — {book['title']}")
    await state.set_state(AdminDeleteBookStates.waiting_book_id)
    await message.answer("\n".join(lines), reply_markup=ReplyKeyboardRemove())


@router.message(AdminDeleteBookStates.waiting_book_id)
async def admin_delete_finish(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if not text.isdigit():
        await message.answer("Iltimos, kitob ID raqamini yuboring.")
        return
    ok = delete_book(int(text))
    await state.clear()
    if ok:
        await message.answer("✅ Kitob o'chirildi.", reply_markup=admin_menu())
    else:
        await message.answer("Bunday ID topilmadi.", reply_markup=admin_menu())


@router.message(F.text == "📦 Buyurtmalar")
async def admin_orders(message: Message) -> None:
    if not is_admin(message):
        return
    rows = latest_orders(10)
    if not rows:
        await message.answer("Hozircha buyurtmalar yo'q.", reply_markup=admin_menu())
        return
    lines = ["📦 So'nggi buyurtmalar:\n"]
    for row in rows:
        order_id, book_title, customer_name, phone, address, payment_type, status, created_at = row
        lines.append(
            f"#{order_id} | {book_title}\n"
            f"👤 {customer_name} | 📞 {phone}\n"
            f"📍 {address}\n"
            f"💳 {payment_type} | 📌 {status} | 🕒 {created_at}\n"
        )
    await message.answer("\n".join(lines), reply_markup=admin_menu())


@router.message(F.text == "📊 Statistika")
async def admin_stats(message: Message) -> None:
    if not is_admin(message):
        return
    text = (
        "📊 Statistika\n\n"
        f"👥 Foydalanuvchilar: {user_count()}\n"
        f"📦 Buyurtmalar: {order_count()}\n"
        f"📚 Kitoblar: {len(load_books())}"
    )
    await message.answer(text, reply_markup=admin_menu())


@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Jarayon bekor qilindi.", reply_markup=main_menu())


@router.message(F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def group_signal(message: Message, bot: Bot) -> None:
    if not message.text:
        return
    lower = message.text.lower()
    if any(k in lower for k in KEYWORDS):
        alert = (
            "🚨 Muhokama guruhida qiziqqan odam topildi\n\n"
            f"👥 Guruh: {message.chat.title}\n"
            f"👤 Ism: {message.from_user.full_name}\n"
            f"🔗 Username: @{message.from_user.username or 'yoq'}\n"
            f"💬 Xabar: {message.text}"
        )
        await notify_admin(bot, alert)


@router.message()
async def fallback(message: Message) -> None:
    track_user(message)
    await message.answer("Kerakli bo'limni menyudan tanlang.", reply_markup=main_menu())


async def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN kiritilmagan")
    init_db()
    if not BOOKS_PATH.exists():
        save_books([])

    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
