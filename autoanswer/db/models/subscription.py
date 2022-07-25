import typing

from loguru import logger
from tortoise import models, fields
from tortoise.functions import Sum

from autoanswer.apps.bot.temp import controllers

if typing.TYPE_CHECKING:
    from autoanswer.db.models.user import User


class AbstractSubscription(models.Model):
    pass


# todo 5/31/2022 12:38 PM taima: сделать дневной лимит
class SubscriptionTemplate(models.Model):
    """Шаблоны для создания подписок"""
    title = fields.CharField(255, default="Базовая подписка", index=True)
    price = fields.IntField(default=0)
    duration = fields.IntField(default=1)

    def __str__(self):
        return self.title

    @property
    def view(self):
        return (f"Название: {self.title}\n"
                f"Цена: {self.price}\n"
                f"Длительность подписки: {self.duration}\n")
        # f"Лимит: {self.limit or 'Безлимит'}")

    @classmethod
    async def create_from_dict(cls, data: list | dict) -> list | tuple["SubscriptionTemplate", bool]:
        if isinstance(data, list):
            return [await SubscriptionTemplate.get_or_create(**obj) for obj in data]
        else:
            return await SubscriptionTemplate.get_or_create(**data)

    @classmethod
    async def refresh_subscription_templates(cls, sub_data: list[dict]):
        # for s in await SubscriptionTemplate.all():
        #     await s.delete()
        await cls.create_from_dict(sub_data)
        logger.info("Subscriptions refreshed")


class Subscription(SubscriptionTemplate):
    """Подписки с привязкой к пользователю"""
    title = fields.CharField(255, default="Базовая подписка")
    connected_at = fields.DatetimeField(auto_now_add=True)
    user: "User" = fields.OneToOneField("models.User")

    @classmethod
    async def decreased_duration(cls):
        """Reduce the subscription duration for all users by 1 day"""
        logger.info("Reducing subscription duration")
        for s in await cls.all().prefetch_related("user__accounts__trigger_collection"):
            if s.duration > 0:
                s.duration -= 1
                await s.save(update_fields=["duration"])
                if s.duration == 0:
                    logger.info(f"Subscription {s} expired")
                    for account in await s.user.accounts:
                        await account.fetch_related("trigger_collection")
                        if controller := controllers.get(account.trigger_collection.pk):
                            await controller.stop()

        logger.info("Subscription duration reduced")

    @classmethod
    async def all_limits(cls) -> int:
        return (await cls.all().annotate(count=Sum("limit")).values("count"))[0].get("count")

    @property
    def view(self):
        return (f"Название: {self.title}\n"
                # f"Цена {self.price}\n"
                f"Длительность подписки: {self.duration}\n")
        # f"Лимит: {self.limit or 'Безлимит'}")
