from aiogram import Router, types, F
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.fsm.state import StatesGroup, State
from aiogram.utils import markdown as md

from autoanswer.apps.bot.callback_data.base_callback import TriggerCollectionCallback, TriggerCollectionAction, \
    Action
from autoanswer.apps.bot.markups.common import triggers_markups
from autoanswer.apps.bot.utils import part_sending
from autoanswer.db.models import User
from autoanswer.db.models.trigger import TriggerCollection

router = Router()


class EditTriggerCollectionAnswer(StatesGroup):
    edit = State()


async def trigger_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🔧 Настройка ответов:", reply_markup=triggers_markups.get_trigger_menu())


async def get_trigger_collections(
        call: types.CallbackQuery,
        user: User,
        callback_data: TriggerCollectionCallback,
        state: FSMContext):
    await state.clear()
    triggers_coll = await user.get_trigger_collections()
    if not triggers_coll:
        await call.message.answer("У вас нет ни одной коллекции ответов")
        return
    await call.message.answer("Текущая подключенный аккаунты:",
                              reply_markup=triggers_markups.get_trigger_collections(triggers_coll))


async def get_trigger_collection(
        call: types.CallbackQuery,
        callback_data: TriggerCollectionCallback,
        state: FSMContext,
        user: User):
    await state.clear()
    trigger_collection = await TriggerCollection.get_from_local_or_full(pk=callback_data.pk)
    await part_sending(call.message, str(trigger_collection),
                       reply_markup=triggers_markups.switch_trigger_collection_status(trigger_collection))

    # await call.message.answer(
    #     f"{trigger_collection}",
    #     reply_markup=triggers_markups.switch_trigger_collection_status(trigger_collection),
    # )


async def switch_trigger_collection_status(
        call: types.CallbackQuery,
        state: FSMContext,
        user: User,
        callback_data: TriggerCollectionCallback):
    await state.clear()
    # trigger_coll = await TriggerCollection.get(id=callback_data.pk).prefetch_related("triggers")
    trigger_coll = await TriggerCollection.get_from_local_or_full(pk=callback_data.pk)
    await trigger_coll.switch_status(callback_data.payload)

    await call.message.edit_text(f"{trigger_coll}")
    await call.message.edit_reply_markup(triggers_markups.switch_trigger_collection_status(trigger_coll))


async def edit_trigger_collection(call: types.CallbackQuery,
                                  state: FSMContext,
                                  callback_data: TriggerCollectionCallback):
    await state.clear()
    # trigger_coll = await TriggerCollection.get(id=callback_data.pk).select_related("triggers")
    trigger_coll = await TriggerCollection.get_from_local_or_full(pk=callback_data.pk)
    triggers_str = ""
    for num, value in enumerate(trigger_coll.triggers, 1):
        p_num = md.hcode(f'# {num}')
        triggers_str += f"{p_num}\n{value}\n\n"

    await call.message.answer(
        "✏️ Для изменения введите выберите номер автоответа\n\n"
        f"{triggers_str}\n"
        f"{md.hbold('Текст ответа на все сообщения: ')}\n"
        f"{md.hcode(trigger_coll.answer_to_all_messages)}\n"
        ,
        reply_markup=triggers_markups.edit_trigger_collection(trigger_coll),
    )


async def edit_trigger_collection_answer(
        call: types.CallbackQuery,
        state: FSMContext,
        callback_data: TriggerCollectionCallback):
    await state.clear()
    await state.update_data(trigger_collection_answer_pk=callback_data.pk)
    await call.message.answer("Введите тест сообщения", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(EditTriggerCollectionAnswer.edit)


async def edit_trigger_collection_answer_done(
        message: types.Message,
        state: FSMContext):
    data = await state.get_data()
    # trigger_coll = await TriggerCollection.get(id=data["trigger_collection_answer_pk"]).prefetch_related("triggers")
    trigger_coll = await TriggerCollection.get_from_local_or_full(pk=data["trigger_collection_answer_pk"])
    await trigger_coll.set_answer(answer=message.text)
    await state.clear()
    await message.answer("Ответ успешно изменен ✅\n\n"
                         f"{trigger_coll}",
                         reply_markup=triggers_markups.switch_trigger_collection_status(trigger_coll))


def register_trigger_menu(dp: Router):

    dp.include_router(router)

    callback = router.callback_query.register
    message = router.message.register

    message(trigger_menu, text_startswith="⚙", state="*")

    callback(get_trigger_collections,
             TriggerCollectionCallback.filter(F.action == Action.all),
             state="*")

    callback(get_trigger_collection,
             TriggerCollectionCallback.filter(F.action == Action.view),
             state="*")

    callback(switch_trigger_collection_status,
             TriggerCollectionCallback.filter(F.action == TriggerCollectionAction.switch),
             state="*")

    callback(edit_trigger_collection,
             TriggerCollectionCallback.filter(F.action == Action.edit),
             state="*")

    callback(edit_trigger_collection_answer,
             TriggerCollectionCallback.filter(F.action == TriggerCollectionAction.edit_answer_to_all_messages),
             state="*")
    message(edit_trigger_collection_answer_done, state=EditTriggerCollectionAnswer.edit)
