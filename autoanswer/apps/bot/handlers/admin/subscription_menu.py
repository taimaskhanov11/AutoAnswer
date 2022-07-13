from aiogram import Router, types, F
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.fsm.state import StatesGroup, State

from autoanswer.apps.bot.callback_data.base_callback import Action, SubscriptionTemplateCallback
from autoanswer.apps.bot.markups.admin import subscription_markups
from autoanswer.config.config import load_yaml
from autoanswer.db.models import SubscriptionTemplate

router = Router()


class CreateSubscriptionTemplateStatesGroup(StatesGroup):
    type = State()
    finish = State()


async def get_subscriptions_templates(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer()
    subscriptions = await SubscriptionTemplate.all()
    await call.message.answer(f"Текущие подписки",
                              reply_markup=subscription_markups.get_subscriptions_templates(subscriptions))


# todo выгрузка подписок из файла
async def create_subscription_template(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer()
    await call.message.answer("Как вы хотите создать подписки",
                              reply_markup=subscription_markups.create_subscription_template())
    # await call.message.answer("Как вы хотите создать подписки",
    #                           reply_markup=subscription_markups.create_subscription())

    # await state.set_state(CreateSubscriptionStatesGroup.type)
    await state.set_state(CreateSubscriptionTemplateStatesGroup.finish)


async def create_subscription_template_type(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer()
    await call.message.answer("ФИНИШ")


async def create_subscription_template_finish(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer()
    # await message.answer("ФИНИШ")
    for s in await SubscriptionTemplate.all():
        await s.delete()
    sub_data: list[dict] = load_yaml("subscriptions.yaml")
    await SubscriptionTemplate.create_from_dict(sub_data)
    await call.message.answer("✅ Подписки успешно выгружены")


def register_subscriptions(dp: Router):
    dp.include_router(router)

    callback = router.callback_query.register
    message = router.message.register

    callback(get_subscriptions_templates, SubscriptionTemplateCallback.filter(F.action == Action.all), state="*")
    callback(create_subscription_template, SubscriptionTemplateCallback.filter(F.action == Action.create), state="*")
    message(create_subscription_template_type, state=CreateSubscriptionTemplateStatesGroup.type)
    callback(create_subscription_template_finish, state=CreateSubscriptionTemplateStatesGroup.finish)
