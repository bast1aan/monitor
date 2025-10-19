""" Fail safe typing_extensions that does not exist on runtime environments """
from typing import TYPE_CHECKING

__all__ = ['dataclass_transform']

if TYPE_CHECKING:
    from typing_extensions import dataclass_transform
else:
    def dataclass_transform(*args, **kwargs):
        def wrapper(f):
            return f
        return wrapper
