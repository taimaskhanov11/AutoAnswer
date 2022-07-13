from enum import Enum

from aiogram.dispatcher.filters.callback_data import CallbackData


class Action(str, Enum):
    all = "all"
    view = "view"
    create = "create"
    delete = "delete"
    edit = "edit"

    purchase = "purchase"


class AccountAction(str, Enum):
    bind = "bind"
    unbind = "unbind"


class UserCallback(CallbackData, prefix="user"):
    pk: int
    action: Action


class AccountCallback(CallbackData, prefix="account"):
    pk: int | None
    api_id: int | None
    action: Action | AccountAction


class TriggerAction(str, Enum):
    edit_answer = "edit_answer"
    edit_phrases = "edit_phrases"


class TriggerCallback(CallbackData, prefix="trigger"):
    pk: int | None
    action: Action | TriggerAction


class TriggerCollectionAction(str, Enum):
    switch = "switch"
    edit_answer_to_all_messages = "edit_answer_to_all_messages"
    edit_delay_before_answer = "edit_delay_before_answer"


class TriggerCollectionCallback(CallbackData, prefix="trigger_collection"):
    pk: int | None
    action: Action | TriggerCollectionAction
    payload: str | None


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
