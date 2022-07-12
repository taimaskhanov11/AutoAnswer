from aiogram import Router

from autoanswer.apps.bot.filters.subscription_filters import SubscriptionFilter
from .account import register_account
from .trigger import register_triggers

router = Router()


def register_sub_functional(dp: Router):
    router.message.filter(SubscriptionFilter())
    router.callback_query.filter(SubscriptionFilter())
    register_triggers(router)
    register_account(router)
    dp.include_router(router)
