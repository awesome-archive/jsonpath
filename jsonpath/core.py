# Standard Library
import weakref

from abc import abstractmethod
from contextvars import ContextVar
from typing import Any, Dict, List, Optional, Tuple
from weakref import ReferenceType


var_root = ContextVar("root")
var_self = ContextVar("self")
var_finding = ContextVar("finding", default=False)


class FindError(Exception):
    pass


def chain(pre, current):
    if pre.ref_begin is None:
        pre.ref_begin = weakref.ref(pre)

    current.ref_begin = pre.ref_begin
    current.left = pre
    pre.ref_right = weakref.ref(current)


def dfs_find(expr, elements, rv):
    if expr is None:
        rv.extend(elements)
    else:
        if isinstance(elements, dict):
            elements = elements.values()

        for element in elements:
            try:
                dfs_find(
                    expr.ref_right() if expr.ref_right else None,
                    expr.find(element),
                    rv,
                )
            except FindError:
                pass


class ExprMeta(type):
    _exprs = {}

    def __init__(cls, name: str, bases: Tuple[type], attr_dict: Dict[str, Any]):
        super().__init__(name, bases, attr_dict)
        cls._exprs[name] = cls

        actual_find = cls.find

        def begin_to_find(self, element):
            if var_finding.get():
                try:
                    return actual_find(self, element)
                except FindError:
                    if self.ref_begin is None:
                        raise

                    return []

            if self.ref_begin is None:
                expr = self
            else:
                expr = self.ref_begin()

            rv = []
            token_root = None
            token_self = None

            try:
                var_root.get()
                token_self = var_self.set(element)
            except LookupError:
                token_root = var_root.set(element)

            token_finding = var_finding.set(True)
            try:
                dfs_find(expr, [element], rv)
                return rv
            finally:
                var_finding.reset(token_finding)
                if token_root:
                    var_root.reset(token_root)
                if token_self:
                    var_self.reset(token_self)

        cls.find = begin_to_find


class Expr(metaclass=ExprMeta):
    def __init__(self) -> None:
        self.left: Optional[Expr] = None
        self.ref_right: Optional[ReferenceType[Expr]] = None
        self.ref_begin: Optional[ReferenceType[Expr]] = None

    def __repr__(self):
        return f"JSONPath({str(self)!r})"

    def __str__(self):
        return self.get_expression()

    def get_expression(self):
        if self.ref_begin is None:
            expr = self
        else:
            expr = self.ref_begin()

        parts = []
        while expr:
            part = expr._get_partial_expression()
            if isinstance(expr, (Array, Search, Compare)):
                if parts:
                    parts[-1] += part
                else:
                    parts.append(part)
            else:
                parts.append(part)

            if expr.ref_right:
                expr = expr.ref_right()
            else:
                expr = None

        return ".".join(parts)

    @abstractmethod
    def _get_partial_expression(self):
        raise NotImplementedError

    @abstractmethod
    def find(self, element):
        raise NotImplementedError

    def __getattr__(self, name):
        if name not in Expr._exprs:
            raise AttributeError

        expr_cls = Expr._exprs[name]

        def _expr_cls(*args, **kwargs):
            expr = expr_cls(*args, **kwargs)
            chain(pre=self, current=expr)
            return expr

        return _expr_cls

    def __lt__(self, value):
        return self.LessThan(value)

    def __le__(self, value):
        return self.LessEqual(value)

    def __eq__(self, value):
        return self.Equal(value)

    def __ge__(self, value):
        return self.GreaterEqual(value)

    def __gt__(self, value):
        return self.GreaterThan(value)

    def __ne__(self, value):
        return self.NotEqual(value)


class Root(Expr):
    def _get_partial_expression(self):
        return "$"

    def find(self, element):
        return [var_root.get(element)]


class Name(Expr):
    def __init__(self, name=None):
        super().__init__()
        self.name = name

    def _get_partial_expression(self):
        if self.name is None:
            return "*"

        return self.name

    def find(self, element):
        if not isinstance(element, dict):
            raise FindError()

        if self.name is None:
            return list(element.values())

        if self.name not in element:
            raise FindError()

        return [element[self.name]]


