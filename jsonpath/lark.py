# Standard Library
from typing import Any, Dict


try:
    from lark import Transformer, v_args, Lark
    from lark.exceptions import UnexpectedToken, VisitError

    Lark_StandAlone = Lark
    DATA: Dict[str, Any] = {}
except ImportError:
    import importlib.resources

    exec(importlib.resources.read_text(__name__.split(".")[0], "lark"))


__all__ = (
    "Transformer",
    "v_args",
    "Lark",
    "Lark_StandAlone",
    "DATA",
    "UnexpectedToken",
    "VisitError",
)
