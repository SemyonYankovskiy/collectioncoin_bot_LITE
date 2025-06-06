import asyncio
from datetime import datetime
from helpers.types import MessageWithUser
from handlers import profile
from handlers.graph import grafik
from handlers.services import send_message_to_user
from settngs import dp
from database import User


async def send_to_all_users(message_text="Бот был перезагружен, обновите данные \n /refresh"):
    # Получаем список всех пользователей из базы данных
    users_list = User.get_all()

    # Отправляем сообщение каждому пользователю
    for user in users_list:
        await send_message_to_user(user.tg_id, message_text)
        await asyncio.sleep(0.1)


@dp.message_handler(commands=["m"])
async def from_user_to_user(message: MessageWithUser):
    if message.from_user.id != 726837488:
        await message.answer("Сложно непонятно говоришь")
        await message.answer("⬇️ Доступные команды")
    else:
        # Получаем аргументы из сообщения пользователя
        args = message.get_args().split(maxsplit=1)
        if len(args) != 2:
            await message.answer("Используйте команду следующим образом: /m <user_id> <текст>")
            return

        # Извлекаем user_id и текст из аргументов
        user_id, text = args
        try:
            user_id = int(user_id)
        except ValueError:
            await message.answer("Неверный формат user_id. Пожалуйста, укажите целое число.")
            return

        # Вызываем вспомогательную функцию для безопасной отправки сообщения
        success = await send_message_to_user(user_id, text)

        if success:
            await message.answer("Сообщение успешно отправлено другому пользователю.")
        else:
            await message.answer("Не удалось отправить сообщение. Пожалуйста, попробуйте позже.")