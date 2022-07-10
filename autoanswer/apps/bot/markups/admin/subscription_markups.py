from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from autoanswer.apps.bot.callback_data.base_callback import Action, SubscriptionTemplateCallback
from autoanswer.apps.bot.markups.admin.admin_markups import back_to_admin
from autoanswer.db.models import SubscriptionTemplate


def get_subscriptions_templates(subscriptions: list[SubscriptionTemplate]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for sub in subscriptions:
        builder.button(
            text=str(sub),
            callback_data=SubscriptionTemplateCallback(pk=sub.pk, action=Action.view)
        )
    builder.button(text="➕ Создать новую подписку", callback_data=SubscriptionTemplateCallback(action=Action.create))
    builder.add(back_to_admin)
    builder.adjust(1)
    return builder.as_markup()


def create_subscription_template() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    # builder.button(text="Через файл json", callback_data="json")
    # builder.button(text="В ручную", callback_data="custom")
    builder.button(text="Обновить подписки из конфига", callback_data="yaml")
    builder.row(back_to_admin)
    # builder.button(text="Загрузить новые подписки из файла", callback_data="yaml")
    #
    # builder = ReplyKeyboardBuilder()
    # builder.button(text="Через файл json")
    # builder.button(text="В ручную")
    return builder.as_markup(resize_keyboard=True)
