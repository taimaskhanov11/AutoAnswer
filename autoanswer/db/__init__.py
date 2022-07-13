import asyncpg
from loguru import logger
from tortoise import Tortoise

__all__ = (
    "MODELS_DIR",
    "init_db",
    "models",
    "utils"
)
from autoanswer.config.config import Database, config

MODELS_DIR = "autoanswer.db.models"


async def init_db(db: Database = config.db):
    logger.debug(f"Initializing Database {db.database}[{db.host}]...")
    print(MODELS_DIR)
    data = {
        "db_url": db.postgres_url,
        "modules": {"models": [MODELS_DIR]},
    }
    try:
        await Tortoise.init(**data)
        await Tortoise.generate_schemas()
    except asyncpg.exceptions.ConnectionDoesNotExistError as e:
        logger.warning(e)
        logger.info("Creating a new database ...")
        await Tortoise.init(**data, _create_db=True)
        await Tortoise.generate_schemas()
        logger.success(f"New database {db.database} created")

    logger.debug(f"Database {db.database}[{db.host}] initialized")
# Tortoise.init_models(['autoanswer.db.models'], 'models')
