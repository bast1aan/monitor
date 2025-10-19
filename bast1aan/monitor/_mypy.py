""" mypy plugin to add virtual __hash__ method to frozen dataclasses """
from typing import Callable, Optional

from mypy.plugin import Plugin, ClassDefContext
from mypy.plugins.common import add_method

def dataclass_transformer(ctx: ClassDefContext) -> None:
    add_method(
        ctx,
        '__hash__',
        args=[],
        return_type=ctx.api.named_type('builtins.int'),
    )

class MonitorPlugin(Plugin):
    def get_class_decorator_hook(self, fullname: str) -> Optional[Callable[[ClassDefContext], None]]:
        if fullname == 'bast1aan.monitor._util.frozen_dataclass':
            return dataclass_transformer
        return None

def plugin(version: str) -> type[Plugin]:
    return MonitorPlugin
