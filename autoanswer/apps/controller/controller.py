import asyncio
import pprint
import random
from asyncio import Queue
from pathlib import Path
from typing import Optional

from aiogram.dispatcher.fsm.storage.base import StorageKey
from loguru import logger
from pydantic import BaseModel
from telethon import TelegramClient, events
from telethon.tl import types

from autoanswer.apps.bot import temp
from autoanswer.apps.bot.markups.common import common_markups
from autoanswer.apps.bot.temp import controller_codes_queue, controllers
from autoanswer.apps.bot.utils.message import styled_message
from autoanswer.config.config import config
from autoanswer.db.models import Account, User
from autoanswer.db.models.trigger import TriggerCollection, File
from autoanswer.loader import bot, _, storage

SESSION_PATH = Path(Path(__file__).parent, "sessions")


class Controller(BaseModel):
    # todo 5/20/2022 6:24 PM taima: сделать owner_id и тип модели User
    owner: User
    phone: str
    api_id: int
    api_hash: str
    path: Optional[Path]
    client: Optional[TelegramClient]
    trigger_collection: Optional['TriggerCollection']

    """Пользователи которые получили ответ от бота"""
    answered: Optional[list[int]] = []

    class Config:
        arbitrary_types_allowed = True

    def __str__(self):
        return f"{self.phone}[app{self.api_id}]"

    @property
    def owner_id(self):
        return self.owner.user_id

    def get_random_sleep_time(self):
        """Возвращает случайное время ожидания"""
        _from = self.trigger_collection.delay_before_answer - 1
        _to = self.trigger_collection.delay_before_answer + 1
        return random.randint(_from, _to)

    def init(self):
        logger.debug(f"Инициализация клиента {self}")
        self.path = Path(SESSION_PATH, f"{self.api_id}_{self.owner_id}.session")
        self.client = TelegramClient(str(self.path), self.api_id, self.api_hash)

    async def custom_start(self):
        """Ручная настройка"""
        self.init()
        await self.client.start(
            lambda: self.phone
        )

    async def get_phone_try(self):
        """Попытка получить номер телефона"""
        raise Exception("Не удалось получить номер телефона")

    async def start(self):
        """Создать новый client и запустить"""
        # todo 7/14/2022 6:06 PM taima:
        self.init()
        logger.info(f"Контроллер создан")
        try:
            # await self.client.start(lambda: self.phone)
            await self.client.start(lambda: self.get_phone_try())
            # await self.client.connect()
            await self.client.get_me()
            controllers[self.trigger_collection.pk] = self
            await self.listening()

        except Exception as e:
            account = await Account.get(pk=self.trigger_collection.account_id)
            await account.delete()
            await self.stop(unlink=True)
            await bot.send_message(self.owner_id,
                                   f"Произошла ошибка при подключении,вероятно аккаунт забанен.\n"
                                   f"Пожалуйста переподключите аккаунт {self.phone}[{self.api_id}]")
            # await bot.send_message(269019356, "hi")
            logger.warning("Ошибка при подключении клиента [{}]{} {}".format(self.owner_id, self.api_id, e))

    async def stop(self, unlink=False):
        """Приостановить client и удалить"""
        await self.client.disconnect()
        if temp.controllers.get(self.trigger_collection.pk):
            del temp.controllers[self.trigger_collection.pk]
        if unlink:
            if self.path.exists():
                self.path.unlink(missing_ok=True)
        logger.info(f"Контроллер {self} приостановлен и удален")

    @staticmethod
    def _from_self(event: events.NewMessage.Event):
        return event.chat_id == config.bot.id

    async def answer(self, chat, _answer: str | File):
        if isinstance(_answer, File):
            await self.client.send_file(
                chat,
                _answer.path,
                caption=_answer.caption,
            )
        else:
            # todo 7/13/2022 12:14 PM taima: md code
            await self.client.send_message(chat, styled_message(_answer))
            # await self.client.send_message(chat, md.)

    @logger.catch
    async def listening(self):
        """Настройка ответов на сообщения"""

        @self.client.on(events.NewMessage(incoming=True))
        async def my_event_handler(event: events.NewMessage.Event):
            if self._from_self(event):
                return

            if self.trigger_collection.reply_only_first_message:
                if event.chat_id in self.answered:
                    return

            if self.trigger_collection.reply_to_all_messages or self.trigger_collection.reply_to_phrases:
                logger.debug("Поиск ответа -> {text}", text=event.message.text)
                answer = self.trigger_collection.get_answer(event)
                if answer:
                    logger.success("Answer find {answer}", answer=answer)
                    await asyncio.sleep(self.get_random_sleep_time())
                    await self.answer(await event.get_chat(), answer)
                    if self.trigger_collection.reply_only_first_message:
                        self.answered.append(event.chat_id)

        await self.client.run_until_disconnected()


