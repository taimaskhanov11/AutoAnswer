import typing

import aiohttp
from loguru import logger

if typing.TYPE_CHECKING:
    from autoanswer.config.config import CryptoCloud


def create_invoice_request(crypto: CryptoCloud, data: typing.Any):
    async with aiohttp.ClientSession(headers=crypto.headers) as session:
        async with session.post(crypto.create_url, data=data) as res:
            result_data = await res.json()
            return result_data


def check_invoice_request(crypto: CryptoCloud, invoice_id: str):
    async with aiohttp.ClientSession(headers=crypto.headers) as session:
        async with session.get(crypto.status_url, params={"uuid": invoice_id}) as res:
            result = await res.json()
            logger.trace(result)
            return result["status_invoice"] == "paid"
