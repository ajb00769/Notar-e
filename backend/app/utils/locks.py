import asyncio
from functools import wraps
from typing import Callable, Any, Dict

# In-memory lock registry, keyed by document ID
_locks: Dict[Any, asyncio.Lock] = {}


def document_lock(doc_id_arg: str = "doc_id"):
    """
    Decorator to ensure only one operation per document ID at a time.
    Usage:
        @document_lock(doc_id_arg="doc_id")
        async def sign_document(doc_id, ...):
            ...
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find doc_id from args/kwargs
            if doc_id_arg in kwargs:
                doc_id = kwargs[doc_id_arg]
            else:
                # Assume positional argument order
                import inspect

                sig = inspect.signature(func)
                params = list(sig.parameters.keys())
                doc_id_index = params.index(doc_id_arg)
                doc_id = args[doc_id_index]
            # Get or create lock for this doc_id
            lock = _locks.setdefault(doc_id, asyncio.Lock())
            async with lock:
                return await func(*args, **kwargs)

        return wrapper

    return decorator
