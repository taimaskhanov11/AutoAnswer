from aiogram import Router, types, F
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.fsm.state import StatesGroup, State

from autoanswer.apps.bot import temp
from autoanswer.apps.bot.callback_data.base_callback import AccountCallback, Action
from autoanswer.apps.bot.markups.admin import admin_markups
from autoanswer.apps.bot.markups.common import accounts_markups
from autoanswer.apps.controller.controller import Controller
from autoanswer.db.models import User, Account
from autoanswer.loader import _

router = Router()


class JoinChatStatesGroup(StatesGroup):
    join = State()


class Spam(StatesGroup):
    count = State()
    interval = State()
    view = State()
    text = State()
    chat = State()

    choice = State()


async def view_accounts(call: types.CallbackQuery,
                        user: User,
                        callback_data: AccountCallback,
                        state: FSMContext):
    await state.set_state()
    accounts = await user.accounts
    await call.message.answer(_("Текущие аккаунты"), reply_markup=accounts_markups.view_accounts(accounts))


async def view_account(call: types.CallbackQuery, callback_data: AccountCallback, state: FSMContext):
    await state.set_state()
    account = await Account.get(pk=callback_data.pk)
    await call.message.answer(str(account), 'markdown', reply_markup=accounts_markups.view_account(account))


async def delete_account(call: types.CallbackQuery, callback_data: AccountCallback, state: FSMContext):
    await state.set_state()
    account = await Account.get(pk=callback_data.pk)
    await call.message.answer("Аккаунт удален", admin_markups.back())
    controller: Controller = temp.controllers[call.from_user.id][account.api_id]
    await controller.stop()


def register_accounts_manager(dp: Router):
    dp.include_router(router)

    callback = router.callback_query.register
    message = router.message.register

    callback(view_accounts, AccountCallback.filter(F.action == Action.all))
    callback(view_account, AccountCallback.filter(F.action == Action.view))
    callback(delete_account, AccountCallback.filter(F.action == Action.delete))
