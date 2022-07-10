from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware, types
from aiogram.types import Message, CallbackQuery
from loguru import logger

from autoanswer.apps.bot import temp
from autoanswer.config.config import config
from autoanswer.db.models import User


async def get_user(update: types.CallbackQuery | types.Message) -> dict[str, User] | bool:
    user = update.from_user
    logger.debug(f"Get user for User {user.id}")
    user, is_new = await User.get_or_create(
        user_id=user.id,
        defaults={
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "language": user.language_code,
        },
    )
    if is_new:
        logger.info(f"Новый пользователь {user=}")
    await user.fetch_related("subscription")
    return {"user": user}


class BotMiddleware(BaseMiddleware):

    async def __call__(
            self,
            handler: Callable[[Message | CallbackQuery, dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: dict[str, Any]
    ) -> Any:
        user_data = await get_user(event)
        data.update(**user_data)
        # logger.info(user_data)
        if temp.BOT_RUNNING or event.from_user.id in config.bot.admins:
            return await handler(event, data)
