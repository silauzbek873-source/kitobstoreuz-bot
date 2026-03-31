import asyncio
import json
import logging
import os
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Optional

from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ChatType, ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardButton,
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
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()


class OrderStates(StatesGroup):
    waiting_book = State()
    waiting_quantity = State()
    waiting_name = State()
    waiting_phone = State()
    waiting_address = State()
    waiting_delivery = State()
    waiting_payment = State()


class ContactStates(StatesGroup):
    waiting_message = State()


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
                full_name TEXT,
                book_title TEXT NOT NULL,
                price INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                customer_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                address TEXT NOT NULL,
                delivery_type TEXT NOT NULL,
                payment_type TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
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


def save_order(data: dict, message: Message) -> int:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO orders(
                user_id, username, full_name, book_title, price, quantity,
                customer_name, phone, address, delivery_type, payment_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message.from_user.id,
                message.from_user.username,
                message.from_user.full_name,
                data["book_title"],
                data["price"],
                data["quantity"],
                data["customer_name"],
                data["phone"],
                data["address"],
                data["delivery_type"],
                data["payment_type"],
            ),
        )
        conn.commit()
        return int(cur.lastrowid)


def load_books() -> list[dict]:
    if not BOOKS_PATH.exists():
        return []
    with open(BOOKS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def find_book_by_title(title: str) -> Optional[dict]:
    title = title.strip().lower()
    for book in load_books():
        if book["title"].strip().lower() == title:
            return book
    return None


def books_menu() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for book in load_books():
        kb.button(text=f"📚 {book['title']} — {book['price']:,} so'm".replace(',', ' '), callback_data=f"book:{book['id']}")
    kb.adjust(1)
    return kb.as_markup()


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 Kitoblar"), KeyboardButton(text="🛒 Buyurtma berish")],
            [KeyboardButton(text="💰 Narxlar"), KeyboardButton(text="🚚 Yetkazib berish")],
            [KeyboardButton(text="📩 Admin bilan bog'lanish")],
        ],
        resize_keyboard=True,
    )


async def notify_admin(bot: Bot, text: str) -> None:
    admin_id = get_setting("admin_chat_id")
    if admin_id:
        try:
            await bot.send_message(int(admin_id), text)
        except Exception as e:
            logger.warning("Admin notification failed: %s", e)
    elif ADMIN_USER_ID:
        try:
            await bot.send_message(ADMIN_USER_ID, text)
        except Exception as e:
            logger.warning("Fallback admin notification failed: %s", e)


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    if message.from_user.username and message.from_user.username.lower() == ADMIN_USERNAME.lower():
        set_setting("admin_chat_id", str(message.from_user.id))
    elif ADMIN_USER_ID and message.from_user.id == ADMIN_USER_ID:
        set_setting("admin_chat_id", str(message.from_user.id))

    text = (
        "Assalomu alaykum! 📚\n\n"
        "KitobStoreUz botiga xush kelibsiz.\n"
        "Bu yerda kitoblarni ko'rish, narxini bilish va buyurtma berish mumkin.\n\n"
        f"Admin: @{ADMIN_USERNAME}"
    )
    await message.answer(text, reply_markup=main_menu())


@router.message(Command("admin"))
async def admin_handler(message: Message) -> None:
    if message.from_user.username and message.from_user.username.lower() == ADMIN_USERNAME.lower() or (
        ADMIN_USER_ID and message.from_user.id == ADMIN_USER_ID
    ):
        set_setting("admin_chat_id", str(message.from_user.id))
        await message.answer("✅ Siz admin sifatida ulandingiz. Endi bot sizga buyurtmalar va guruhdagi savollarni yuboradi.")
    else:
        await message.answer("Bu buyruq faqat admin uchun.")


@router.message(F.text == "📚 Kitoblar")
async def books_handler(message: Message) -> None:
    if not load_books():
        await message.answer("Hozircha kitoblar ro'yxati bo'sh.")
        return
    await message.answer("Quyidagi kitoblardan tanlang:", reply_markup=books_menu())


