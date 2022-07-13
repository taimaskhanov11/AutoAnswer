from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from autoanswer.apps.bot.callback_data.base_callback import TriggerCollectionCallback, TriggerCollectionAction, \
    TriggerCallback, Action, TriggerAction, AccountCallback, AccountAction
from autoanswer.db.models.trigger import TriggerCollection, Trigger


def get_trigger_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    keyword = [
        ("👥Текущие аккаунты", TriggerCollectionCallback(action=Action.all)),
        ("➕👤 Привязать аккаунт", AccountCallback(action=AccountAction.bind)),
        # ("➖👤 Отвязать аккаунт", AccountCallback(action=AccountAction.unbind)),
    ]
    for text, callback_data in keyword:
        builder.button(text=text, callback_data=callback_data)
    builder.adjust(1)
    return builder.as_markup()


def get_trigger_collections(triggers_coll: list[TriggerCollection]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for trigger_col in triggers_coll:
        builder.button(text=trigger_col.account.full_name,
                       callback_data=TriggerCollectionCallback(pk=trigger_col.pk, action=Action.view))
    builder.adjust(1)
    return builder.as_markup()


def switch_trigger_collection_status(trigger_collection: TriggerCollection) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    tc = trigger_collection

    # off = ("✅", "▶️ Отключить")
    # on = ("🚫", "▶️ Включить")
    off = "✅"
    on = "🚫"

    reply_to_phrases = off if tc.reply_to_phrases else on
    reply_to_all_messages = off if tc.reply_to_all_messages else on
    reply_to_groups = off if tc.reply_to_groups else on
    reply_to_channels = off if tc.reply_to_channels else on
    reply_only_first_message = off if tc.reply_only_first_message else on

    builder.button(text=f"{reply_to_phrases} ответ на фразы",
                   callback_data=TriggerCollectionCallback(
                       pk=tc.pk,
                       action=TriggerCollectionAction.switch, payload="reply_to_phrases"))

    builder.button(text=f"{reply_to_all_messages} ответ на все сообщения",
                   callback_data=TriggerCollectionCallback(
                       pk=tc.pk,
                       action=TriggerCollectionAction.switch, payload="reply_to_all_messages"))

    builder.button(text=f"{reply_to_groups} ответ на группы",
                   callback_data=TriggerCollectionCallback(
                       pk=tc.pk,
                       action=TriggerCollectionAction.switch, payload="reply_to_groups"))

    builder.button(text=f"{reply_to_channels} ответ на каналы",
                   callback_data=TriggerCollectionCallback(
                       pk=tc.pk,

                       action=TriggerCollectionAction.switch, payload="reply_to_channels"))

    builder.button(text=f"{reply_only_first_message} ответ только на первое сообщение",
                   callback_data=TriggerCollectionCallback(
                       pk=tc.pk,
                       action=TriggerCollectionAction.switch, payload="reply_only_first_message"))

    builder.button(text="📝 Создать новый автоответ",
                   callback_data=TriggerCallback(pk=tc.pk, action=Action.create))

    builder.button(text="Изменить текст ответа на все сообщения",
                   callback_data=TriggerCollectionCallback(
                       pk=tc.pk,
                       action=TriggerCollectionAction.edit_answer_to_all_messages).pack())

    builder.button(text="Изменить данные",
                   callback_data=TriggerCollectionCallback(pk=tc.pk, action=Action.edit)),
    # builder.button(text="Удалить ответ",
    #                callback_data=TriggerCollectionCallback(pk=tc.pk, action=Action.delete)),
    builder.button(text="Отвязать аккаунт",
                   callback_data=AccountCallback(pk=tc.account_id, action=AccountAction.unbind)),
    builder.adjust(1)
    builder.button(text="⬅️ Назад", callback_data="start")
    builder.adjust(1, 1, 2, 1, 1, 1, 1)
    return builder.as_markup()


def edit_trigger_collection(trigger_col: TriggerCollection) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for num, trigger in enumerate(trigger_col.triggers, 1):
        builder.button(text=f"{num}",
                       callback_data=TriggerCallback(pk=trigger.pk, action=Action.view))
    builder.adjust(8)
    k1 = InlineKeyboardButton(text="Изменить текст ответа на все сообщения",
                              callback_data=TriggerCollectionCallback(
                                  pk=trigger_col.pk,
                                  action=TriggerCollectionAction.edit_answer_to_all_messages).pack())

    k2 = InlineKeyboardButton(text="Изменить задержку перед ответом",
                              callback_data=TriggerCollectionCallback(
                                  pk=trigger_col.pk,
                                  action=TriggerCollectionAction.edit_delay_before_answer).pack())

    k3 = InlineKeyboardButton(text="⬅️ Назад",
                              callback_data=TriggerCollectionCallback(
                                  pk=trigger_col.pk, action=Action.view).pack())
    builder.row(k1)
    builder.row(k2)
    builder.row(k3)

    # builder.button(text="Изменить текст ответа на все сообщения",
    #                callback_data=TriggerCollectionCallback(
    #                    pk=trigger_col.pk,
    #                    action=TriggerCollectionAction.edit_answer_to_all_messages))

    # builder.button(text="⬅️ Назад", callback_data=TriggerCollectionCallback(pk=trigger_col.pk, action=Action.view))
    return builder.as_markup()


def get_trigger(trigger: Trigger) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Изменить текст ответа",
                   callback_data=TriggerCallback(pk=trigger.pk,
                                                 action=TriggerAction.edit_answer))
    builder.button(text="Изменить фразы",
                   callback_data=TriggerCallback(pk=trigger.pk,
                                                 action=TriggerAction.edit_phrases))

    builder.button(text="Удалить ответ", callback_data=TriggerCallback(pk=trigger.pk, action=Action.delete))
    builder.button(text="⬅️ Назад",
                   callback_data=TriggerCollectionCallback(pk=trigger.trigger_collection_id, action=Action.view))
    builder.adjust(1)
    return builder.as_markup()
