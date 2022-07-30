import asyncio

from aiogram import Bot, F
from aiogram.types import BotCommand

from autoanswer.apps.bot.handlers.admin import register_admin_handlers
from autoanswer.apps.bot.handlers.common import register_common_handlers
from autoanswer.apps.bot.handlers.errors.errors_handlers import register_error
from autoanswer.apps.bot.middleware.bot_middleware import BotMiddleware
from autoanswer.apps.bot.utils import start_up_message
from autoanswer.apps.bot.utils.purchase import checking_purchases
from autoanswer.apps.controller.controller import init_controllers
from autoanswer.config.config import config, load_yaml
from autoanswer.config.logg_settings_new import init_logging
from autoanswer.db import init_db
from autoanswer.db.models import Subscription, SubscriptionTemplate, AbstractUser
from autoanswer.db.utils.backup import making_backup
from autoanswer.loader import bot, dp, scheduler


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Главное меню"),
        BotCommand(command="/admin", description="Админ меню"),
    ]
    await bot.set_my_commands(commands)


async def start():
    # Настройка логирования
    init_logging(
        level="INFO",
        steaming=True,
        write=True,
    )

    # Инициализация бд
    await init_db()

    dp.startup.register(start_up_message)
    # dp.shutdown.register(on_shutdown)

    # Установка команд бота
    bot_info = await bot.get_me()
    config.bot.id = bot_info.id
    config.bot.username = bot_info.username

    await set_commands(bot)
    dp.message.filter(F.chat.type == "private")


    # Меню админа
    register_admin_handlers(dp)

    # Регистрация хэндлеров
    register_common_handlers(dp)

    # Регистрация хэндлеров ошибок
    register_error(dp)

    # Регистрация middleware
    middleware = BotMiddleware()
    dp.message.outer_middleware(middleware)
    dp.callback_query.outer_middleware(middleware)

    # Регистрация фильтров
    # pass
    # Инициализация контроллеров
    await init_controllers()

    # Обновление подписок
    await SubscriptionTemplate.update_subscriptions(load_yaml("subscriptions.yaml"))

    scheduler.add_job(Subscription.decreased_duration, "cron", hour=0, minute=0)
    scheduler.add_job(making_backup, "interval", hours=1)
    scheduler.add_job(
        checking_purchases,
        "interval",
        # minutes=1,
        seconds=60,
    )
    scheduler.start()
    await dp.start_polling(bot, skip_updates=True)


def main():
    asyncio.run(start())


if __name__ == "__main__":
    main()
