import asyncio
from asyncio import Queue

from aiogram import types, Router, F
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils import markdown as md
from loguru import logger

from autoanswer.apps.bot.callback_data.base_callback import AccountCallback, Action
from autoanswer.apps.bot.markups.admin import admin_markups
from autoanswer.apps.bot.markups.common import common_markups
from autoanswer.apps.bot.temp import controller_codes_queue, controllers
from autoanswer.apps.controller.controller import ConnectAccountController
from autoanswer.db.models import User, Account
from autoanswer.loader import _

router = Router()


class ConnectAccount(StatesGroup):
    api = State()
    code = State()


class UnlinkAccount(StatesGroup):
    unlink = State()


link = md.hlink("ссылке", "https://my.telegram.org/auth?to=apps ")


async def connect_account(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer(_(
        f"▫️ Для подключения аккаунта перейдите по 👉🏻 {link}\n\n"
        "▫️ Введите данные аккаунта (номер телефона и затем код) \n\n"
        "▫️ Сохраните значения полей api_id и api_hash.\n\n"
        "️▫️ Отправьте БОТу эти значение в формате api_id:api_hash:номер телефона. \n\nℹ️ Например:\n"
        "123445:asdf31234fads:79622231741 \n\n 🚫 НЕ РЕКОМЕНДУЕМ подключать:\n"
        "- Новореги (недавно зарегистрированные аккаунты);\n"
        "- Аккаунты с виртуальным номером.\n"
        "Такие аккаунты с высокой вероятностью получат ограничение от Telegram."
    ), reply_markup=common_markups.back())
    await state.set_state(ConnectAccount.api)


async def connect_account_phone(message: types.Message, user: User, state: FSMContext):
    try:
        api_id, api_hash, phone = tuple(map(lambda x: x.strip(), message.text.split(":")))

        account = await Account.get_or_none(api_id=api_id)
        if account:
            await message.answer(_("Этот аккаунт уже подключен"))
            await state.clear()
            return

        logger.info(f"{user.username}| Полученные данные {api_id}|{api_hash}|{phone}")
        controller = ConnectAccountController(
            user_id=user.user_id,
            username=user.username,
            phone=phone,
            api_id=api_id,
            api_hash=api_hash
        )
        controller_codes_queue[user.user_id] = Queue(maxsize=1)
        asyncio.create_task(controller.start())
        controllers[controller.user_id][controller.api_id] = controller
        await state.set_state(ConnectAccount.code)
        await message.answer(_("Введите код подтверждения из сообщения Телеграмм с префиксом code, "
                               f"в только таком виде: {md.code('code<ваш код>')}.\n"
                               f"Например: {md.code('code43123')}\n"
                               "Если отправить просто цифры то тг обнулит код\n"), 'markdown')
    except Exception as e:
        logger.critical(e)
        await message.answer(_("Неправильный ввод"))


async def connect_account_code(message: types.Message, user: User, state: FSMContext):
    code = message.text
    if code.isdigit():
        await message.answer(_(f"❌ Неправильный ввод код.\n"
                               f"Пожалуйста повторите попытку создания с первого этапа и введите "
                               f"код с префиксом code как указано в примере ниже\n"
                               f"Например: {md.hcode('code43123')}"),
                             reply_markup=admin_markups.back())
        await state.clear()
        return
    code = message.text.replace("code", "").strip()
    queue = controller_codes_queue.get(user.user_id)
    queue.put_nowait(code)
    await message.answer(
        _("Код получен, ожидайте завершения\nЕсли все прошло успешно Вам придет сообщение в личный чат."))
    await state.clear()


def register_connect_account(dp: Router):
    dp.include_router(router)

    callback = router.callback_query.register
    message = router.message.register

    callback(connect_account, AccountCallback.filter(F.action == Action.connect))
    message(connect_account_phone, state=ConnectAccount.api)
    message(connect_account_code, state=ConnectAccount.code)
