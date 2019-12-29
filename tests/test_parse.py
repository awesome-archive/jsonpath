# Standard Library
import reprlib

# Third Party Library
import pytest

# First Party Library
from jsonpath import parse


@pytest.mark.parametrize(
    "expr,data,expect",
    [
        ("boo", {"boo": 1}, [1]),
        ("boo.bar", {"boo": {"bar": 1}}, [1]),
        ("boo.bar.boo", {"boo": {"bar": {"boo": 1}}}, [1]),
        ("$.*", {"boo": 1, "bar": 2}, [1, 2]),
        ("boo.*", {"boo": {"boo": 1, "bar": 2}}, [1, 2]),
        ("boo.*.boo", {"boo": {"boo": {"boo": 1}, "bar": {"boo": 2}}}, [1, 2]),
        ("boo.*.boo", {"boo": {"boo": {"boo": 1}, "bar": {"bar": 2}}}, [1]),
        ("boo.*.boo", {"boo": {"boo": {"boo": 1}, "bar": 1}}, [1]),
        ("$[0]", [1, 2], [1]),
        ("boo[0]", {"boo": [1, 2]}, [1]),
        ("$[*]", [1, 2], [1, 2]),
        ("$[0:1]", [1, 2], [1]),
        ("$[0:]", [1, 2], [1, 2]),
        ("$[:-1]", [1, 2, 3], [1, 2]),
        ("$[::2]", [1, 2, 3], [1, 3]),
        ("$.*[0]", {"boo": [1, 2, 3], "bar": [2, 3, 4]}, [1, 2]),
        ("$.*[*]", {"boo": [1, 2, 3], "bar": [2, 3, 4]}, [1, 2, 3, 2, 3, 4]),
        ("($.*)[0]", {"boo": [1, 2, 3], "bar": [2, 3, 4]}, [[1, 2, 3]]),
        ("($.*[*])[0]", {"boo": [1, 2, 3], "bar": [2, 3, 4]}, [1]),
        ("$.*", {"boo": [1, 2, 3], "bar": [2, 3, 4]}, [[1, 2, 3], [2, 3, 4]]),
    ],
    ids=reprlib.repr,
)
def test_find(expr, data, expect):
    jp = parse(expr)
    assert jp.find(data) == expect