@router.message(F.text == "💰 Narxlar")
async def prices_handler(message: Message) -> None:
    books = load_books()
    if not books:
        await message.answer("Hozircha narxlar kiritilmagan.")
        return
    lines = ["📚 Kitoblar narxlari:\n"]
    for book in books:
        lines.append(f"• {book['title']} — {book['price']:,} so'm".replace(',', ' '))
    lines.append(f"\n📩 Admin: @{ADMIN_USERNAME}")
    await message.answer("\n".join(lines))


@router.message(F.text == "🚚 Yetkazib berish")
async def delivery_info_handler(message: Message) -> None:
    text = (
        "🚚 Yetkazib berish haqida:\n\n"
        "• Toshkent bo'ylab: 1 kun ichida\n"
        "• Viloyatlarga: 1-3 kun\n"
        "• Express va oddiy yetkazib berish mavjud\n\n"
        f"Savol uchun: @{ADMIN_USERNAME}"
    )
    await message.answer(text)


@router.message(F.text == "📩 Admin bilan bog'lanish")
async def contact_admin_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(ContactStates.waiting_message)
    await message.answer(
        f"Savolingizni yozing. Men uni admin @{ADMIN_USERNAME} ga yuboraman.",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(ContactStates.waiting_message)
async def receive_contact_message(message: Message, state: FSMContext, bot: Bot) -> None:
    text = (
        "📩 Bot orqali yangi savol\n\n"
        f"👤 Ism: {message.from_user.full_name}\n"
        f"🆔 ID: {message.from_user.id}\n"
        f"🔗 Username: @{message.from_user.username if message.from_user.username else 'yo\'q'}\n"
        f"💬 Xabar: {message.text}"
    )
    await notify_admin(bot, text)
    await message.answer(
        f"✅ Xabaringiz admin @{ADMIN_USERNAME} ga yuborildi.",
        reply_markup=main_menu(),
    )
    await state.clear()


@router.message(F.text == "🛒 Buyurtma berish")
async def order_start_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(OrderStates.waiting_book)
    await message.answer(
        "Buyurtma uchun kitob nomini yuboring yoki quyidagi ro'yxatdan tanlang:",
        reply_markup=ReplyKeyboardRemove(),
    )
    if load_books():
        await message.answer("📚 Mavjud kitoblar:", reply_markup=books_menu())


@router.callback_query(F.data.startswith("book:"))
async def callback_book_picker(callback, state: FSMContext):
    book_id = callback.data.split(":", 1)[1]
    book = next((b for b in load_books() if str(b["id"]) == book_id), None)
    if not book:
        await callback.answer("Kitob topilmadi", show_alert=True)
        return
    await state.update_data(book_title=book["title"], price=book["price"])
    await state.set_state(OrderStates.waiting_quantity)
    await callback.message.answer(
        f"Tanlandi: {book['title']}\nNarxi: {book['price']:,} so'm\n\nNechta olasiz?".replace(',', ' ')
    )
    await callback.answer()


@router.message(OrderStates.waiting_book)
async def order_book_handler(message: Message, state: FSMContext) -> None:
    book = find_book_by_title(message.text)
    if not book:
        await message.answer("Bu nomdagi kitob topilmadi. Iltimos, aniq nom kiriting yoki ro'yxatdan tanlang.")
        return
    await state.update_data(book_title=book["title"], price=book["price"])
    await state.set_state(OrderStates.waiting_quantity)
    await message.answer(
        f"Tanlandi: {book['title']}\nNarxi: {book['price']:,} so'm\n\nNechta olasiz?".replace(',', ' ')
    )


@router.message(OrderStates.waiting_quantity)
async def order_quantity_handler(message: Message, state: FSMContext) -> None:
    if not message.text.isdigit() or int(message.text) <= 0:
        await message.answer("Iltimos, sonni raqam bilan kiriting. Masalan: 1")
        return
    await state.update_data(quantity=int(message.text))
    await state.set_state(OrderStates.waiting_name)
    await message.answer("Ism va familiyangizni kiriting:")


@router.message(OrderStates.waiting_name)
async def order_name_handler(message: Message, state: FSMContext) -> None:
    await state.update_data(customer_name=message.text.strip())
    await state.set_state(OrderStates.waiting_phone)
    await message.answer("Telefon raqamingizni kiriting: masalan +998901234567")


@router.message(OrderStates.waiting_phone)
async def order_phone_handler(message: Message, state: FSMContext) -> None:
    await state.update_data(phone=message.text.strip())
    await state.set_state(OrderStates.waiting_address)
    await message.answer("Yetkazib berish manzilini kiriting:")


@router.message(OrderStates.waiting_address)
async def order_address_handler(message: Message, state: FSMContext) -> None:
    await state.update_data(address=message.text.strip())
    await state.set_state(OrderStates.waiting_delivery)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Oddiy"), KeyboardButton(text="Express")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await message.answer("Yetkazib berish turini tanlang:", reply_markup=keyboard)


@router.message(OrderStates.waiting_delivery)
async def order_delivery_handler(message: Message, state: FSMContext) -> None:
    delivery_type = message.text.strip()
    if delivery_type not in {"Oddiy", "Express"}:
        await message.answer("Iltimos, Oddiy yoki Express ni tanlang.")
        return
    await state.update_data(delivery_type=delivery_type)
    await state.set_state(OrderStates.waiting_payment)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Naqd"), KeyboardButton(text="Karta")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await message.answer("To'lov turini tanlang:", reply_markup=keyboard)


@router.message(OrderStates.waiting_payment)
async def order_payment_handler(message: Message, state: FSMContext, bot: Bot) -> None:
    payment_type = message.text.strip()
    if payment_type not in {"Naqd", "Karta"}:
        await message.answer("Iltimos, Naqd yoki Karta ni tanlang.")
        return
    await state.update_data(payment_type=payment_type)
    data = await state.get_data()
    order_id = save_order(data, message)
    total = data["price"] * data["quantity"]

    customer_text = (
        "✅ Buyurtmangiz qabul qilindi!\n\n"
        f"📚 Kitob: {data['book_title']}\n"
        f"💰 Narx: {data['price']:,} so'm\n"
        f"🔢 Soni: {data['quantity']}\n"
        f"💵 Jami: {total:,} so'm\n"
        f"🚚 Yetkazib berish: {data['delivery_type']}\n"
        f"💳 To'lov: {data['payment_type']}\n\n"
        f"📩 Admin: @{ADMIN_USERNAME}"
    ).replace(',', ' ')
    await message.answer(customer_text, reply_markup=main_menu())

    admin_text = (
        f"🛒 Yangi buyurtma #{order_id}\n\n"
        f"📚 Kitob: {data['book_title']}\n"
        f"💰 Narx: {data['price']:,} so'm\n"
        f"🔢 Soni: {data['quantity']}\n"
        f"💵 Jami: {total:,} so'm\n\n"
        f"👤 Mijoz: {data['customer_name']}\n"
        f"📞 Telefon: {data['phone']}\n"
        f"📍 Manzil: {data['address']}\n"
        f"🚚 Dastavka: {data['delivery_type']}\n"
        f"💳 To'lov: {data['payment_type']}\n\n"
        f"🔗 Username: @{message.from_user.username if message.from_user.username else 'yo\'q'}\n"
        f"🆔 User ID: {message.from_user.id}"
    ).replace(',', ' ')
    await notify_admin(bot, admin_text)
    await state.clear()


KEYWORDS = {"narx", "bormi", "buyurtma", "yetkazib", "admin", "kitob kerak", "olmoqchi", "sotib"}


@router.message(F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}))
async def group_lead_handler(message: Message, bot: Bot) -> None:
    if not message.text:
        return
    text_lower = message.text.lower()
    if any(keyword in text_lower for keyword in KEYWORDS):
        forwarded = (
            "🚨 Muhokama guruhida sotuvga yaqin xabar\n\n"
            f"👥 Guruh: {message.chat.title}\n"
            f"👤 Ism: {message.from_user.full_name}\n"
            f"🔗 Username: @{message.from_user.username if message.from_user.username else 'yo\'q'}\n"
            f"💬 Xabar: {message.text}"
        )
        await notify_admin(bot, forwarded)


@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("❌ Jarayon bekor qilindi.", reply_markup=main_menu())


async def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN muhit o'zgaruvchisi kiritilmagan")

    init_db()
    bot = Bot(BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
