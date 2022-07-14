from aiogram import Router, types
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils import markdown as md

from autoanswer.apps.bot.markups.common import common_markups
from autoanswer.db.models import User

router = Router()


async def start(message: types.Message | types.CallbackQuery, user: User, state: FSMContext):
    await state.clear()
    if isinstance(message, types.CallbackQuery):
        message = message.message

    await message.answer("👷 Используйте кнопки меню:", reply_markup=common_markups.main_menu())


async def profile(message: types.Message, user: User, state: FSMContext):
    # todo 7/10/2022 11:06 PM taima: Поправить профиль
    await state.clear()
    await message.answer(
        f"{md.bold('🔑 ID')}: {md.code(user.user_id)}\n"
        f"{md.bold('👤 Username')}: @{md.code(user.username)}\n"
        f"{md.bold('💵 Подписка')} - {md.italic(user.subscription.title)}\n"
        f"🕜 Осталось дней - {md.code(user.subscription.duration)}.\n",
    )


async def description(message: types.Message, state: FSMContext):
    await message.answer("📄 Инструкция:\n\n"
                         "➡️ Как начать работать с БОТом: https://t.me/autoanswers/7\n"
                         "➡️ Как настроить автоответы: https://t.me/autoanswers/9 \n"
                         "➡️ Тарифы: https://t.me/autoanswers/10 \n"
                         "📹 Видеоинструкция: https://youtu.be/e7SMoMNzTYo")


async def support(message: types.Message, state: FSMContext):
    await message.answer("🧑🏻‍💻 Поддержка: @ihelp_s", "html")


def register_common(dp: router):
    dp.include_router(router)

    callback = router.callback_query.register
    message = router.message.register

    message(start, commands="start", state="*")
    callback(start, text="start", state="*")
    message(profile, text_startswith="👤", state="*")
    message(description, text_startswith="📄", state="*")
    message(support, text_startswith="🙋‍♂", state="*")
