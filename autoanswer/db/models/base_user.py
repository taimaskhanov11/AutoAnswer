from tortoise import fields, Model


class TimestampMixin:
    created_at = fields.DatetimeField(null=True, auto_now_add=True)
    # registered_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(null=True, auto_now=True)


class AbstractUser(TimestampMixin, Model):
    id = fields.BigIntField(pk=True)
    username = fields.CharField(32, unique=True, index=True, null=True)
    first_name = fields.CharField(255, null=True)
    last_name = fields.CharField(255, null=True)
