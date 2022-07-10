import collections
import typing
from asyncio import Queue

if typing.TYPE_CHECKING:
    from autoanswer.apps.bot.utils import MailSender
    from autoanswer.apps.controller.controller import Controller

SUBSCRIPTION_CHANNELS: list[tuple[str, str]] = []
MAIL_SENDER: typing.Optional["MailSender"] = None
BOT_RUNNING: bool = True

controller_codes_queue: dict[int, Queue] = {}
controllers: dict[int, dict[int, 'Controller']] = collections.defaultdict(dict)
