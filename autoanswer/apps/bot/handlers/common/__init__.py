from aiogram import Dispatcher, Router

from .common_menu import register_common
from .make_subscription import register_make_subscriptions
from .sub_functional import register_sub_functional

router = Router()


def register_common_handlers(dp: Dispatcher):
    register_common(router)
    register_make_subscriptions(router)
    register_sub_functional(router)
    dp.include_router(router)
