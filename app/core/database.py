import psycopg2
from psycopg2.extensions import connection

from app.core.config import settings

# defines a function which allows for functions to get a db connection
def get_connection() -> connection:
    return psycopg2.connect(settings.database_url)


def check_db_connection() -> bool:
    try:
        with get_connection() as db_connection:
            with db_connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return cursor.fetchone() == (1,)
    except Exception:
        return False
