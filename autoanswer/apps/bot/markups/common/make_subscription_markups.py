from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from autoanswer.apps.bot.callback_data.base_callback import Action, SubscriptionTemplateCallback
from autoanswer.db.models import SubscriptionTemplate
from autoanswer.loader import _


def get_subscriptions_templates(subscriptions: list[SubscriptionTemplate]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for sub in subscriptions:
        builder.button(
            text=str(sub),
            callback_data=SubscriptionTemplateCallback(pk=sub.pk, action=Action.view, for_purchase=True)
        )
    builder.button(text=_("⬅️ Назад"), callback_data="start")
    builder.adjust(1)

    return builder.as_markup()


def view_subscription_template(subscription: SubscriptionTemplate):
    builder = InlineKeyboardBuilder()
    builder.button(text=_("💳 Приобрести"),
                   callback_data=SubscriptionTemplateCallback(pk=subscription.pk, action=Action.purchase))
    builder.button(text=_("⬅️ Назад"), callback_data="purchase")
    builder.adjust(1)
    return builder.as_markup()


def subscription_purchase():
    builder = InlineKeyboardBuilder()

    builder.button(text=_("₿ Оплата криптовалютой"), callback_data="crypto")
    builder.button(text=_("🥝 Оплата через QIWI"), callback_data="qiwi")
    builder.button(text=_("⬅️ Назад"), callback_data="purchase")
    builder.adjust(1)
    return builder.as_markup()


def subscription_purchase_method(url):
    builder = InlineKeyboardBuilder()

    builder.button(text=_("✅ Перейти к оплате"), url=url)
    builder.button(text=_("⏳ Я оплатил"), callback_data="check_purchase")
    builder.button(text=_("⬅️ Назад"), callback_data="purchase")
    builder.adjust(1)
    return builder.as_markup()
