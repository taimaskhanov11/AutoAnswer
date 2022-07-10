from aiogram import F, Router, types
from aiogram.dispatcher.fsm.context import FSMContext
# from aiogram.dispatcher.filters
from aiogram.dispatcher.fsm.state import StatesGroup, State
from loguru import logger

from autoanswer.apps.bot.callback_data.base_callback import ChannelCallback, Action
from autoanswer.apps.bot.markups.admin import channel_markups, admin_markups
from autoanswer.apps.bot.utils import parse_channel_link
from autoanswer.db.models.user import Channel

router = Router()


class NewChat(StatesGroup):
    done = State()


class NewSponsorChat(StatesGroup):
    done = State()


async def view_chats(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer()
    chats = await Channel.all()
    await call.message.answer(f"Все чаты для обязательной подписки:",
                              reply_markup=channel_markups.view_channels(chats))


async def create_chat(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer(f"Добавьте бота в чат и сделайте администратором, чтобы проверять подписки.\n"
                              f"Введите ссылку на канал. "
                              f"Введите ссылку по которому должны будут пройти пользователи и через пробел фактическую ссылку на канал для проверки ботом\n"
                              f"Например:\n"
                              f"https://t.me/+bIBc0e-525k2MThi https://t.me/mychannel",
                              reply_markup=admin_markups.back())
    await state.set_state(NewChat.done)


async def create_chat_done(message: types.Message, state: FSMContext):
    try:
        await state.clear()
        skin, link = parse_channel_link(message.text)
        chat = await Channel.create(skin=skin, link=link)
        await message.answer(f"Чат для подписки: {chat}\n успешно добавлен", reply_markup=admin_markups.back())
    except Exception as e:
        logger.warning(e)
        await message.answer("Неправильный ввод", reply_markup=admin_markups.back())


async def view_chat(call: types.CallbackQuery, callback_data: ChannelCallback, state: FSMContext):
    await state.clear()
    chat = await Channel.get(pk=callback_data.pk)
    await call.message.answer(f"{chat}",
                              reply_markup=channel_markups.touch_channel(chat))


async def delete_chat(call: types.CallbackQuery, callback_data: ChannelCallback, state: FSMContext):
    await state.clear()
    await state.update_data(delete_chat=callback_data.pk)
    chat = await Channel.get(pk=callback_data.pk)
    await chat.delete()
    await call.message.answer(f"Канал для подписки: {chat} успешно удален")


def register_channel(dp: Router):
    dp.include_router(router)

    callback = router.callback_query.register
    message = router.message.register

    callback(view_chats, ChannelCallback.filter(F.action == Action.all), state="*")
    callback(create_chat, ChannelCallback.filter(F.action == Action.create), state="*")
    message(create_chat_done, state=NewChat.done)
    callback(view_chat, ChannelCallback.filter(F.action == Action.view), state="*")
    callback(delete_chat, ChannelCallback.filter(F.action == Action.delete), state="*")
