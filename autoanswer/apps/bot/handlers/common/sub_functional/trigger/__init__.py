from aiogram import Router

from .trigger_menu import register_trigger_menu
from .trigger_solo import register_trigger_solo

router = Router()


def register_triggers(dp: Router):
    register_trigger_menu(router)
    register_trigger_solo(router)
    dp.include_router(router)
