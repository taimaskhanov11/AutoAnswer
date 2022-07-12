import typing
from pathlib import Path

from aiogram.utils import markdown as md
from loguru import logger
from pydantic import BaseModel, validator
from telethon import events
from tortoise import fields, models

from autoanswer.apps.bot.temp import controllers
from autoanswer.config.config import MEDIA_DIR

if typing.TYPE_CHECKING:
    from autoanswer.db.models.account import Account


class File(BaseModel):
    path: str | Path | None
    caption: str | None

    @validator('path')
    def correct_path(cls, v):
        return MEDIA_DIR / v


class Trigger(models.Model):
    phrases = fields.JSONField()  # list
    answer = fields.TextField(null=True)
    file_name = fields.TextField(null=True)
    trigger_collection: fields.ForeignKeyRelation['TriggerCollection'] = fields.ForeignKeyField(
        "models.TriggerCollection", related_name="triggers")

    def __str__(self):
        _str = (f"{md.hbold('Фразы: ')}️ {md.hcode(', '.join(self.phrases))}\n"
                f"{md.hbold('Текст ответа: ')}{md.hcode(self.answer)}")
        if self.file_name:
            _str += f"\n{md.hbold('Файл: ')}{md.hcode(self.file_name)}"
        return _str

    async def set_phrases(self, phrases: list | str):
        self.phrases = self.fix_phrases(phrases)
        await self.save(update_fields=["phrases"])

    @classmethod
    def fix_phrases(cls, phrases: str | list):
        if isinstance(phrases, str):
            phrases = list(map(lambda x: x.strip(), phrases.split(",")))
        return phrases

    async def set_answer(self, answer: str):
        self.answer = answer.lower()
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
    account: 'Account' = fields.OneToOneField("models.Account", related_name="trigger_collection")
    reply_to_phrases = fields.BooleanField(default=False)
    reply_to_all_messages = fields.BooleanField(default=False)
    reply_to_groups = fields.BooleanField(default=False)
    reply_to_channels = fields.BooleanField(default=False)
    reply_only_first_message = fields.BooleanField(default=False)

    delay_before_answer = fields.IntField(default=0)
    answer_to_all_messages = fields.TextField(null=True)
    triggers: fields.ReverseRelation[Trigger]

    @classmethod
    async def get_from_local_or_full(cls, pk: int | str):
        if controller := controllers.get(pk):
            return controller.trigger_collection
        return await cls.get(id=pk).prefetch_related("triggers", "account")

    @classmethod
    async def refresh_if_local(cls, pk: int | str):
        if controller := controllers.get(pk):
            await controller.trigger_collection.refresh_from_db()

    @classmethod
    async def get_full(cls, pk: int | str):
        return await cls.get(id=pk).prefetch_related("triggers", "account")

    async def switch_status(self, field: str):
        setattr(self, field, not getattr(self, field))
        await self.save(update_fields=[field])

    async def set_answer(self, answer: str):
        self.answer_to_all_messages = answer
        await self.save(update_fields=["answer_to_all_messages"])

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
                return self.answer_to_all_messages
            logger.trace("Ответ не найден -> {text}", text=event.message.text)
        else:
            logger.debug("Не соответствует требованиям. Поиск отключен")

    def __str__(self):
        triggers_str = ""
        for num, value in enumerate(self.triggers, 1):
            p_num = md.hcode(f'# {num}')
            triggers_str += f"{p_num}\n{value}\n\n"
        return (
            f"Аккаунт: {self.account.full_name}\n"
            f"{triggers_str}\n"
            f"{md.hbold('Текст ответа на все сообщения: ')}\n"
            f"{md.hcode(self.answer_to_all_messages)}\n"
        )