class ConnectAccountController(Controller):
    async def _get_code(self):
        logger.info(f"Ожидание кода {self}")
        queue: Queue = controller_codes_queue.get(self.owner_id)
        code = await queue.get()
        queue.task_done()
        del controller_codes_queue[self.owner_id]
        return code

    async def clear_temp(self):
        await self.client.disconnect()

        if self.trigger_collection:
            if controllers.get(self.trigger_collection.pk):
                del controllers[self.trigger_collection.pk]
        self.path.unlink(missing_ok=True)
        if controllers.get(self.owner_id):
            del controllers[self.owner_id]
        logger.info(f"Временные файлы очищены {self}")

    async def connect_finished_message(self):
        await self.client.send_message("me", "✅ Бот успешно подключен")
        await bot.send_message(
            self.owner_id, "✅ Бот успешно подключен", reply_markup=common_markups.menu_button()
        )
        logger.success(f"Аккаунт пользователя {self} успешно подключен")

    async def _2auth(self):
        raise ValueError("Двухэтапная аутентификация")

    async def try_connect(self):
        await self.client.start(
            lambda: self.phone, password=lambda: self._2auth(), code_callback=lambda: self._get_code()
        )

    async def clear_state(self):
        key = StorageKey((await bot.get_me()).id, self.owner_id, self.owner_id)
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
                self.owner_id, _("🚫 Ошибка, отмена привязки ... Попробуйте отключить Двухэтапную аутентификацию")
            )
            try:
                await self.clear_temp()
            except Exception as e:
                logger.warning(e)
            return False
        await self.clear_state()

        account_data: types.User = await self.client.get_me()
        account = await Account.connect(self, account_data.to_dict())
        self.trigger_collection = account.trigger_collection
        await self.connect_finished_message()
        return True

    async def start(self):
        self.init()
        logger.info(f"Контроллер создан")
        try:
            if await self.connect_account():
                controllers[self.trigger_collection.pk] = self
                await self.listening()

        except Exception as e:
            account = await Account.get_or_none(pk=self.trigger_collection.account_id)
            if account:
                await account.delete()
            await self.stop(unlink=True)
            await bot.send_message(self.owner_id,
                                   f"Произошла ошибка при подключении,вероятно аккаунт забанен.\n"
                                   f"Пожалуйста переподключите аккаунт {self.phone}[{self.api_id}]")
            logger.warning("Ошибка при подключении клиента [{}]{} {}".format(self.owner_id, self.api_id, e))


async def start_controller(account: Account):
    account_data = dict(account)
    controller = Controller(
        owner=account.owner,
        trigger_collection=account.trigger_collection,
        **account_data
    )
    asyncio.create_task(controller.start())

    logger.info(f"Контроллер {controller} запущен")


async def init_controllers():
    logger.debug("Инициализация контролеров")
    for acc in await Account.all().prefetch_related(
            "owner__subscription", "trigger_collection__triggers",
            "trigger_collection__account"):
        if acc.owner.subscription.is_active:
            await start_controller(acc)

    logger.info(f"Контроллеры проинициализированы\n{pprint.pformat(controllers)}")


async def main():
    c = Controller(user_id=269019356,
                   phone="79647116291",
                   api_id=16629671,
                   api_hash="8bb51f9d62e259d5e893ccb02d133b2a")
    await c.custom_start()


if __name__ == '__main__':
    asyncio.run(main())
