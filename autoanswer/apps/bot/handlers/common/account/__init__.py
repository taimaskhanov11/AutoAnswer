from aiogram import Router

from .accounts_manager import register_accounts_manager
from .connect_account import register_connect_account

router = Router()


def register_account(dp: Router):
    register_accounts_manager(router)
    register_connect_account(router)
    dp.include_router(router)
