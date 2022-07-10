import datetime

from loguru import logger

from autoanswer.config.config import TZ
from autoanswer.db.models.invoice import InvoiceCrypto, InvoiceQiwi
from autoanswer.loader import bot, _


async def checking_purchases():
    logger.trace("Checking purchases")
    for cls in [InvoiceCrypto, InvoiceQiwi]:
        logger.trace(f"Check cls {cls.__name__}")
        invoices: list[InvoiceCrypto | InvoiceQiwi] = await cls.filter(expire_at__gte=datetime.datetime.now(TZ),
                                                                       is_paid=False)
        for invoice in invoices:
            logger.trace(f"Check invoice {invoice.invoice_id}[{invoice.amount}]")
            try:
                if await invoice.check_payment():
                    await invoice.successfully_paid()
                    logger.success(
                        f"The invoice [{cls.__name__}] [{invoice.user}]{invoice.amount} {invoice.currency} "
                        f"has been successfully paid")
                    await bot.send_message(invoice.user.user_id,
                                           _("✅ Подписка {} успешно оплачена").format(invoice.subscription_template))
            except Exception as e:
                raise e
                logger.warning(e)
