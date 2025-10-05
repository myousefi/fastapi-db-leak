from __future__ import annotations

import logging
import time

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.core.db import engine
from app.models import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 60
SLEEP_SECONDS = 1


def wait_for_database() -> None:
    attempt = 0
    while attempt < MAX_ATTEMPTS:
        attempt += 1
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            logger.info("Database connection established")
            return
        except OperationalError:
            logger.info("Database not ready, retrying (%s/%s)", attempt, MAX_ATTEMPTS)
            time.sleep(SLEEP_SECONDS)
    raise RuntimeError("Database never became available")


def ensure_schema() -> None:
    Base.metadata.create_all(bind=engine)


def main() -> None:
    logger.info("Waiting for database")
    wait_for_database()
    logger.info("Creating tables if needed")
    ensure_schema()
    logger.info("Startup checks completed")


if __name__ == "__main__":
    main()
