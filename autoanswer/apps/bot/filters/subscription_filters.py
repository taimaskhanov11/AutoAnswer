from aiogram import types
from aiogram.dispatcher.filters import BaseFilter

from autoanswer.db.models import User


class SubscriptionFilter(BaseFilter):
    async def __call__(self, update: types.CallbackQuery | types.Message, user: User) -> bool:

        if user.subscription.duration > 0:
            return True
        else:
            if isinstance(update, types.CallbackQuery):
                update = update.message
            await update.answer("Для того, чтобы пользоваться ботом, нужно купить подписку")
