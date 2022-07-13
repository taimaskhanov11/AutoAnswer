import re

from aiogram import types
from aiogram.utils import markdown as md

from autoanswer.config.config import MEDIA_DIR
from autoanswer.loader import bot

bold_pattern = re.compile(r"<жир>(.*)</жир>")
italic_pattern = re.compile(r"<кур>(.*)</кур>")
code_pattern = re.compile(r"<код>(.*)</код>")
pod_pattern = re.compile(r"<под>(.*)</под>")
per_pattern = re.compile(r"<пер>(.*)</пер>")
spoiler_pattern = re.compile(r"<спо>(.*)</спо>")


def strikethrough(text: str):
    return f"~~{text}~~"


def bold(text: str):
    return f"**{text}**"


def italic(text: str):
    return f"__{text}__"


def spoiler(text: str):
    return f"||{text}||"


md.bold = bold
md.italic = italic
md.strikethrough = strikethrough
md.spoiler = spoiler


def styled_message(text: str | None) -> str:
    """
    Подготовка и стилизация текста для отправки контроллером
    <жир> текст </жир> - жирный
    <кур> текст </кур> - курсив
    <под> текст </под> - подчеркнутый
    <пер> текст </пер> - перечеркнутый
    <код> текст </код> - код

    :param text:
    :return:
    """
    text = text or ''
    # todo 7/13/2022 2:02 PM taima:
    res = re.sub(spoiler_pattern, lambda x: md.bold(x.group(1)),
                 re.sub(bold_pattern, lambda x: md.bold(x.group(1)),
                        re.sub(italic_pattern, lambda x: md.italic(x.group(1)),
                               re.sub(code_pattern, lambda x: md.code(x.group(1)),
                                      re.sub(pod_pattern, lambda x: md.underline(x.group(1)),
                                             re.sub(per_pattern, lambda x: md.strikethrough(x.group(1)), text))))))
    return res


async def check_for_file(message: types.Message):
    file = None
    file_name = None
    default_file_name = "some_file.png"
    answer = message.text
    if message.photo:
        file = message.photo[-1]
    elif message.audio:
        file = message.audio
    elif message.document:
        file = message.document
    elif message.video:
        file = message.video
    elif message.voice:
        file = message.voice
        default_file_name = "audio.ogg"

    if file:
        answer = message.caption
        file_id = getattr(file, "file_id")
        file_name = getattr(file, "file_name", default_file_name)
        await bot.download(file_id, MEDIA_DIR / file_name)
    return answer, file_name
