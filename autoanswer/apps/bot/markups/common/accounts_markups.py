from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from autoanswer.apps.bot.callback_data.base_callback import AccountCallback, Action
from autoanswer.db.models import Account


def view_accounts(accounts: list[Account]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for a in accounts:
        builder.button(
            text=f"{a.first_name}[{a.phone}]",
            callback_data=AccountCallback(pk=a.pk, action=Action.view)
        )
    builder.adjust(1)
    return builder.as_markup()


def view_account(account: Account) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Удалить",
        callback_data=AccountCallback(pk=account.pk, action=Action.delete)
    )
    return builder.as_markup()
