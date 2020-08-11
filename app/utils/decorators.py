from functools import wraps
from typing import Callable

from django.db import connections as db_connections


def coroutine(gen: Callable) -> Callable:
    @wraps(gen)
    def prime_coro(*args, **kwargs):
        g = gen(*args, **kwargs)
        next(g)
        return g
    
    return prime_coro


def close_db_connections_when_finished(fn: Callable) -> Callable:
    """
    Primary usage: clean up "dangling" db connections that were opened by django
    for every manually spawned thread
    which is not a part of the request-response cycle.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        finally:
            db_connections.close_all()
    
    return wrapper
