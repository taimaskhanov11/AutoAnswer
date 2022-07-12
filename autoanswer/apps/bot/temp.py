import typing
from asyncio import Queue

if typing.TYPE_CHECKING:
    from autoanswer.apps.bot.utils import MailSender
    from autoanswer.apps.controller.controller import Controller
# Bot settings
SUBSCRIPTION_CHANNELS: list[tuple[str, str]] = []
MAIL_SENDER: typing.Optional["MailSender"] = None
BOT_RUNNING: bool = True

# Account settings
controller_codes_queue: dict[int, Queue] = {}
controllers: dict[int, 'Controller'] = {}
