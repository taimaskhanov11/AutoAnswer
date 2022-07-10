from aiogram import Router, types
from aiogram.dispatcher.fsm.context import FSMContext

from autoanswer.apps.bot.markups.common import common_markups
from autoanswer.db.models import User
from aiogram.utils import markdown as md
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
        f"{md.hbold('🔑 ID')}: {md.hcode(user.user_id)}\n"
        f"{md.hbold('👤 Username')}: @{md.hcode(user.username)}\n"
        f"{md.hbold('💵 Подписка')} - {md.hitalic(user.subscription.title)}\n"
        f"🕜 Осталось дней до завершения до завершения подписки - {md.hcode(user.subscription.duration)}.\n",
    )


def register_common(dp: router):
    dp.include_router(router)

    callback = router.callback_query.register
    message = router.message.register

    message(start, commands="start", state="*")
    callback(start, text="start", state="*")
    message(profile, text_startswith="👤", state="*")
