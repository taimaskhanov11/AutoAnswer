from tortoise import fields, models


class Log(models.Model):
    level = fields.CharField(max_length=10)
    message = fields.TextField()
    date = fields.DatetimeField(auto_now_add=True)

    def __str__(self):
        return self.level
