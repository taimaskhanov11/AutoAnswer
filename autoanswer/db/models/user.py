import datetime
import typing

from aiogram.types import BufferedInputFile
from loguru import logger
from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_queryset_creator, PydanticListModel
from tortoise.models import MODEL
from tortoise.transactions import in_transaction

from autoanswer.db.models.subscription import Subscription

if typing.TYPE_CHECKING:
    from autoanswer.db.models.account import Account


class Channel(models.Model):
    skin = fields.CharField(100, index=True)
    link = fields.CharField(100, index=True)


class User(models.Model):
    user_id = fields.BigIntField(index=True, unique=True)
    username = fields.CharField(32, unique=True, index=True, null=True)
    first_name = fields.CharField(255, null=True)
    last_name = fields.CharField(255, null=True)
    locale = fields.CharField(32, default="ru")
    registered_at = fields.DatetimeField(auto_now_add=True)
    is_search = fields.BooleanField(default=False)

    subscription: Subscription
    accounts: fields.ReverseRelation['Account']

    async def __aenter__(self):
        # Включение режима блокировки пока запрос не завершиться
        await self.switch_search_to(True)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Отключение режима поиска
        await self.switch_search_to(False)
        if exc_type:
            logger.exception(f"{exc_type}, {exc_val}, {exc_tb}")

    async def switch_search_to(self, status: bool):
        self.is_search = status
        await self.save(update_fields=["is_search"])

    @classmethod
    async def create(cls: typing.Type[MODEL], using_db=False, **kwargs) -> MODEL:
        async with in_transaction():
            user = await super().create(using_db, **kwargs)
            await Subscription.create(user=user)
            return user

    @classmethod
    async def count_all(cls):
        return await cls.all().count()

    @classmethod
    async def count_new_today(cls) -> int:
        date = datetime.date.today()
        # return await cls.filter(registered_at=).count()
        return await User.filter(
            registered_at__year=date.year,
            registered_at__month=date.month,
            registered_at__day=date.day,
        ).count()

    @classmethod
    async def reset_search(cls):
        count = await cls.filter(is_search=True).update(is_search=False)
        logger.trace(f"Сброс состояния поиска: {count}")

    @classmethod
    async def export_users(cls,
                           _fields: tuple[str],
                           _to: typing.Literal["text", "txt", "json"]) -> BufferedInputFile | str:
        UserPydanticList = pydantic_queryset_creator(User, include=_fields)
        users: PydanticListModel = await UserPydanticList.from_queryset(User.all())
        if _to == "text":
            users_list = list(users.dict()["__root__"])
            user_value_list = list(map(lambda x: str(list(x.values())), users_list))
            result = "\n".join(user_value_list)
        elif _to == "txt":
            users_list = list(users.dict()["__root__"])
            user_value_list = list(map(lambda x: str(list(x.values())), users_list))
            user_txt = "\n".join(user_value_list)
            result = BufferedInputFile(bytes(user_txt, "utf-8"), filename="users.txt")
        else:
            # json.dumps(ensure_ascii=False, default=str)
            result = BufferedInputFile(bytes(users.json(ensure_ascii=False), "utf-8"),
                                       filename="users.json")
        return result
