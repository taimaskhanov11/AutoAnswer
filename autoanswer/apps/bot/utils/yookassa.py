import datetime
import uuid

from aiogram.client.session import aiohttp
from pydantic import BaseModel
from requests.auth import _basic_auth_str

from autoanswer.config.config import config

shop_id = config.payment.yookassa.shop_id
yookassa_api_key = config.payment.yookassa.api_key
link = config.payment.yookassa.create_url
headers = {"Authorization": _basic_auth_str(shop_id,
                                            yookassa_api_key),
           "Content-type": "application/json"}
tz = datetime.timezone(datetime.timedelta(hours=0))


class Confirmation(BaseModel):
    confirmation_url: str
    type: str


class Amount(BaseModel):
    currency: str
    value: float


class YooPayment(BaseModel):
    id: uuid.UUID
    amount: Amount
    description: str
    created_at: datetime.datetime
    confirmation: Confirmation | None
    paid: bool
    status: str

    @classmethod
    async def create_payment(
            cls,
            description: str,
            amount: float,
            return_url: str = f"https://t.me/{config.bot.username}"
    ) -> "YooPayment":
        data = {
            "amount": {"value": amount, "currency": "RUB"},
            "confirmation": {"type": "redirect", "return_url": return_url},
            "capture": True,
            "description": description,
            # "expires_at": str(datetime.datetime.now(tz) + datetime.timedelta(minutes=15))
        }
        async with aiohttp.ClientSession(headers=headers | {"Idempotence-Key": str(uuid.uuid4())}) as session:
            async with session.post(link, json=data) as response:
                return cls.parse_obj(await response.json())

    @classmethod
    async def get(cls, bill_id: uuid.UUID) -> "YooPayment":
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(f"{link}/{bill_id}") as response:
                res = await response.json()
                return cls.parse_obj(res)

    @classmethod
    async def cancel(cls, bill_id: uuid.UUID) -> "YooPayment":
        async with aiohttp.ClientSession(headers=headers | {"Idempotence-Key": str(uuid.uuid4())}) as session:
            async with session.post(f"{link}/{bill_id}/cancel", json={}) as response:
                res = await response.json()
                return cls.parse_obj(res)
