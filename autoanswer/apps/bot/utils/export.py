import asyncio
from unittest import mock

from autoanswer.config.config import config
from autoanswer.db.models import User

fields_nums = {
    "user_id": "1",
    "username": "2",
    "first_name": "3",
    "last_name": "4",
}


async def part_sending(message, answer, reply_markup=None):
    if len(answer) > 4096:
        for x in range(0, len(answer), 4096):
            y = x + 4096
            if y >= len(answer):
                await message.answer(answer[x: y], reply_markup=reply_markup)
            else:
                await message.answer(answer[x:y])
            await asyncio.sleep(0.5)
    else:
        await message.answer(answer, reply_markup=reply_markup)


def parse_user_fields(fields_text: str) -> tuple:
    if "0" in fields_text:
        return ()
    else:
        return tuple(filter(lambda x: fields_nums[x] in fields_text, fields_nums))


async def get_mock_users() -> list:
    user = await User.exclude(user_id__in=config.bot.admins).first()
    users = []
    for i in range(250):
        mock_user = mock.Mock()
        mock_user.user_id = user.user_id
        mock_user.first_name = user.first_name
        users.append(mock_user)
    return users