class Array(Expr):
    def __init__(self, idx=None):
        super().__init__()
        self.idx = idx

    def _get_partial_expression(self):
        if self.idx is None:
            idx = "*"
        else:
            idx = self.idx

        return f"[{idx!s}]"

    def find(self, element):
        if self.idx is None and isinstance(element, list):
            return element
        elif (
            isinstance(self.idx, int)
            and isinstance(element, list)
            and self.idx < len(element)
        ):
            return [element[self.idx]]
        elif isinstance(self.idx, Slice):
            return self.idx.find(element)
        elif isinstance(self.idx, Expr):
            filtered_items = []
            if isinstance(element, list):
                items = element
            elif isinstance(element, dict):
                items = element.values()
            else:
                raise FindError()

            for item in items:
                try:
                    token = var_finding.set(False)
                    try:
                        rv = self.idx.find(item)
                    finally:
                        var_finding.reset(token)
                    if rv:
                        if isinstance(self.idx, Compare):
                            if not rv[0]:
                                continue

                        filtered_items.append(item)
                except FindError:
                    pass
            return filtered_items

        raise FindError()


class Slice(Expr):
    def __init__(self, start=None, end=None, step=None):
        super().__init__()
        self.start = start
        self.end = end
        self.step = step

    def _get_partial_expression(self):
        parts = []
        if self.start:
            parts.append(str(self.start))
        else:
            parts.append("")

        if self.end:
            parts.append(str(self.end))
        else:
            parts.append("")

        if self.step:
            parts.append(str(self.step))

        return ":".join(parts)

    def find(self, element):
        if isinstance(element, list):
            start = self.start
            end = self.end
            step = self.step
            if start is None:
                start = 0
            if end is None:
                end = len(element)
            if step is None:
                step = 1

            return element[start:end:step]

        raise FindError()


class Brace(Expr):
    def __init__(self, expr: Expr):
        super().__init__()
        self.expr = expr

    def _get_partial_expression(self):
        return f"({self.expr!s})"

    def find(self, element):
        if isinstance(self.expr, Expr):
            token = var_finding.set(False)
            try:
                return [self.expr.find(element)]
            finally:
                var_finding.reset(token)

        raise FindError()


def recusive_find(expr: Expr, element: Any, rv: List[Any]):
    try:
        find_rv = expr.find(element)
        rv.extend(find_rv)
    except FindError:
        pass
    if isinstance(element, list):
        for item in element:
            recusive_find(expr, item, rv)
    elif isinstance(element, dict):
        for item in element.values():
            recusive_find(expr, item, rv)


class Search(Expr):
    def __init__(self, expr):
        super().__init__()
        self.expr = expr

    def _get_partial_expression(self):
        return f"..{self.expr!s}"

    def find(self, element):
        if isinstance(self.expr, (Name, Array)):
            rv = []
            if isinstance(self.expr, Array) and isinstance(self.expr.idx, Expr):
                recusive_find(self.expr, [element], rv)
            else:
                recusive_find(self.expr, element, rv)
            return rv


class Self(Expr):
    def _get_partial_expression(self):
        return "@"

    def find(self, element):
        return [var_self.get(element)]


class Compare(Expr):
    def __init__(self, target):
        super().__init__()
        self.target = target

    def get_target_value(self):
        if isinstance(self.target, Expr):
            try:
                token = var_finding.set(False)
                rv = self.target.find(var_self.get())
                if not rv:
                    raise FindError()

                return rv[0]
            finally:
                var_finding.reset(token)

        else:
            return self.target


class LessThan(Compare):
    def _get_partial_expression(self):
        return f" < {self.target}"

    def find(self, element):
        return [element < self.get_target_value()]


class LessEqual(Compare):
    def _get_partial_expression(self):
        return f" <= {self.target}"

    def find(self, element):
        return [element <= self.get_target_value()]


class Equal(Compare):
    def _get_partial_expression(self):
        return f" = {self.target}"

    def find(self, element):
        return [element == self.get_target_value()]


class GreaterEqual(Compare):
    def _get_partial_expression(self):
        return f" >= {self.target}"

    def find(self, element):
        return [element >= self.get_target_value()]


class GreaterThan(Compare):
    def _get_partial_expression(self):
        return f" > {self.target}"

    def find(self, element):
        return [element > self.get_target_value()]


class NotEqual(Compare):
    def _get_partial_expression(self):
        return f" != {self.target}"

    def find(self, element):
        return [element != self.get_target_value()]


__all__ = (
    "Expr",
    "ExprMeta",
    "Name",
    "Root",
    "Array",
    "Slice",
    "Search",
    "Self",
    "Brace",
    "chain",
    "recusive_find",
    "Compare",
    "LessThan",
    "LessEqual",
    "Equal",
    "GreaterEqual",
    "GreaterThan",
    "NotEqual",
)
