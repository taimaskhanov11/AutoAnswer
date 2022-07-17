from aiogram import Router, types, F
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.dispatcher.fsm.state import StatesGroup, State
from aiogram.utils import markdown as md

from autoanswer.apps.bot.callback_data.base_callback import TriggerCollectionCallback, TriggerCollectionAction, \
    Action
from autoanswer.apps.bot.markups.common import triggers_markups
from autoanswer.apps.bot.utils import part_sending
from autoanswer.apps.bot.utils.message import check_for_file
from autoanswer.db.models import User
from autoanswer.db.models.trigger import TriggerCollection

router = Router()

edit_text_answer = ("Отправьте ответ!\n\n"
                    "Ответом может быть текст, фото, видео, голосовое сообщение или любой другой файл.\n"
                    "Также вы можете прикрепить файл к тексту.\n\n"
                    "Чтобы стилизовать текст используйте следующие атрибуты:\n\n"
                    f"<жир>текст</жир> - {md.bold('жирный')}\n"
                    f"<кур>текст</кур> - {md.italic('курсив')}\n"
                    # f"<под>текст</под> - {md.underline('подчеркнутый')}\n"
                    f"<пер>текст</пер> - {md.strikethrough('перечеркнутый')}\n"
                    f"<код>текст</код> - {md.code('код')}\n"
                    f"<скр>текст</скр> - Скрытый текст\n\n"
                    "Пример:\n"
                    f"Так делается {md.bold('<жир>жирный текст</жир>')}\n\n")


class EditTriggerCollectionAnswer(StatesGroup):
    edit = State()


class EditTriggerCollectionDelay(StatesGroup):
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
        await call.message.answer("Для начала подключите хотя бы 1 аккаунт.")
        return
    await call.message.answer("Выберите аккаунт:",
                              reply_markup=triggers_markups.get_trigger_collections(triggers_coll))


async def get_trigger_collection(
        call: types.CallbackQuery,
        callback_data: TriggerCollectionCallback,
        state: FSMContext,
        user: User):
    await state.clear()
    trigger_collection = await TriggerCollection.get_local_or_full(pk=callback_data.pk)
    await part_sending(call.message, trigger_collection.prettify,
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
    trigger_coll = await TriggerCollection.get_local_or_full(pk=callback_data.pk)
    await trigger_coll.switch_status(callback_data.payload)
    # await call.message.edit_text(trigger_coll.prettify)
    await call.message.edit_reply_markup(triggers_markups.switch_trigger_collection_status(trigger_coll))


async def edit_trigger_collection(call: types.CallbackQuery,
                                  state: FSMContext,
                                  callback_data: TriggerCollectionCallback):
    await state.clear()
    trigger_coll = await TriggerCollection.get_local_or_full(pk=callback_data.pk)
    await call.message.edit_reply_markup(triggers_markups.edit_trigger_collection(trigger_coll))
    # await call.message.answer(
    #     "✏️ Для изменения введите выберите номер автоответа\n\n"
    #     f"{trigger_coll.triggers_prettify}\n"
    #     f"{md.bold('Текст ответа на все сообщения: ')}\n"
    #     f"{md.code(trigger_coll.answer_to_all_messages)}\n"
    #     ,
    #     reply_markup=triggers_markups.edit_trigger_collection(trigger_coll),
    # )


async def edit_trigger_collection_answer(
        call: types.CallbackQuery,
        state: FSMContext,
        callback_data: TriggerCollectionCallback):
    await state.clear()
    await state.update_data(trigger_collection_answer_pk=callback_data.pk)
    await call.message.answer(edit_text_answer, reply_markup=types.ReplyKeyboardRemove())

    await state.set_state(EditTriggerCollectionAnswer.edit)


async def edit_trigger_collection_answer_done(
        message: types.Message,
        state: FSMContext):
    answer, file_name = await check_for_file(message)
    data = await state.get_data()
    pk = data.get('trigger_collection_answer_pk')
    trigger_coll = await TriggerCollection.get_local_or_full(pk)

    trigger_coll.answer_to_all_messages = answer
    trigger_coll.file_name = file_name
    await trigger_coll.save(update_fields=['answer_to_all_messages', 'file_name'])

    await state.clear()
    await message.answer("Ответ успешно изменен ✅\n\n"
                         f"{trigger_coll.prettify}",
                         reply_markup=triggers_markups.switch_trigger_collection_status(trigger_coll))


async def edit_trigger_collection_delay(
        call: types.CallbackQuery,
        state: FSMContext,
        callback_data: TriggerCollectionCallback):
    await state.clear()
    await state.update_data(trigger_collection_answer_pk=callback_data.pk)
    await call.message.answer("Отправьте задержку в секундах.\n",
                              reply_markup=types.ReplyKeyboardRemove())

    await state.set_state(EditTriggerCollectionDelay.edit)


async def edit_trigger_collection_delay_done(
        message: types.Message,
        state: FSMContext, ):
    data = await state.get_data()
    pk = data.get('trigger_collection_answer_pk')
    trigger_coll = await TriggerCollection.get_local_or_full(pk)
    await trigger_coll.set_delay_before_answer(int(message.text))
    await state.clear()
    await message.answer("Задержка успешно изменена ✅\n\n"
                         f"{trigger_coll.prettify}",
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

    callback(edit_trigger_collection_delay,
             TriggerCollectionCallback.filter(F.action == TriggerCollectionAction.edit_delay_before_answer),
             state="*")
    message(edit_trigger_collection_delay_done, state=EditTriggerCollectionDelay.edit)
