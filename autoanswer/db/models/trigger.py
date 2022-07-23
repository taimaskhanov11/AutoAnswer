import typing
from pathlib import Path

from aiogram.utils import markdown as md
from loguru import logger
from pydantic import BaseModel, validator
from telethon import events
from tortoise import fields, models

from autoanswer.apps.bot.temp import controllers
from autoanswer.apps.bot.utils.message import styled_message
from autoanswer.config.config import MEDIA_DIR

if typing.TYPE_CHECKING:
    from autoanswer.db.models.account import Account


def prepare_for_answer(text: str):
    return text.replace("`", "").replace("*", "").replace("_", "")


class File(BaseModel):
    path: str | Path | None
    caption: str | None

    @validator('path')
    def correct_path(cls, v):
        return MEDIA_DIR / v


class Trigger(models.Model):
    id: int
    phrases = fields.JSONField()  # list
    answer = fields.TextField(null=True)
    file_name = fields.CharField(50, null=True)
    trigger_collection: fields.ForeignKeyRelation['TriggerCollection'] = fields.ForeignKeyField(
        "models.TriggerCollection", related_name="triggers")
    trigger_collection_id: int

    @property
    def prettify(self):
        _str = (f"{md.bold('Фразы: ')}️ {md.code(', '.join(self.phrases))}\n"
                # f"{md.bold('Текст ответа: ')}{md.code(self.answer)}")
                f"{md.bold('Текст ответа: ')}{styled_message(self.answer)}")
        if self.file_name:
            _str += f"\n{md.bold('Файл: ')}{md.code(self.file_name)}"
        # todo 7/23/2022 3:32 PM taima: переделать
        return prepare_for_answer(_str)

    @classmethod
    async def get_local_or_full(cls, pk: int) -> 'Trigger':
        trigger = await cls.get(pk=pk)
        if controller := controllers.get(trigger.trigger_collection_id):
            return controller.trigger_collection.get_trigger(pk)
        await trigger.fetch_related("trigger_collection")
        return trigger

    @classmethod
    async def get_full(cls, pk: int | str) -> 'Trigger':
        return await cls.get(id=pk).select_related('trigger_collection')

    @staticmethod
    def fix_phrases(phrases: str | list):
        if isinstance(phrases, str):
            phrases = map(lambda x: x.strip(), phrases.split(","))
        return list(map(lambda x: x.lower(), phrases))

    async def set_phrases(self, phrases: list | str):
        self.phrases = self.fix_phrases(phrases)
        await self.save(update_fields=["phrases"])

    async def set_answer(self, answer: str):
        self.answer = answer
        await self.save(update_fields=["answer"])

    async def set_file_name(self, file_name: str):
        self.answer = file_name
        await self.save(update_fields=["set_file_name"])

    def get_answer(self, text: str) -> str | File | None:
        for phrase in self.phrases:
            if phrase in text:
                if self.file_name:
                    return File(path=self.file_name, caption=self.answer)
                return self.answer


class TriggerCollection(models.Model):
    id: int
    account_id: int
    account: 'Account' = fields.OneToOneField("models.Account", related_name="trigger_collection")
    reply_to_phrases = fields.BooleanField(default=False)
    reply_to_all_messages = fields.BooleanField(default=False)
    reply_to_groups = fields.BooleanField(default=False)
    reply_to_channels = fields.BooleanField(default=False)
    reply_only_first_message = fields.BooleanField(default=False)

    delay_before_answer = fields.IntField(default=0)
    answer_to_all_messages = fields.TextField(null=True)
    file_name = fields.CharField(50, null=True)

    triggers: fields.ReverseRelation[Trigger]

    @classmethod
    async def get_full(cls, pk: int | str):
        return await cls.get(pk=pk).prefetch_related("triggers", "account")

    @classmethod
    async def get_local_or_full(cls, pk: int | str) -> 'TriggerCollection':
        if controller := controllers.get(pk):
            return controller.trigger_collection
        return await cls.get_full(pk)

    @classmethod
    async def refresh_local(cls, pk: int | str, _fields: list = None):
        if controller := controllers.get(pk):
            await controller.trigger_collection.refresh_from_db(fields=_fields)

    @classmethod
    async def refresh_local_to_new(cls, pk: int | str):
        if controller := controllers.get(pk):
            trigger_collection = await cls.get_full(pk)
            controller.trigger_collection = trigger_collection

    def get_trigger(self, pk: int | str):
        for trigger in self.triggers:
            if trigger.pk == pk:
                return trigger

    async def switch_status(self, field: str):
        """Switch answer status"""
        setattr(self, field, not getattr(self, field))
        await self.save(update_fields=[field])

    async def set_answer(self, answer: str):
        self.answer_to_all_messages = answer
        await self.save(update_fields=["answer_to_all_messages"])

    async def set_delay_before_answer(self, delay: int):
        self.delay_before_answer = delay
        await self.save(update_fields=["delay_before_answer"])

    def get_answer(self, event: events.NewMessage.Event):
        # todo 7/12/2022 12:18 PM taima: переделать
        check = True
        channel = False
        group = False

        if event.is_group:
            group = True
            if not self.reply_to_groups:
                check = False
                logger.trace("{pk}|Сообщение из группы. Ответ отключен", pk=self.pk)
            else:
                logger.trace("{pk}|Сообщение из группы. Ответ включен", pk=self.pk)

        elif event.is_channel:
            channel = True
            if not self.reply_to_channels:
                check = False
                logger.trace("{pk}|Сообщение из канала. Ответ отключен", pk=self.pk)
            else:
                logger.trace("{pk}|Сообщение из канала. Ответ включен", pk=self.pk)

        if not any([channel, group]):
            logger.trace("{pk}|Сообщение из приватного чата", pk=self.pk)

        if check:
            text = event.message.text.lower()
            if self.reply_to_phrases:
                if self.triggers:
                    for trigger in self.triggers:
                        if answer := trigger.get_answer(text):
                            logger.success(
                                "Ответ на фразы найден {text} -> {answer_to_all_messages}", text=event.message.text,
                                answer_to_all_messages=self.answer_to_all_messages)
                            return answer

            if self.reply_to_all_messages:
                logger.success("Ответ на все сообщения {text} -> {answer_to_all_messages}", text=event.message.text,
                               answer_to_all_messages=self.answer_to_all_messages)

                if self.file_name:
                    return File(path=self.file_name, caption=self.answer_to_all_messages)
                return self.answer_to_all_messages

            logger.trace("Ответ не найден -> {text}", text=event.message.text)
        else:
            logger.debug("Не соответствует требованиям. Поиск отключен")

    @property
    def triggers_prettify(self):
        triggers_str = ""
        for num, value in enumerate(self.triggers, 1):
            p_num = md.code(f'# {num}')
            triggers_str += f"{p_num}\n{value.prettify}\n\n"
        # todo 7/23/2022 3:31 PM taima: переделать
        return prepare_for_answer(triggers_str)

    @property
    def prettify(self):
        return (
            f"Аккаунт: {self.account.full_name}\n"
            f"{self.triggers_prettify}\n"
            f"{md.bold('Текст ответа на все сообщения: ')}\n"
            # f"{styled_message(self.answer_to_all_messages)}\n"
            f"{self.answer_to_all_messages}\n"
            f"{md.bold('Задержка перед ответом: ')}{md.code(self.delay_before_answer)} секунд\n"
            # f"{md.code(self.answer_to_all_messages)}\n"
        ).replace("`", "").replace("*", "").replace("_", "")

