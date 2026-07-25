from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .session import engine


def is_database_ready() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return False

    return True
