from aiogram import Dispatcher, Router

from .common_menu import register_common
from .make_subscription import register_make_subscriptions
from .account import register_account


router = Router()


def register_common_handlers(dp: Dispatcher):
    register_common(router)
    register_make_subscriptions(router)
    register_account(router)
    dp.include_router(router)
