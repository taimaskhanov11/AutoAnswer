import datetime
import typing

from aiogram.client.session import aiohttp
from loguru import logger
from tortoise import models, fields
from tortoise.transactions import atomic

from autoanswer.config.config import TZ, config
from .subscription import SubscriptionTemplate
from ...apps.bot.utils.yookassa import YooPayment

if typing.TYPE_CHECKING:
    from .user import User

headers = {"Authorization": f"Token {config.payment.cryptocloud.api_key}"}


class InvoiceAbstract(models.Model):
    """Абстрактный класс для создания счета"""
    subscription_template: SubscriptionTemplate = fields.ForeignKeyField("models.SubscriptionTemplate",
                                                                         on_delete=fields.CASCADE)
    user: "User" = fields.ForeignKeyField("models.User", on_delete=fields.CASCADE)
    currency = fields.CharField(5, default="RUB", description="RUB")
    amount = fields.DecimalField(17, 7)
    invoice_id = fields.CharField(50, index=True)
    created_at = fields.DatetimeField(default=datetime.datetime.now(TZ))
    expire_at = fields.DatetimeField(default=datetime.datetime.now(TZ) + datetime.timedelta(minutes=30))
    email = fields.CharField(20, null=True)
    pay_url = fields.CharField(255)
    is_paid = fields.BooleanField(default=False)

    class Meta:
        abstract = True

    # todo 6/1/2022 11:01 AM taima: успешная оплата
    # todo 6/1/2022 9:30 PM taima: проверка на цену и остальная логика доработать
    @atomic()
    async def successfully_paid(self):
        # todo 7/10/2022 10:45 PM taima: проверка на цену и остальная логика доработать
        await self.fetch_related("user__subscription", "subscription_template")
        self.user.subscription.title = self.subscription_template.title
        self.user.subscription.duration += self.subscription_template.duration
        self.user.subscription.price = self.subscription_template.price
        self.is_paid = True
        await self.user.subscription.save()
        await self.save(update_fields=["is_paid"])

    async def check_payment(self) -> bool:
        pass

    @classmethod
    async def create_invoice(cls, **kwargs):
        pass


class InvoiceCrypto(InvoiceAbstract):
    """
    for create:
        amount
        shop_id
        order_id
        email
        currency

    result:
        {'status': 'success',
        'pay_url': 'https://cryptocloud.plus/pay/4N8RWT',
        'currency': 'BTC',
        'invoice_id': '4N8RWT',
        'amount': 3e-06,
        'amount_usd': 0.1170788818966779}
    check result:
        {'status': 'success', 'status_invoice': 'created'}
        {'status': 'success', 'status_invoice': 'paid'}
    checked time:
        7-10 m
    """
    user: "User" = fields.ForeignKeyField("models.User", on_delete=fields.CASCADE, related_name="invoice_cryptos")
    shop_id = fields.CharField(50, default=config.payment.cryptocloud.shop_id)
    currency = fields.CharField(5, default="RUB", description="USD, RUB, EUR, GBP")
    order_id = fields.CharField(50, null=True, description="Custom product ID")

    async def check_payment(self) -> bool:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(config.payment.cryptocloud.status_url,
                                   params={"uuid": self.invoice_id}) as res:
                result = await res.json()
                logger.trace(result)
                if result["status_invoice"] == "paid":
                    return True
        return False

    @classmethod
    async def create_invoice(cls,
                             user: "User",
                             subscription_template: SubscriptionTemplate,
                             amount: int | float | str,
                             comment: str = None,
                             currency="RUB",
                             email: str = None,
                             order_id: str = None,
                             shop_id: str = config.payment.cryptocloud.shop_id,
                             lifetime: int = 60) -> 'InvoiceCrypto':
        cryptocloud = config.payment.cryptocloud
        async with aiohttp.ClientSession(headers=headers) as session:
            data = dict(
                amount=amount,
                currency=currency,
                email=email,
                order_id=order_id,
                expire_at=datetime.datetime.now(TZ) + datetime.timedelta(minutes=lifetime),
                shop_id=shop_id
            )
            # pprint(data)
            async with session.post(cryptocloud.create_url, data=data) as res:
                # pprint(await res.json())
                print(await res.text())
                result_data = await res.json()
                del result_data["amount"]
                del result_data["currency"]
                created_invoice = await cls.create(**result_data,
                                                   **data,
                                                   user=user,
                                                   subscription_template=subscription_template, )
                logger.debug(
                    f"InvoiceCrypto created [{user.user_id}][{created_invoice.invoice_id}] {created_invoice.pay_url}")
                return created_invoice


