from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def main_menu() -> ReplyKeyboardMarkup:
    keyword = [
        "👤 Мой профиль",
        "💳 Купить подписку",
        "📄 Описание",
        "🙋‍♂ Поддержка",
        "⚙ Настроить автоответы",

    ]
    builder = ReplyKeyboardBuilder()
    for i in keyword:
        builder.button(text=i)
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def menu_button() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Главное меню", callback_data="start")
    return builder.as_markup()


def back() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад", callback_data="start")
    return builder.as_markup()
