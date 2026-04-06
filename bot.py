import asyncio
import logging
from urllib.parse import unquote

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

BOT_TOKEN = "8655416610:AAEYVGS85Pninlk6P54Hg5fbrewbC_8uONQ"
ADMIN_ID = 7020576612

logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()


class OrderState(StatesGroup):
    phone = State()
    full_name = State()
    address = State()


contact_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)


def parse_book_name_from_start(message_text: str) -> str:
    if not message_text:
        return "Noma'lum kitob"

    parts = message_text.split(maxsplit=1)
    if len(parts) < 2:
        return "Noma'lum kitob"

    start_param = parts[1].strip()

    if start_param.startswith("book_"):
        raw_name = start_param.replace("book_", "", 1)
        return unquote(raw_name)

    return "Noma'lum kitob"


@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    book_name = parse_book_name_from_start(message.text or "")

    telegram_id = message.from_user.id
    username = message.from_user.username or "yo'q"
    first_name = message.from_user.first_name or "yo'q"

    await state.update_data(
        book_name=book_name,
        telegram_id=telegram_id,
        username=username,
        telegram_name=first_name,
    )

    if book_name != "Noma'lum kitob":
        text = (
            f"📚 <b>Siz tanlagan kitob:</b> {book_name}\n\n"
            "Buyurtmani davom ettirish uchun pastdagi tugma orqali "
            "<b>telefon raqamingizni yuboring</b>."
        )
    else:
        text = (
            "📚 <b>KitobStoreUz botiga xush kelibsiz!</b>\n\n"
            "Agar siz sayt orqali kirgan bo'lsangiz, kitob nomi avtomatik keladi.\n"
            "Hozir buyurtmani davom ettirish uchun pastdagi tugma orqali "
            "<b>telefon raqamingizni yuboring</b>."
        )

    await message.answer(text, reply_markup=contact_keyboard)
    await state.set_state(OrderState.phone)


@dp.message(OrderState.phone, F.contact)
async def get_phone(message: Message, state: FSMContext):
    phone_number = message.contact.phone_number
    await state.update_data(phone=phone_number)

    await message.answer(
        "✍️ Endi <b>ism familiyangizni</b> to'liq kiriting:",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(OrderState.full_name)


@dp.message(OrderState.phone)
async def phone_not_contact(message: Message):
    await message.answer(
        "Iltimos, pastdagi <b>📱 Telefon raqamni yuborish</b> tugmasini bosing."
    )


@dp.message(OrderState.full_name)
async def get_full_name(message: Message, state: FSMContext):
    full_name = (message.text or "").strip()

    if len(full_name) < 3:
        await message.answer("Iltimos, ism familiyangizni to'liqroq kiriting.")
        return

    await state.update_data(full_name=full_name)
    await message.answer("📍 Endi <b>manzilingizni</b> kiriting:")
    await state.set_state(OrderState.address)


@dp.message(OrderState.address)
async def get_address(message: Message, state: FSMContext):
    address = (message.text or "").strip()

    if len(address) < 5:
        await message.answer("Iltimos, manzilni to'liqroq kiriting.")
        return

    await state.update_data(address=address)
    data = await state.get_data()

    username = data.get("username", "yo'q")
    username_text = f"@{username}" if username != "yo'q" else "yo'q"

    admin_text = (
        "🛒 <b>Yangi buyurtma</b>\n\n"
        f"📚 <b>Kitob:</b> {data.get('book_name', 'Noma\'lum kitob')}\n"
        f"👤 <b>To'liq ism:</b> {data.get('full_name', '-')}\n"
        f"📞 <b>Telefon:</b> {data.get('phone', '-')}\n"
        f"📍 <b>Manzil:</b> {data.get('address', '-')}\n\n"
        f"🆔 <b>Telegram ID:</b> {data.get('telegram_id', '-')}\n"
        f"👤 <b>Username:</b> {username_text}\n"
        f"🙍 <b>Telegram ismi:</b> {data.get('telegram_name', '-')}"
    )

    await bot.send_message(ADMIN_ID, admin_text)

    await message.answer(
        "✅ <b>Buyurtmangiz qabul qilindi.</b>\n"
        "Tez orada siz bilan bog'lanamiz."
    )

    await state.clear()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
