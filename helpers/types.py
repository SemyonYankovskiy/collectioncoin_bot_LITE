from aiogram.types import Message, CallbackQuery

from database import User


class MessageWithUser(Message):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user: User = User(tg_id=self.from_user.id)


class CallbackQueryWithUser(CallbackQuery):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user: User = User(tg_id=self.from_user.id)
