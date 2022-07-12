import argparse
import datetime
import os
from pathlib import Path
from typing import Optional

import yaml
from glQiwiApi import QiwiP2PClient
from loguru import logger
from pydantic import BaseModel, BaseSettings
from pydantic.env_settings import InitSettingsSource, EnvSettingsSource, SecretsSettingsSource

BASE_DIR = Path(__file__).parent.parent.parent
LOG_DIR = BASE_DIR / "logs"
MEDIA_DIR = BASE_DIR / 'media'
LOG_DIR.mkdir(exist_ok=True)
MEDIA_DIR.mkdir(exist_ok=True)

I18N_DOMAIN = "autoanswer"
LOCALES_DIR = BASE_DIR / "autoanswer/apps/bot/locales"
TZ = datetime.timezone(datetime.timedelta(hours=3))

config_file = "config.yaml" if not os.getenv("DEBUG") else "config_dev.yaml"


def load_yaml(file) -> dict:
    with open(Path(BASE_DIR, file), "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def yaml_config_settings_source(settings: BaseSettings) -> dict:
    return load_yaml(settings.__config__.config_file)


def parse_config():
    parser = argparse.ArgumentParser(description="config_file")
    parser.add_argument("-f", type=str)
    args = parser.parse_args()
    if args.f:
        logger.success(f"Выгрузка конфига из файла {args.f}")
    return args.f


class Bot(BaseModel):
    id: int | None
    token: str
    admins: Optional[list[int]]


class Database(BaseModel):
    user: str
    password: str
    database: str
    host: str
    port: int

    @property
    def postgres_url(self):
        return f"postgres://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class CryptoCloud(BaseModel):
    shop_id: str
    api_key: str
    create_url: str
    status_url: str


class Qiwi(BaseModel):
    token: str


class Payment(BaseModel):
    cryptocloud: CryptoCloud | None
    qiwi: Qiwi | None


class Config(BaseSettings):
    bot: Bot
    db: Database
    payment: Payment | None

    class Config:
        env_file = r"..\..\.env"
        env_file_encoding = "utf-8"
        config_file = config_file
        case_sensitive = True

        @classmethod
        def customise_sources(cls,
                              init_settings: InitSettingsSource,
                              env_settings: EnvSettingsSource,
                              file_secret_settings: SecretsSettingsSource):
            return init_settings, env_settings, yaml_config_settings_source, file_secret_settings


config = Config()
QIWI_CLIENT = QiwiP2PClient(secret_p2p=config.payment.qiwi.token)
