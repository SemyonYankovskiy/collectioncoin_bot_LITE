import asyncio
from datetime import datetime
from aiogram.utils import exceptions
import emoji
from core.site_calc import more_info, file_opener
from helpers.types import MessageWithUser
from database import DataCoin, User
from handlers.map import save_user_map
from helpers.handler_decorators import check_and_set_user
from settngs import dp, bot

from aiogram.dispatcher.filters.state import State, StatesGroup

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ContentType
from datetime import datetime
import asyncio
import traceback
from concurrent.futures import ThreadPoolExecutor


# =================== Состояния ===================
class RefreshStates(StatesGroup):
    waiting_for_choice = State()
    waiting_for_file = State()


# =================== Потоковый executor ===================
executor = ThreadPoolExecutor(max_workers=2)


# =================== Хендлер /refresh ===================
@dp.message_handler(commands=["refresh"])
@check_and_set_user
async def refresh_start(message: types.Message):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("🌐 Обновить список монет", callback_data="refresh_coins"),
        InlineKeyboardButton("🔄 Обновить список обмена", callback_data="refresh_swap"),
        InlineKeyboardButton("🔙 Назад", callback_data="refresh_back")
    )
    await message.answer("Выберите действие ⤵️", reply_markup=kb)
    await RefreshStates.waiting_for_choice.set()
    print(datetime.now(), "|", f"User {message.from_user.id} started refresh")


# =================== Обработка выбора действия ===================
@dp.callback_query_handler(state=RefreshStates.waiting_for_choice)
@check_and_set_user
async def refresh_choice_callback(call: CallbackQuery, state: FSMContext):
    action_map = {
        "refresh_coins": "🌐 Обновить список монет",
        "refresh_swap": "🔄 Обновить список обмена"
    }

    if call.data == "refresh_back":
        await call.message.edit_text("✖️ Действие отменено.")
        await state.finish()
        return

    choice = action_map.get(call.data)
    if not choice:
        await call.answer("❌ Неверный выбор", show_alert=True)
        return

    await state.update_data(choice=choice)

    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("🔙 Назад", callback_data="refresh_back")
    )
    await call.message.edit_text("💹 Отправьте файл Excel (.xlsx).", reply_markup=kb)
    await RefreshStates.waiting_for_file.set()
    print(datetime.now(), "|", f"User {call.from_user.id} chose: {choice}")


# =================== Выход из шага загрузки файла ===================
@dp.callback_query_handler(lambda c: c.data == "refresh_back", state=RefreshStates.waiting_for_file)
async def cancel_file_upload(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("✖️ Загрузка файла отменена.")
    await state.finish()
    print(datetime.now(), "|", f"User {call.from_user.id} cancelled file upload")


# =================== Загрузка и обработка файла ===================
@dp.message_handler(content_types=ContentType.DOCUMENT, state=RefreshStates.waiting_for_file)
@check_and_set_user
async def refresh_receive_file(message: types.Message, state: FSMContext):
    print(datetime.now(), "|", f"User {message.from_user.id} sent a document")

    data = await state.get_data()
    choice = data.get("choice")
    if not choice:
        await message.answer("Что-то пошло не так, повторите команду /refresh")
        await state.finish()
        return

    document = message.document
    if not document.file_name.endswith(".xlsx"):
        await message.answer("Файл должен быть в формате .xlsx")
        return

    user = User.get(message.from_user.id)
    user_coin_id = user.user_coin_id
    if choice == "🌐 Обновить список монет":
        file_name = f"./users_files/{user_coin_id}_.xlsx"
    else:
        file_name = f"./users_files/{user_coin_id}_SWAP.xlsx"

    try:
        await document.download(destination_file=file_name)
        print(datetime.now(), "|", f"File saved as {file_name}")

        loop = asyncio.get_running_loop()
        total, total_count = await loop.run_in_executor(executor, file_opener, file_name)
        print(datetime.now(), "|", f"file_opener returned total={total}, total_count={total_count}")

        user = User.get(message.from_user.id)
        DataCoin(user.tg_id, total, total_count).save()
        print(datetime.now(), "|", f"DataCoin saved for user {user.tg_id}")

        if choice == "🌐 Обновить список монет":
            await message.answer("⏳ Я не завис, рисую карты")
            await loop.run_in_executor(executor, save_user_map, user)
            print(datetime.now(), "|", f"Карты обновлены для пользователя {user.tg_id}")

        await message.answer("✅ База данных успешно обновлена")

    except Exception as e:
        print(datetime.now(), "|", f"Ошибка при обработке файла: {e}")
        traceback.print_exc()
        await message.answer("Произошла ошибка при обработке файла. Попробуйте позже.")

    await state.finish()


# Вспомогательная функция для безопасной отправки сообщения
async def send_message_to_user(user_id: int, text: str, disable_notification: bool = False, parse_mode="MARKDOWN") -> bool:
    user = User.get(user_id)
    try:
        await bot.send_message(user_id, text, parse_mode, disable_notification=disable_notification, )
    except exceptions.BotBlocked:
        print(datetime.now(), "| ", f"Пользователь [{user.user_name}] заблокировал бота")
    except exceptions.ChatNotFound:
        print(datetime.now(), "| ", f"Неверный ID пользователя [{user.user_name}]")
    except exceptions.RetryAfter as e:
        print(datetime.now(), "| ", f"Превышен лимит отправки сообщений для [{user.user_name}]. Жди {e.timeout} сек.")
        await asyncio.sleep(e.timeout)
        return await send_message_to_user(user_id, text)
    except exceptions.UserDeactivated:
        print(datetime.now(), "| ", f"Пользователь [{user.user_name}] деактивирован")
    except exceptions.TelegramAPIError:
        print(datetime.now(), "| ", f"Не удалось отправить сообщение пользователю [{user.user_name}]")
    else:
        print(datetime.now(), "| ", f"Сообщение успешно отправлено пользователю [{user.user_name}]")
        return True
    return False


@dp.message_handler(commands=["summ"])
@check_and_set_user
async def summ(message: MessageWithUser):

    await message.answer(emoji.emojize(":coin:"))
    await _summ(message)


@check_and_set_user
async def _summ(message: MessageWithUser):
    print(datetime.now(), "| USER:", message.from_user.id, 'commands=["summ"]')

    coin_st = DataCoin.get_for_user(message.from_user.id, limit=1)
    # обращаемся к функции more info, передаем в эту функциию значение переменной (значение из 4 столбца массива)
    try:
        lot, count, sold = more_info(f"./users_files/{message.user.user_coin_id}_.xlsx")

        await message.answer(
            f"🪙 Количество монет {lot} \n"
            f"🌐 Количество стран {count} \n\n"
            f"💶 Общая стоимость {coin_st[0].totla_sum} руб. \n\n"
            f"💵 Потрачено {sold} руб. "
        )
    except Exception:
        await message.answer(f"Ой! Обновите базу данных вручную \n/refresh")
