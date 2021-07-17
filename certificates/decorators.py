from functools import wraps
from logging import Logger
from typing import List


def exception_logging(logger: Logger, exceptions: List[Exception] = []):
    """Функция декоратор для логгирования исключений."""

    def wrapper(function):

        @wraps(function)
        def throw(*args, **kwargs):
            """Декоратор для обработки исключений."""
            try:
                return function(*args, **kwargs)
            except tuple(exceptions) as e:
                logger.exception(e)
                raise e
            except Exception as e:
                logger.exception(e)
                raise e

        return throw

    return wrapper
