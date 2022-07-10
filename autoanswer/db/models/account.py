import typing

from loguru import logger
from tortoise import fields, models

from autoanswer.db.models.user import User

if typing.TYPE_CHECKING:
    from autoanswer.apps.controller.controller import ConnectAccountController


class Account(models.Model):
    user_id = fields.BigIntField(index=True, unique=True)
    username = fields.CharField(32, unique=True, index=True, null=True)
    first_name = fields.CharField(255, null=True)
    last_name = fields.CharField(255, null=True)
    registration_date = fields.DatetimeField(auto_now_add=True)
    api_id = fields.BigIntField(unique=True, index=True)
    api_hash = fields.CharField(max_length=50)
    phone = fields.CharField(max_length=20)
    owner: fields.ForeignKeyRelation["User"] = fields.ForeignKeyField("models.User", on_delete=fields.CASCADE)

    def __str__(self):
        return (super().__str__() +
                f"\nAPI_ID: {self.api_id}\n"
                f"API_HASH: {self.api_hash}\n"
                f"Номер: {self.phone}")

    @classmethod
    async def connect(cls, controller: 'ConnectAccountController', account_data: dict):
        user = await User.get(user_id=controller.user_id)
        acc, is_create = await cls.get_or_create(
            owner=user,
            api_id=controller.api_id,
            defaults={**controller.dict(exclude={"user_id", "username", "api_id"}) |
                        {"user_id": account_data["id"],
                         "username": account_data["username"],
                         "first_name": account_data["first_name"],
                         "last_name": account_data["last_name"]}}
        )
        if not is_create:
            logger.info(f"{acc} уже существует")
        # await user.save()
