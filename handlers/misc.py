from datetime import datetime

import emoji
from aiogram.types import InputFile

from helpers.types import MessageWithUser
from settngs import dp, bot


@dp.message_handler(commands=["start"])
async def hello_welcome(message: MessageWithUser):
    print(datetime.now(), "| ",  message.from_user.id, 'commands=["start"]')
    # keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    # buttons = ["Страны", "Карта"]
    # keyboard.add(*buttons)
    # button_1 = types.KeyboardButton(text="График")
    # keyboard.add(button_1)
    await message.answer(emoji.emojize(":robot:"))
    await message.answer(f"Здарова, {message.from_user.full_name}")
    await message.answer("⬇️ Доступные команды")


@dp.message_handler(commands=["help"])
async def ua_welcome(message: MessageWithUser):
    print(datetime.now(), "| ",  message.from_user.id, 'commands=["help"]')

    await message.answer(
        "💬 Пластмассовый мир победил, пока я не придумаю как обойти капчу бот работает в ручном режиме.\n"
        "💬 Для новых пользователей нужно зарегистрироваться в "
        "боте /reg с указанием вашего ID на сайте ru.ucoin.net. Затем нужно вызвать команду /refresh и закинуть в него файл с сайта\n💬 После регистрации бот хранить данные о вашей коллекции,списке обмена\n"
        "/swap_list, "
        "считать суммарную стоимость монет /summ, показывать количество монет по странам /countries,"
        " рисовать карту мира /map "
        "а также строить график изменения стоимости монет за последний месяц /grafik\n \n"
        "💬 Вы можете удалить свои данные из бота /delete. При удалении данных стираются также значения стоимости "
        "монет,"
        "график обнуляется \n \n"
        "💬 Если у вас есть монеты, стоимость которых не нужно учитывать, выберите (на сайте Ucoin) для монеты желтую "
        "метку (см.рис. ниже)"
    )
    await bot.send_photo(chat_id=message.from_user.id, photo=InputFile("img/help.png"))
    await message.answer("⚙️ Поддержка @M0IIC")
    await message.answer("⬇️ Доступные команды")


@dp.message_handler()
async def unknown(message: MessageWithUser):
    await message.answer("Сложно непонятно говоришь")
    await message.answer("⬇️ Доступные команды")
