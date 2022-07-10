import re
from pprint import pprint

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from autoanswer.apps.bot.callback_data.base_callback import Action, SubscriptionTemplateCallback
from autoanswer.apps.bot.markups.utils import get_inline_keyboard, get_inline_url_keyboard, get_inline_button

admin_back_buttons = ("⬅️ Назад", "admin")
back_to_admin = get_inline_button(("⬅️ Назад", "admin"))


def admin_start():
    keyword = [
        # ("📄 Список каналов для обязательной подписки", ChannelCallback(action=Action.all)),
        # ("✍ Добавить канал для обязательной подписки", ChannelCallback(action=Action.create)),
        ("📈 Общая информация о боте", "statistics"),
        ("🔖 Сделать рассылку", "send_mail"),
        ("⚙ Настройки бота", "bot_settings"),
        ("🧾 Подписки", SubscriptionTemplateCallback(action=Action.all)),
        ("👥 Экспорт пользователей", "export_users"),
        ("✍ Изменить текст меню", "change_menu"),
    ]
    builder = InlineKeyboardBuilder()
    for i in keyword:
        builder.button(text=i[0], callback_data=i[1])

    builder.adjust(1)
    return builder.as_markup()
    # return get_inline_keyboard(keyword)


def admin_button():
    keyboard = [
        (("Админ панель", "admin"),),
    ]
    return get_inline_keyboard(keyboard)


def back():
    keyboard = [
        [admin_back_buttons]
    ]
    return get_inline_keyboard(keyboard)


def export_users():
    keyboard = [
        (("Отправить сообщением", "test"),),
        (("Отправить тестовый файл", "txt"),),
        (("Отправить сообщением", "test"),),
    ]
    return get_inline_keyboard(keyboard)


def export_users_send_type():
    keyboard = [
        (("Отправить сообщением", "text"),),
        (("Отправить тестовый файл", "txt"),),
        (("Отправить json-file", "json"),),
        [admin_back_buttons]
    ]
    return get_inline_keyboard(keyboard)


def start_message():
    keyboard = [
        (("Изменить", "edit_start_message"),),
    ]
    return get_inline_keyboard(keyboard)


def send_mail_preview():
    keyboard = [
        (("➕ Добавить url кнопки", "add_button"),),
        (("✅ Подтвердить", "accept"),),
        (("❌ Отменить", "admin"),),
        # (("❌ Отменить", "cancel"),),
    ]
    return get_inline_keyboard(keyboard)


def send_mail_done(status: bool = True):
    keyboard = [
        (("⏸ Пауза", "pause_mail"),) if status else (("▶️ Возобновить", "continue_mail"),),
        (("⏹ Стоп", "stop_mail"),),
    ]
    return get_inline_keyboard(keyboard)


@logger.catch
def parse_buttons(text: str):
    keyboard = []
    # change_keyboard = re.split(r'\s\n|\w\n|$', text)[:-1]
    # change_keyboard = re.split(r'[(\s)\w](\n)', text)[:-1]
    # change_keyboard = re.split(r'\s\n|[^|]\n', text)
    change_keyboard = re.split(r'(?<=\w\n)', text)
    # pprint(change_keyboard)
    for but_parent in change_keyboard:
        keyboard.append(
            list(map(lambda x: list(map(lambda x: x.strip(), x.split('-'))), but_parent.split("|\n")))
        )
    return keyboard
    # return get_inline_url_keyboard(keyboard)
    # data = re.findall(r"(\bwall|\bphoto)(-?\d+_\d+)", i)


def send_mail_add_button(text: str) -> InlineKeyboardMarkup:
    keyboard = [
        # (("➕ Добавить еще url кнопки", "add_button"),),
        (("➕ Добавить новый url кнопки", "add_button"),),
        (("✅ Подтвердить", "accept"),),
        (("❌ Отменить", "cancel"),),
    ]
    inline_keyboard = get_inline_keyboard(keyboard)
    inline_url_keyboard = get_inline_url_keyboard(parse_buttons(text))
    inline_url_keyboard.inline_keyboard.extend(inline_keyboard.inline_keyboard)
    return inline_url_keyboard


def send_mail_add_button_in_current(markup: InlineKeyboardMarkup) -> InlineKeyboardMarkup:
    keyboard = [
        # (("➕ Добавить еще url кнопки", "add_button"),),
        (("➕ Добавить новый url кнопки", "add_button"),),
        (("✅ Подтвердить", "accept"),),
        (("❌ Отменить", "cancel"),),
    ]

    inline_keyboard = get_inline_keyboard(keyboard)
    new_markup = markup.copy()
    new_markup.inline_keyboard.extend(inline_keyboard.inline_keyboard)
    return markup


if __name__ == '__main__':
    text = ("Кнопка 1 - https://www.example1.com |\n"
            "Кнопка 2 - https://www.example2.com\n"
            "Кнопка 3 - https://www.example3.com\n"
            "Кнопка 4 - https://www.example4.com")
    # pprint(send_mail_preview().inline_keyboard)
    pprint(parse_buttons(text))
    # print(send_mail_add_button(text))
    # parse_buttons("Кнопка 1 - https://www.example1.com,\n"
    #               "Кнопка 2 - https://www.example2.com,\n"
    #               "Кнопка 3 - https://www.example3.com|\n"
    #               "Кнопка 4 - https://www.example4.com\n")
