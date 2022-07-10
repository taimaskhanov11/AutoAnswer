from enum import Enum

from aiogram.dispatcher.filters.callback_data import CallbackData


class Action(str, Enum):
    all = "all"
    view = "view"
    create = "create"
    delete = "delete"
    edit = "edit"

    connect = "connect"
    purchase = "purchase"

class UserCallback(CallbackData, prefix="user"):
    pk: int
    action: Action


class AccountCallback(CallbackData, prefix="account"):
    pk: int | None
    api_id: int | None
    action: Action


class ChannelCallback(CallbackData, prefix="channel"):
    pk: int | None
    action: str


class SubscriptionCallback(CallbackData, prefix="subscription"):
    pk: int | None
    action: Action


class SubscriptionTemplateCallback(CallbackData, prefix="subscription_template"):
    pk: int | None
    action: Action
    for_purchase: bool | None
