from datetime import datetime

import emoji
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from helpers.types import MessageWithUser
from database import User, DataCoin
from helpers.handler_decorators import check_and_set_user
from settngs import dp, bot


def get_user_profile_keyboard():
    keyboard = InlineKeyboardMarkup()

    # Первая кнопка для изменения цветовой схемы
    button_color_scheme = InlineKeyboardButton(
        "Изменить цветовую схему для карты",
        callback_data="choose_color_map_scheme"
    )

    # Вторая кнопка, при нажатии на которую будет отображаться уведомление
    button_notify = InlineKeyboardButton(
        "Показ изображений вкл|выкл",
        callback_data="show_pictures"
    )

    # Добавляем кнопки в клавиатуру
    keyboard.add(button_color_scheme)
    keyboard.add(button_notify)

    return keyboard


@dp.message_handler(commands=["profile"])
@check_and_set_user
async def profile(message: MessageWithUser):
    print(datetime.now(), "| ", message.from_user.id, 'commands=["profile"]')

    user = User.get(message.from_user.id)
    last_refresh = user.last_refresh

    keyboard = get_user_profile_keyboard()
    await message.answer(
        f'<a href="https://ru.ucoin.net/uid{message.user.user_coin_id}?v=home">👤 Профиль</a>\n'
        f"\n🕓 Последнее обновление: {last_refresh}",

        parse_mode="HTML",
        reply_markup=keyboard,
    )

class Form(StatesGroup):
    user_coin_id = State()
    user_name = State()


@dp.message_handler(commands=["reg"])
async def reg_welcome(message: MessageWithUser):
    if User.get(tg_id=message.from_user.id) is not None:
        await message.answer("Ты уже регистрировался")
        return

    await message.answer(
        "Введи свой `user_coin_id` (например, 123456)\n________________________\nИли нажми /EXIT"
    )
    await message.answer(emoji.emojize(":eyes:"))
    await Form.user_coin_id.set()


@dp.message_handler(state=Form.user_coin_id)
async def process_user_coin_id(message: MessageWithUser, state: FSMContext):
    if message.text.lower() == "/exit":
        await state.finish()
        await message.answer("⬇️ Доступные команды")
        return

    user_coin_id = message.text.strip()

    if not user_coin_id.isdigit():
        await message.answer("ID должен быть числом. Попробуй снова или нажми /EXIT")
        return

    # Сохраняем временно user_coin_id
    await state.update_data(user_coin_id=user_coin_id)

    await message.answer(
        "Теперь введи имя пользователя, которое будет отображаться.\n"
        "Если хочешь использовать имя из Telegram — отправь /skip"
    )
    await Form.user_name.set()


@dp.message_handler(state=Form.user_name)
async def process_user_name(message: MessageWithUser, state: FSMContext):
    if message.text.lower() == "/exit":
        await state.finish()
        await message.answer("⬇️ Доступные команды")
        return

    data = await state.get_data()
    user_coin_id = data.get("user_coin_id")

    if message.text.lower() == "/skip" or not message.text.strip():
        user_name = message.from_user.full_name.replace(" ", "_")
    else:
        user_name = message.text.strip().replace(" ", "_")

    # Попытка сохранить пользователя
    try:
        # Предполагаемая структура User (проверь!)
        user = User(
            tg_id=message.from_user.id,
            user_coin_id=user_coin_id,
            user_name=user_name,
        )
        user.save()  # <-- здесь скорее всего и происходит ошибка

    except Exception as e:
        await message.answer(f"❌ Ошибка при сохранении: {e}")
        await state.finish()
        return


    await message.answer("Регистрация завершена ✅\nДанные сохранены в базе")
    await state.finish()


class DeleteForm(StatesGroup):
    confirm_delete = State()  # 1 состояние для удаления данных из бота
    confirm_delete2 = State()  # 2 состояние для удаления данных из бота


@dp.message_handler(commands=["delete"])
@check_and_set_user
async def delete1(message: MessageWithUser):
    print(datetime.now(), "| ",  message.from_user.id, 'commands=["delete"]')

    await DeleteForm.confirm_delete.set()
    await message.answer(
        "При удалении данных стираются также значения стоимости монет, график обнуляется"
    )
    await message.answer("Точно удалить? \nпиши   да   или   нет")


@dp.message_handler(state=DeleteForm.confirm_delete)
@check_and_set_user
async def delete2(message: MessageWithUser, state: FSMContext):
    if message.text.lower() == "да":
        await DeleteForm.confirm_delete2.set()
        await message.answer("Последний раз спрашиваю \nпиши   да   или   нет")

    else:
        await message.answer("Ну и всё, больше так не делай")

        await state.finish()  # Завершаем текущий state


@dp.message_handler(state=DeleteForm.confirm_delete2)
@check_and_set_user
async def delete3(message: MessageWithUser, state: FSMContext):
    if message.text.lower() == "да":
        User.delete(tg_id=message.from_user.id)
        DataCoin.delete_user_data(tg_id=message.from_user.id)
        await message.answer("Данные удалены из базы данных бота \n↓↓↓ Доступные команды")

    else:
        await message.answer("Ну и нахуй ты мне мозгу ебешь, кожаный мешок")

    await state.finish()  # Завершаем текущий state
