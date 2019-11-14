# Standard Library
import reprlib

# Third Party Library
import pytest

# First Party Library
from jsonpath.core import Array, Brace, Name, Root, Slice


@pytest.mark.parametrize(
    "name,data,expect",
    [("boo", {"boo": 1}, [1]), (None, {"boo": 1, "bar": 2}, [1, 2])],
    ids=reprlib.repr,
)
def test_name_find(name, data, expect):
    assert Name(name).find(data) == expect


@pytest.mark.parametrize(
    "names,data,expect",
    [
        (["boo", "bar"], {"boo": {"bar": 1}}, [1]),
        (["boo", "bar", "boo"], {"boo": {"bar": {"boo": 1}}}, [1]),
        (
            ["boo", None, "boo"],
            {"boo": {"boo": {"boo": 1}, "bar": {"boo": 2}}},
            [1, 2],
        ),
    ],
    ids=reprlib.repr,
)
def test_name_chain_find(names, data, expect):
    jp = Name(names[0])
    for name in names[1:]:
        jp = jp.Name(name)

    assert jp.find(data) == expect


@pytest.mark.parametrize(
    "data", [[], "abc", {"a": "b"}, 1, 1.0], ids=reprlib.repr
)
def test_root(data):
    assert Root().find(data) == [data]


@pytest.mark.parametrize(
    "start,end,step,data,expect",
    [
        (0, 1, 1, [1, 2], [1]),
        (0, None, 1, [1, 2], [1, 2]),
        (None, -1, 1, [1, 2, 3], [1, 2]),
        (None, None, 2, [1, 2, 3], [1, 3]),
    ],
    ids=reprlib.repr,
)
def test_slice_in_array(start, end, step, data, expect):
    jp = Root().Array(Slice(start, end, step))
    assert jp.find(data) == expect


@pytest.mark.parametrize(
    "expr,data,expect",
    [
        (Root().Search(Array(0)), {"boo": [{"boo": [1]}]}, [{"boo": [1]}, 1]),
        (
            Root().Search(Array()),
            {"boo": [{"boo": [1, 2]}]},
            [{"boo": [1, 2]}, 1, 2],
        ),
        (
            Root().Search(Array(Slice(None, -1, 2))),
            {"boo": [{"boo": [1, 2, 3, 4, 5]}, 1]},
            [{"boo": [1, 2, 3, 4, 5]}, 1, 3],
        ),
    ],
)
def test_search(expr, data, expect):
    assert expr.find(data) == expect


@pytest.mark.parametrize(
    "start,end,step,data,expect",
    [
        (0, 1, 1, [1, 2], [1]),
        (0, None, 1, [1, 2], [1, 2]),
        (None, -1, 1, [1, 2, 3], [1, 2]),
        (None, None, 2, [1, 2, 3], [1, 3]),
    ],
    ids=reprlib.repr,
)
def test_slice(start, end, step, data, expect):
    jp = Root().Slice(start, end, step)
    assert jp.find(data) == expect


@pytest.mark.parametrize(
    "expr,data,expect",
    [
        (
            Root().Array(Name("price") > 100),
            [{"price": 100}, {"price": 200}],
            [{"price": 200}],
        ),
        (
            Root().Array(Name("price").GreaterThan(100)),
            [{"price": 100}, {"price": 200}],
            [{"price": 200}],
        ),
        (
            Root().Array(Name("price") >= 100),
            [{"price": 100}, {"price": 200}],
            [{"price": 100}, {"price": 200}],
        ),
        (
            Root().Array(Name("price").GreaterEqual(100)),
            [{"price": 100}, {"price": 200}],
            [{"price": 100}, {"price": 200}],
        ),
        (
            Root().Array(Name("price") < 100),
            [{"price": 100}, {"price": 200}],
            [],
        ),
        (
            Root().Array(Name("price").LessThan(100)),
            [{"price": 100}, {"price": 200}],
            [],
        ),
        (
            Root().Array(Name("price") <= 100),
            [{"price": 100}, {"price": 200}],
            [{"price": 100}],
        ),
        (
            Root().Array(Name("price").LessEqual(100)),
            [{"price": 100}, {"price": 200}],
            [{"price": 100}],
        ),
        (
            Root().Array(Name("price") == 100),
            [{"price": 100}, {"price": 200}],
            [{"price": 100}],
        ),
        (
            Root().Array(Name("price").Equal(100)),
            [{"price": 100}, {"price": 200}],
            [{"price": 100}],
        ),
        (
            Root().Array(Name("price") != 100),
            [{"price": 100}, {"price": 200}],
            [{"price": 200}],
        ),
        (
            Root().Array(Name("price").NotEqual(100)),
            [{"price": 100}, {"price": 200}],
            [{"price": 200}],
        ),
    ],
    ids=reprlib.repr,
)
def test_comparation(expr, data, expect):
    assert expr.find(data) == expect


