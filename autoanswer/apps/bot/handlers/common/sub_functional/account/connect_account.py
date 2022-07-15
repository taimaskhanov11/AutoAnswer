import asyncio
from asyncio import Queue

from aiogram import types, Router, F
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils import markdown as md
from loguru import logger

from autoanswer.apps.bot.callback_data.base_callback import AccountCallback, AccountAction
from autoanswer.apps.bot.markups.admin import admin_markups
from autoanswer.apps.bot.markups.common import common_markups, accounts_markups
from autoanswer.apps.bot.temp import controller_codes_queue, controllers
from autoanswer.apps.controller.controller import ConnectAccountController
from autoanswer.db.models import User, Account
from autoanswer.loader import _

router = Router()


class ConnectAccount(StatesGroup):
    api = State()
    code = State()


class UnlinkAccount(StatesGroup):
    unbind = State()


link = md.link("ссылке", "https://my.telegram.org/auth?to=apps ")


async def connect_account(call: types.CallbackQuery, user: User, state: FSMContext):
    await state.clear()
    await user.fetch_related("accounts")
    if len(user.accounts) >= 3:
        await call.message.answer(_("Вы не можете подключить более 3 аккаунтов"))
        return

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
            owner=user,
            phone=phone,
            api_id=api_id,
            api_hash=api_hash
        )
        controller_codes_queue[user.user_id] = Queue(maxsize=1)
        asyncio.create_task(controller.start())
        await state.set_state(ConnectAccount.code)
        await message.answer(_("Введите код подтверждения из сообщения Телеграмм с префиксом code, "
                               f"в только таком виде: {md.code('code<ваш код>')}.\n"
                               f"Например: {md.code('code43123')}\n"
                               "Если отправить просто цифры то тг обнулит код\n"))
    except Exception as e:
        logger.critical(e)
        await message.answer(_("Неправильный ввод"))


async def connect_account_code(message: types.Message, user: User, state: FSMContext):
    code = message.text
    if code.isdigit():
        await message.answer(_(f"❌ Неправильный ввод код.\n"
                               f"Пожалуйста повторите попытку создания с первого этапа и введите "
                               f"код с префиксом code как указано в примере ниже\n"
                               f"Например: {md.code('code43123')}"),
                             reply_markup=admin_markups.back())
        await state.clear()
        return
    code = message.text.replace("code", "").strip()
    queue = controller_codes_queue.get(user.user_id)
    queue.put_nowait(code)
    await message.answer(
        _("Код получен, ожидайте завершения\nЕсли все прошло успешно Вам придет сообщение в личный чат."))
    await state.clear()


async def unbind_account(
        call: types.CallbackQuery,
        callback_data: AccountCallback,
        user: User,
        state: FSMContext):
    await state.update_data(account_pk=callback_data.pk)
    await call.message.answer("Вы действительно хотите отключить аккаунт?",
                              reply_markup=accounts_markups.unbind_account())
    await state.set_state(UnlinkAccount.unbind)


async def unbind_account_done(
        call: types.CallbackQuery,
        user: User,
        state: FSMContext):
    if call.data == "yes":
        data = await state.get_data()
        account = await Account.get_or_none(pk=data["account_pk"])
        if account:
            await account.delete()
            if controller := controllers.get(account.api_id):
                await controller.stop()
            await call.message.answer(_("Аккаунт успешно отключен"))
        else:
            await call.message.answer(_("Аккаунт не найден"))
    else:
        await call.message.answer("Удаление отменено")
    await state.clear()


def register_connect_account(dp: Router):
    dp.include_router(router)

    callback = router.callback_query.register
    message = router.message.register

    callback(connect_account, AccountCallback.filter(F.action == AccountAction.bind))
    message(connect_account_phone, state=ConnectAccount.api)
    message(connect_account_code, state=ConnectAccount.code)

    callback(unbind_account, AccountCallback.filter(F.action == AccountAction.unbind))
    callback(unbind_account_done, state=UnlinkAccount.unbind)
