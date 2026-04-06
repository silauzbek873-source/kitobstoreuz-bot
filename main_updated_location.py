import asyncio
import logging

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


class UserDataState(StatesGroup):
    phone = State()
    full_name = State()
    location = State()


contact_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

location_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📍 Joylashuvni yuborish", request_location=True)]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)


@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    username = message.from_user.username or "yo'q"
    first_name = message.from_user.first_name or "yo'q"

    await state.update_data(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name
    )

    username_text = f"@{username}" if username != "yo'q" else "yo'q"

    await message.answer(
        f"Salom, <b>{first_name}</b>!\n\n"
        f"🆔 Telegram ID avtomatik olindi: <code>{telegram_id}</code>\n"
        f"👤 Username: {username_text}\n\n"
        "Buyurtmani davom ettirish uchun pastdagi tugma orqali telefon raqamingizni yuboring:",
        reply_markup=contact_keyboard
    )
    await state.set_state(UserDataState.phone)


@dp.message(UserDataState.phone, F.contact)
async def get_phone(message: Message, state: FSMContext):
    phone_number = message.contact.phone_number
    await state.update_data(phone=phone_number)

    await message.answer(
        "✍️ Endi ism familiyangizni kiriting:",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(UserDataState.full_name)


@dp.message(UserDataState.phone)
async def phone_error(message: Message):
    await message.answer("Iltimos, pastdagi tugmani bosib telefon raqamingizni yuboring.")


@dp.message(UserDataState.full_name)
async def get_full_name(message: Message, state: FSMContext):
    full_name = (message.text or "").strip()

    if len(full_name) < 3:
        await message.answer("Iltimos, ism familiyangizni to'liqroq kiriting.")
        return

    await state.update_data(full_name=full_name)

    await message.answer(
        "📍 Endi pastdagi tugma orqali joylashuvingizni yuboring:",
        reply_markup=location_keyboard
    )
    await state.set_state(UserDataState.location)


@dp.message(UserDataState.location, F.location)
async def get_location(message: Message, state: FSMContext):
    latitude = message.location.latitude
    longitude = message.location.longitude

    await state.update_data(latitude=latitude, longitude=longitude)
    data = await state.get_data()

    username = data.get("username", "yo'q")
    username_text = f"@{username}" if username != "yo'q" else "yo'q"

    admin_text = (
        "🛒 <b>Yangi zakaz</b>\n\n"
        f"🆔 <b>Telegram ID:</b> <code>{data.get('telegram_id')}</code>\n"
        f"👤 <b>Username:</b> {username_text}\n"
        f"🙍 <b>Telegram ismi:</b> {data.get('first_name')}\n"
        f"✍️ <b>To'liq ism:</b> {data.get('full_name')}\n"
        f"📞 <b>Telefon:</b> {data.get('phone')}\n"
        f"📍 <b>Joylashuv:</b> {latitude}, {longitude}\n"
        f"🗺 <b>Xarita linki:</b> https://maps.google.com/?q={latitude},{longitude}"
    )

    await bot.send_message(ADMIN_ID, admin_text)

    await message.answer(
        "✅ Zakazingiz qabul qilindi. Tez orada siz bilan bog'lanamiz.",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.clear()


@dp.message(UserDataState.location)
async def location_error(message: Message):
    await message.answer("Iltimos, pastdagi tugmani bosib joylashuvingizni yuboring.")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