@pytest.mark.parametrize(
    "expr,data,expect",
    [
        (
            Root().Search(Array(Name("price") > 100)),
            {
                "price": 200,
                "charpter": [{"price": 100}, {"price": 200}, {"price": 300}],
            },
            [
                {
                    "price": 200,
                    "charpter": [
                        {"price": 100},
                        {"price": 200},
                        {"price": 300},
                    ],
                },
                {"price": 200},
                {"price": 300},
            ],
        ),
        (
            Root().Search(Array(Name("price") >= 100)),
            {
                "price": 200,
                "charpter": [{"price": 100}, {"price": 200}, {"price": 300}],
            },
            [
                {
                    "price": 200,
                    "charpter": [
                        {"price": 100},
                        {"price": 200},
                        {"price": 300},
                    ],
                },
                {"price": 100},
                {"price": 200},
                {"price": 300},
            ],
        ),
        (
            Root().Search(Array(Name("price") <= 100)),
            {
                "price": 200,
                "charpter": [{"price": 100}, {"price": 200}, {"price": 300}],
            },
            [{"price": 100}],
        ),
        (
            Root().Search(Array(Name("price") < 100)),
            {
                "price": 200,
                "charpter": [{"price": 100}, {"price": 200}, {"price": 300}],
            },
            [],
        ),
        (
            Root().Search(Array(Name("price") == 100)),
            {
                "price": 200,
                "charpter": [{"price": 100}, {"price": 200}, {"price": 300}],
            },
            [{"price": 100}],
        ),
        (
            Root().Search(Array(Name("price") != 100)),
            {
                "price": 200,
                "charpter": [{"price": 100}, {"price": 200}, {"price": 300}],
            },
            [
                {
                    "price": 200,
                    "charpter": [
                        {"price": 100},
                        {"price": 200},
                        {"price": 300},
                    ],
                },
                {"price": 200},
                {"price": 300},
            ],
        ),
    ],
)
def test_comparation_in_search(expr, data, expect):
    assert expr.find(data) == expect


@pytest.mark.parametrize(
    "expr,data,expect",
    [
        (
            Root().Name(),
            {"boo": [1, 2, 3], "bar": [2, 3, 4]},
            [[1, 2, 3], [2, 3, 4]],
        ),
        (Root().Name().Array(0), {"boo": [1, 2, 3], "bar": [2, 3, 4]}, [1, 2]),
        (
            Root().Name().Array(),
            {"boo": [1, 2, 3], "bar": [2, 3, 4]},
            [1, 2, 3, 2, 3, 4],
        ),
        (
            Brace(Root().Name()).Array(0),
            {"boo": [1, 2, 3], "bar": [2, 3, 4]},
            [[1, 2, 3]],
        ),
        (
            Brace(Root().Name().Array()).Array(0),
            {"boo": [1, 2, 3], "bar": [2, 3, 4]},
            [1],
        ),
    ],
    ids=reprlib.repr,
)
def test_others(expr, data, expect):
    assert expr.find(data) == expect
