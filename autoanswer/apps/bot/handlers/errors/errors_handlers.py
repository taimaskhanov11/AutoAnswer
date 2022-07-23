import sys

from aiogram import Dispatcher, Router
from aiogram.exceptions import TelegramBadRequest
from loguru import logger

router = Router()


async def error_handler(update, exception: TelegramBadRequest):
    if isinstance(exception, TelegramBadRequest):
        _type, _, tb = sys.exc_info()
        logger.opt(exception=(_type, None, tb)).error("An error occurred")
    logger.exception(exception)
    return True


# @router.errors()
# class MyHandler(ErrorHandler):
#     async def handle(self) -> Any:
#         print(self.exception_name)
#         print(self.exception_message)
#         logger.exception(
#             "Cause unexpected exception %s: %s",
#             self.exception_name,
#             str(self.exception_message)
#         )


def register_error(dp: Dispatcher):
    dp.include_router(router)
    router.errors.register(error_handler)