class InvoiceQiwi(InvoiceAbstract):
    """{'amount': {'currency': 'RUB', 'value': 5.0},
         'created_at': datetime.datetime(2022, 5, 22, 21, 24, 17, 186000, tzinfo=datetime.timezone(datetime.timedelta(seconds=10800))),
         'custom_fields': {'pay_sources_filter': 'qw', 'theme_code': 'Yvan-YKaSh'},
         'customer': None,
         'expire_at': datetime.datetime(2022, 5, 22, 21, 54, 7, tzinfo=datetime.timezone(datetime.timedelta(seconds=10800))),
         'id': '397a2a00-19ae-40f6-9ea1-c4e3bccb315f',
         'pay_url': 'https://oplata.qiwi.com/form/?invoice_uid=f8b7366e-3b5d-44e0-9356-50c56eab18d6',
         'recipientPhoneNumber': '79898600122',
         'site_id': '7l0erf-00',
         'status': {'changed_datetime': datetime.datetime(2022, 5, 22, 21, 24, 17, 186000, tzinfo=datetime.timezone(datetime.timedelta(seconds=10800))),
                    'value': 'WAITING'}}
    """
    user: "User" = fields.ForeignKeyField("models.User", on_delete=fields.CASCADE, related_name="invoice_qiwis")
    comment = fields.CharField(255, null=True)

    async def check_payment(self) -> bool:
        status = await config.payment.qiwi.get_bill_status(self.invoice_id)
        if status == "PAID":
            return True
        return False

    # todo 5/22/2022 3:46 PM taima: сделать для других валют
    @classmethod
    async def create_invoice(cls,
                             user: "User",
                             subscription_template: SubscriptionTemplate,
                             amount: int | float | str,
                             comment: str = None,
                             email: str = None,
                             lifetime: int = 30, ) -> "InvoiceQiwi":
        async with config.payment.qiwi:
            bill = await config.payment.qiwi.create_p2p_bill(
                amount=amount,
                comment=comment,
                expire_at=datetime.datetime.now(TZ) + datetime.timedelta(minutes=lifetime),
            )
            logger.debug(f"InvoiceQiwi created [{user}][{bill.id}] {bill.pay_url}")
            return await cls.create(**bill.dict(exclude={"id", "amount"}),
                                    user=user,
                                    subscription_template=subscription_template,
                                    amount=bill.amount.value,
                                    invoice_id=bill.id,
                                    email=email, )


class InvoiceYooKassa(InvoiceAbstract):
    """
        {'id': '2a60ca77-000f-5000-a000-16cf4119f15e', 'status': 'pending', 'amount': {'value': '1.00',
                                                                                       'currency': 'RUB'},
        'description': 'Текстовый', 'recipient': {'account_id': '878719', 'gateway_id': '1934486'},
        'created_at': '2022-07-13T12:12:39.501Z',
        'confirmation': {'type': 'redirect',
                         'confirmation_url': 'https://yoomoney.ru/checkout/payments/v2/contract?orderId=2a60ca77-000f-5000-a000-16cf4119f15e'},
        'test': False, 'paid': False, 'refundable': False, 'metadata': {}}
    """
    user: "User" = fields.ForeignKeyField("models.User", on_delete=fields.CASCADE, related_name="invoice_yookassas")
    comment = fields.CharField(255, null=True)

    async def check_payment(self) -> bool:
        yoo_payment = await YooPayment.get(self.invoice_id)
        if yoo_payment.paid:
            return True
        return False

    # todo 5/22/2022 3:46 PM taima: сделать для других валют
    @classmethod
    async def create_invoice(cls,
                             user: "User",
                             subscription_template: SubscriptionTemplate,
                             amount: int | float | str,
                             comment: str = None,
                             email: str = None,
                             lifetime: int = 30, ) -> "InvoiceYooKassa":
        yoo_payment = await YooPayment.create_payment(
            description=comment,
            amount=amount,
        )
        logger.debug(f"InvoiceYooKassa created [{user}][{yoo_payment.id}] {yoo_payment.confirmation.confirmation_url}")
        return await cls.create(user=user,
                                subscription_template=subscription_template,
                                amount=yoo_payment.amount.value,
                                comment=comment,
                                invoice_id=yoo_payment.id,
                                pay_url=yoo_payment.confirmation.confirmation_url,
                                email=email)
