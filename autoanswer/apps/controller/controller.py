import asyncio
import hashlib
import pprint
import warnings
from asyncio import Queue
from pathlib import Path
from typing import Optional

from aiogram.dispatcher.fsm.storage.base import StorageKey
from loguru import logger
from pydantic import BaseModel
from telethon import TelegramClient
from telethon.tl import types
from telethon.tl.functions import phone
from telethon.tl.functions.messages import GetDhConfigRequest

from autoanswer.apps.bot import temp
from autoanswer.apps.bot.markups.common import common_markups
from autoanswer.apps.bot.temp import controller_codes_queue, controllers
from autoanswer.db.models import Account
from autoanswer.loader import bot, _, storage

SESSION_PATH = Path(Path(__file__).parent, "sessions")


class Controller(BaseModel):
    # todo 5/20/2022 6:24 PM taima: сделать owner_id и тип модели User
    user_id: int
    username: Optional[str]
    phone: str
    api_id: int
    api_hash: str
    path: Optional[Path]
    client: Optional[TelegramClient]

    class Config:
        arbitrary_types_allowed = True

    def __str__(self):
        return f"{self.phone}[app{self.api_id}]"

    def init(self):
        logger.debug(f"Инициализация клиента {self}")
        self.path = Path(SESSION_PATH, f"{self.api_id}_{self.user_id}.session")
        self.client = TelegramClient(str(self.path), self.api_id, self.api_hash)

    async def custom_start(self):
        """Ручная настройка"""
        self.init()
        await self.client.start(
            lambda: self.phone
        )

    async def start(self):
        """Создать новый client и запустить"""
        self.init()
        logger.debug(f"Контроллер создан")
        await self.client.connect()
        # await self.listening()
        # todo 5/21/2022 2:59 AM taima: включить подкючение

    async def stop(self):
        """Приостановить client и удалить"""
        await self.client.disconnect()
        del temp.controllers[self.api_id]
        logger.info(f"Контроллер {self} приостановлен и удален")


class ConnectAccountController(Controller):
    async def _get_code(self):
        logger.info(f"Ожидание кода {self}")
        queue: Queue = controller_codes_queue.get(self.user_id)
        code = await queue.get()
        queue.task_done()
        del controller_codes_queue[self.user_id]
        return code

    async def clear_temp(self):
        await self.client.disconnect()
        del controllers[self.api_id]
        self.path.unlink(missing_ok=True)
        del controller_codes_queue[self.user_id]
        logger.info(f"Временные файлы очищены {self}")

    # deprecated
    async def get_code(self):
        warnings.warn(
            "use self._get_code()",
            DeprecationWarning,
            stacklevel=2,
        )
        try:
            return await asyncio.wait_for(self._get_code(), timeout=40)
        except Exception as e:
            logger.warning(f"Не удалось получить код для подключения {self} {e}")
            await storage.finish(user=self.user_id)
            await bot.send_message(
                self.user_id,
                "🚫 Ошибка, отмена привязки ...\nПовторите попытку",
                reply_markup=common_markups.menu_button(),
            )
            await self.clear_temp()

    async def connect_finished_message(self):
        await self.client.send_message("me", "✅ Бот успешно подключен")
        await bot.send_message(
            self.user_id, "✅ Бот успешно подключен", reply_markup=common_markups.menu_button()
        )
        logger.success(f"Аккаунт пользователя {self} успешно подключен")

    async def _2auth(self):
        raise ValueError("Двухэтапная аутентификация")

    async def try_connect(self):
        await self.client.start(
            lambda: self.phone, password=lambda: self._2auth(), code_callback=lambda: self._get_code()
        )

    async def clear_state(self):
        key = StorageKey((await bot.get_me()).id, self.user_id, self.user_id)
        await storage.set_state(bot, key)
        await storage.set_data(bot, key, {})

    async def connect_account(self):
        """Подключение аккаунта и создание сессии"""
        logger.debug(f"Подключение аккаунта {self}")
        try:
            await asyncio.wait_for(self.try_connect(), timeout=30)
        except Exception as e:
            logger.warning(f"Не удалось получить код для подключения {self} {e}")
            await bot.send_message(
                self.user_id, _("🚫 Ошибка, отмена привязки ... Попробуйте отключить Двухэтапную аутентификацию")
            )
            await self.clear_temp()
            return

        await self.clear_state()
        account_data: types.User = await self.client.get_me()
        logger.info(account_data)
        await Account.connect(self, account_data.to_dict())
        # await self.client.disconnect()
        await self.connect_finished_message()

    async def start(self):
        self.init()
        logger.debug(f"Контроллер создан")
        await self.connect_account()
        # await self.listening()


async def start_controller(account: Account):
    account_data = dict(account)
    del account_data["user_id"]
    controller = Controller(
        user_id=account.owner.user_id,
        **account_data
    )
    asyncio.create_task(controller.start())
    controllers[controller.user_id][controller.api_id] = controller

    logger.info(f"Контроллер {controller} запущен")


async def restart_controller(user):
    account = await Account.get(user=user).prefetch_related(
        "chats__message_filter__user_filters",
        "chats__message_filter__word_filter",
        "chats__chat_storage",
        "user",
    )
    await start_controller(account)
    # await controller.client.send_message("me", _("✅ Бот успешно подключен"))


async def init_controllers():
    logger.debug("Инициализация контролеров")
    for acc in await Account.all().select_related("owner"):
        await start_controller(acc)

    logger.info(f"Контроллеры проинициализированы\n{pprint.pformat(controllers)}")


async def main():
    c = CustomController(user_id=269019356,
                         phone="79647116291",
                         api_id=16629671,
                         api_hash="8bb51f9d62e259d5e893ccb02d133b2a")
    await c.custom_start()


if __name__ == '__main__':
    asyncio.run(main())
