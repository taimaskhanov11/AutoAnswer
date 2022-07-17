from aiogram import Router, types, F
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.fsm.state import StatesGroup, State

from autoanswer.apps.bot.callback_data.base_callback import TriggerCallback, Action, TriggerAction
from autoanswer.apps.bot.handlers.common.sub_functional.trigger.trigger_menu import edit_text_answer
from autoanswer.apps.bot.markups.common import triggers_markups
from autoanswer.apps.bot.utils.message import check_for_file
from autoanswer.db.models.trigger import Trigger, TriggerCollection

router = Router()


class CreateTrigger(StatesGroup):
    phrases = State()
    answer = State()


class EditTriggerPhrases(StatesGroup):
    phrases = State()
    answer = State()


async def get_trigger(call: types.CallbackQuery,
                      state: FSMContext,
                      callback_data: TriggerCallback):
    await state.clear()
    trigger = await Trigger.get_full(pk=callback_data.pk)
    await call.message.answer(
        trigger.prettify,
        reply_markup=triggers_markups.get_trigger(trigger),
    )


async def delete_trigger(call: types.CallbackQuery,
                         callback_data: TriggerCallback):
    trigger = await Trigger.get_local_or_full(pk=callback_data.pk)
    await trigger.delete()
    await TriggerCollection.refresh_local_to_new(pk=trigger.trigger_collection_id)
    await call.message.answer("Триггер удален ✅")


async def create_trigger(call: types.CallbackQuery,
                         callback_data: TriggerCallback,
                         state: FSMContext):
    await state.clear()
    await state.update_data(trigger_coll_pk=callback_data.pk)
    await call.message.answer("Введите фразы для ответа через запятую",
                              reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(CreateTrigger.phrases)


async def create_trigger_phrases(message: types.Message,
                                 state: FSMContext):
    phrases = Trigger.fix_phrases(message.text)
    await state.update_data(phrases=phrases)
    await message.answer(edit_text_answer, reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(CreateTrigger.answer)


async def create_trigger_answer(message: types.Message,
                                state: FSMContext):
    # todo 7/12/2022 7:01 PM taima: Проверить на размер файла
    try:
        answer, file_name = await check_for_file(message)

        data = await state.get_data()
        phrases = data["phrases"]
        trigger_coll_pk = data["trigger_coll_pk"]

        trigger_coll = await TriggerCollection.get_local_or_full(pk=trigger_coll_pk)
        trigger = await Trigger.create(phrases=phrases,
                                       answer=answer,
                                       file_name=file_name,
                                       trigger_collection=trigger_coll)

        await TriggerCollection.refresh_local_to_new(trigger_coll.pk)
        await message.answer(f"Триггер создан ✅\n\n{trigger.prettify}", "markdown",
                             reply_markup=triggers_markups.get_trigger(trigger), )
        await state.clear()
    except Exception as e:
        print(e)


async def edit_trigger_phrases(call: types.CallbackQuery,
                               state: FSMContext,
                               callback_data: TriggerCallback):
    await state.clear()
    await state.update_data(trigger_pk=callback_data.pk)
    await call.message.answer("Введите фразы для ответа через запятую",
                              reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(EditTriggerPhrases.phrases)


async def edit_trigger_phrases_done(message: types.Message,
                                    state: FSMContext):
    data = await state.get_data()
    pk = data["trigger_pk"]
    trigger = await Trigger.get_local_or_full(pk=pk)
    await trigger.set_phrases(message.text)
    await message.answer(
        trigger.prettify,
        reply_markup=triggers_markups.get_trigger(trigger),
    )
    await state.clear()
    await message.answer("Фразы обновлены ✅")


async def edit_trigger_answer(call: types.CallbackQuery,
                              state: FSMContext,
                              callback_data: TriggerCallback):
    await state.clear()
    await state.update_data(trigger_pk=callback_data.pk)
    await call.message.answer(edit_text_answer,
                              reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(EditTriggerPhrases.answer)


async def edit_trigger_answer_done(message: types.Message,
                                   state: FSMContext):
    answer, file_name = await check_for_file(message)
    data = await state.get_data()
    pk = data["trigger_pk"]
    trigger = await Trigger.get_local_or_full(pk=pk)
    await trigger.set_answer(answer)
    if file_name:
        await trigger.set_file_name(file_name)

    await message.answer(
        trigger.prettify,
        reply_markup=triggers_markups.get_trigger(trigger),
    )

    await state.clear()
    await message.answer("Ответ обновлен ✅")


def register_trigger_solo(dp: Router):
    dp.include_router(router)

    callback = router.callback_query.register
    message = router.message.register

    callback(get_trigger, TriggerCallback.filter(F.action == Action.view), state="*")
    callback(delete_trigger, TriggerCallback.filter(F.action == Action.delete), state="*")

    callback(edit_trigger_phrases, TriggerCallback.filter(F.action == TriggerAction.edit_phrases), state="*")
    message(edit_trigger_phrases_done, state=EditTriggerPhrases.phrases)

    callback(edit_trigger_answer, TriggerCallback.filter(F.action == TriggerAction.edit_answer), state="*")
    message(edit_trigger_answer_done, state=EditTriggerPhrases.answer)

    callback(create_trigger, TriggerCallback.filter(F.action == Action.create), state="*")
    message(create_trigger_phrases, state=CreateTrigger.phrases)
    message(create_trigger_answer, state=CreateTrigger.answer)
