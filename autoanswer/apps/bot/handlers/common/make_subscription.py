import datetime

from aiogram import Router, types, F
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.fsm.state import StatesGroup, State
from loguru import logger

from autoanswer.apps.bot.callback_data.base_callback import SubscriptionTemplateCallback, Action
from autoanswer.apps.bot.markups.common import make_subscription_markups
from autoanswer.config.config import TZ
from autoanswer.db.models import InvoiceCrypto, InvoiceQiwi, InvoiceYooKassa
from autoanswer.db.models import SubscriptionTemplate, User

router = Router()


class Purchase(StatesGroup):
    # method = State()
    # purchase = State()
    finish = State()


async def get_subscriptions_templates(message: types.Message, state: FSMContext):
    await state.clear()
    if isinstance(message, types.CallbackQuery):
        message = message.message
    # await call.answer()
    subscriptions = await SubscriptionTemplate.all()
    await message.answer("Выберите подписку",
                         reply_markup=make_subscription_markups.get_subscriptions_templates(subscriptions))


async def view_subscription_template(call: types.CallbackQuery, callback_data: SubscriptionTemplateCallback,
                                     state: FSMContext):
    # await call.answer()
    subscription = await SubscriptionTemplate.get(pk=callback_data.pk)
    # await call.message.answer(subscription.view,
    #                           reply_markup=make_subscription_markups.view_subscription_template(subscription))
    await call.message.edit_text(subscription.view)
    await call.message.edit_reply_markup(
        reply_markup=make_subscription_markups.view_subscription_template(subscription))


async def subscription_purchase(call: types.CallbackQuery, callback_data: SubscriptionTemplateCallback,
                                state: FSMContext):
    await state.clear()
    # await call.message.delete()
    await state.update_data(purchase_pk=callback_data.pk)
    # await call.message.answer(_("Выберите способ оплаты"), reply_markup=make_subscription_markups.subscription_purchase())
    await call.message.edit_reply_markup(make_subscription_markups.subscription_purchase())
    await state.set_state(Purchase.finish)
    # subscription.


@logger.catch(reraise=True)
async def subscription_purchase_method(call: types.CallbackQuery, user: User, state: FSMContext):
    await call.message.delete()
    data = await state.get_data()
    sub_pk = data["purchase_pk"]
    logger.trace(f"{sub_pk=}")
    subscription = await SubscriptionTemplate.get(pk=sub_pk)
    purchase_data = {
        "user": user,
        "subscription_template": subscription,
        "amount": subscription.price,
        "comment": subscription.title,
    }
    logger.trace(purchase_data)
    invoices_count = 0

    for cls in [InvoiceCrypto, InvoiceQiwi]:
        logger.trace(f"Check old invoices cls {cls.__name__}")
        count = await cls.filter(expire_at__gte=datetime.datetime.now(TZ), is_paid=False).count()
        invoices_count += count
    if invoices_count > 10:
        await call.message.answer("Слишком много неоплаченных чеков, повторите попытку позже.")
        await state.clear()
        return

    if call.data == "qiwi":
        logger.info(f"{user.user_id} Payment via QIWI")
        invoice = await InvoiceQiwi.create_invoice(**purchase_data)

    elif call.data == "yookassa":
        logger.info(f"{user.user_id} Payment via YooKassa")
        invoice = await InvoiceYooKassa.create_invoice(**purchase_data)

    else:  # call.data == crypto
        logger.info(f"{user.user_id} Payment via Crypto")
        invoice = await InvoiceCrypto.create_invoice(**purchase_data)

    await call.message.answer(f"✅ Чек на оплату подписки {subscription.view} Создан!",
                              reply_markup=make_subscription_markups.subscription_purchase_method(invoice.pay_url))
    await state.clear()


async def purchase_check(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("❗️ Проверка оплаты происходит автоматически в течении 1 минуты для оплаты через ЮKassa "
                              "и в течении 10 минут через криптовалюту.\n"
                              "После успешной операции вам придет уведомление об успешной оплате.")


def register_make_subscriptions(dp: router):
    dp.include_router(router)

    callback = router.callback_query.register
    message = router.message.register

    message(get_subscriptions_templates, text_startswith="💳")
    callback(get_subscriptions_templates, text="purchase")
    callback(view_subscription_template,
             SubscriptionTemplateCallback.filter((F.action == Action.view) & F.for_purchase))

    callback(subscription_purchase,
             SubscriptionTemplateCallback.filter(F.action == Action.purchase))
    callback(subscription_purchase_method, state=Purchase.finish)

    callback(purchase_check, text="check_purchase", state="*")
