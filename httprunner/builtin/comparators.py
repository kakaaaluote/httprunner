"""
Built-in validate comparators.
"""

import math
import re
from collections import defaultdict
from typing import Any, Callable, Iterable, Literal, Optional, Text, Union

import jsonschema
from pydantic import BaseModel

from httprunner.builtin.jsonassert import (  # noqa
    json_assert,
    json_contains,
    json_equal,
)
from httprunner.builtin.jsoncomparator.jsonassert import (  # noqa
    json_contains_v2,
    json_equal_v2,
)
from httprunner.exceptions import ParamsError

Number = Union[int, float]


def equal(
    check_value: Any,
    expect_value: Any,
    message: Text = "",
):
    """Assert check_value equals to expect_value."""
    assert check_value == expect_value, message


def each_equal(
    check_value: Union[list, tuple],
    expect_value: Any,
    message: Text = "",
    *,
    is_not_empty: bool,
):
    """Assert each item of check_value equals to expect_value.

    If is_not_empty is True, check_value should not be empty.
    """
    # check_value should be list or tuple
    assert isinstance(
        check_value, (list, tuple)
    ), "check_value must be list or tuple type"

    # if is_not_empty is True, check_value should not be empty
    if is_not_empty:
        assert check_value, "check_value should not be empty when is_not_empty is True"

    # assert each item in check_value equals to expect_value, record the index and value of all the different items
    diff_items = [
        (index, item) for index, item in enumerate(check_value) if item != expect_value
    ]

    # if diff_items is not empty, raise AssertionError
    assert (
        not diff_items
    ), f"{message}\n预期列表中每一个值都等于 {repr(expect_value)}，但下面这些值不等于预期值，显示格式为 (index, value): \n{repr(diff_items)}"


def greater_than(
    check_value: Union[int, float], expect_value: Union[int, float], message: Text = ""
):
    assert check_value > expect_value, message


def less_than(
    check_value: Union[int, float], expect_value: Union[int, float], message: Text = ""
):
    assert check_value < expect_value, message


def greater_or_equals(
    check_value: Union[int, float], expect_value: Union[int, float], message: Text = ""
):
    assert check_value >= expect_value, message


def less_or_equals(
    check_value: Union[int, float], expect_value: Union[int, float], message: Text = ""
):
    assert check_value <= expect_value, message


def not_equal(check_value: Any, expect_value: Any, message: Text = ""):
    assert check_value != expect_value, message


def string_equals(check_value: Text, expect_value: Any, message: Text = ""):
    assert str(check_value) == str(expect_value), message


def length_equal(check_value: Text, expect_value: int, message: Text = ""):
    assert isinstance(expect_value, int), "expect_value should be int type"
    assert len(check_value) == expect_value, message


def length_greater_than(
    check_value: Text, expect_value: Union[int, float], message: Text = ""
):
    assert isinstance(
        expect_value, (int, float)
    ), "expect_value should be int/float type"
    assert len(check_value) > expect_value, message


def length_greater_or_equals(
    check_value: Text, expect_value: Union[int, float], message: Text = ""
):
    assert isinstance(
        expect_value, (int, float)
    ), "expect_value should be int/float type"
    assert len(check_value) >= expect_value, message


def length_less_than(
    check_value: Text, expect_value: Union[int, float], message: Text = ""
):
    assert isinstance(
        expect_value, (int, float)
    ), "expect_value should be int/float type"
    assert len(check_value) < expect_value, message


def length_less_or_equals(
    check_value: Text, expect_value: Union[int, float], message: Text = ""
):
    assert isinstance(
        expect_value, (int, float)
    ), "expect_value should be int/float type"
    assert len(check_value) <= expect_value, message


def contains(check_value: Any, expect_value: Any, message: Text = ""):
    assert isinstance(
        check_value, (list, tuple, dict, str, bytes)
    ), "expect_value should be list/tuple/dict/str/bytes type"
    assert expect_value in check_value, message


def not_contain(check_value: Any, expect_value: Any, message: str = "") -> None:
    assert isinstance(
        check_value, (list, tuple, dict, str, bytes)
    ), "check_value should be list/tuple/dict/str/bytes type"
    assert expect_value not in check_value, message


def contained_by(check_value: Any, expect_value: Any, message: Text = ""):
    assert isinstance(
        expect_value, (list, tuple, dict, str, bytes)
    ), "expect_value should be list/tuple/dict/str/bytes type"
    assert check_value in expect_value, message


def not_contained_by(check_value: Any, expect_value: Any, message: str = "") -> None:
    assert isinstance(
        expect_value, (list, tuple, dict, str, bytes)
    ), "expect_value should be list/tuple/dict/str/bytes type"
    assert check_value not in expect_value, message


def type_match(check_value: Any, expect_value: Any, message: Text = ""):
    def get_type(name):
        if isinstance(name, type):
            return name
        elif isinstance(name, str):
            try:
                return __builtins__[name]  # noqa
            except KeyError:
                raise ValueError(name)
        else:
            raise ValueError(name)

    if expect_value in ["None", "NoneType", None]:
        assert check_value is None, message
    else:
        assert type(check_value) is get_type(expect_value), message


def regex_match(check_value: Text, expect_value: Any, message: Text = ""):
    assert isinstance(expect_value, str), "expect_value should be Text type"
    assert isinstance(check_value, str), "check_value should be Text type"
    assert re.match(expect_value, check_value), message


def startswith(check_value: Any, expect_value: Any, message: Text = ""):
    assert str(check_value).startswith(str(expect_value)), message


def endswith(check_value: Text, expect_value: Any, message: Text = ""):
    assert str(check_value).endswith(str(expect_value)), message


def is_close(
    check_value: Number, expect_value: tuple[Number, Number], message: Text = ""
):
    a = check_value
    b = expect_value[0]
    abs_tol = expect_value[1]

    if not message:
        message = f"difference ({abs(a - b)}) between {a} and {b} exceeded the minimum absolute tolerance ({abs_tol})"

    assert math.isclose(a, b, abs_tol=abs_tol), message


def no_keys_duplicate(
    check_value: list,
    expect_value: Any,
    message: str = "",
) -> None:
    """
    Assert no duplicates in the list specified by `check_value`.

    Note:
        If assertion fails, the error message will print the duplicates and corresponding indexes.
        e.g. given list [55, 55, 56], the error message will contain [(55, [0, 1])]

    :param check_value: the target list to check
    :param expect_value: should be `None`
    """

    def get_list_duplicate_items(array: list) -> list[tuple]:
        """
        Get the duplicates and corresponding indexes from list.

        >>> get_list_duplicate_items([55, 55, 56])
        ... [(55, (0, 1))]
        """
        counter = defaultdict(list)

        for index, item in enumerate(array):
            counter[item].append(index)

        return [
            (list_item, indexes)
            for list_item, indexes in counter.items()
            if len(indexes) > 1
        ]

    assert isinstance(
        check_value, list
    ), f"`check_value` should be a list, but got `{type(check_value)}`"
    assert not (
        duplicate_items := get_list_duplicate_items(check_value)
    ), f"{message}\nduplicate items found: {duplicate_items}"


def list_sorted_in(
    check_value: list,
    expect_value: Union[Callable, Literal["ASC", "DSC"]],
    message: str = "",
):
    """
    Assert the list is sorted in some specific order.

    Note:
        1. if expected_value is string 'ASC', the list is expected to be sorted in ascending order
        2. if expected_value is string 'DSC', the list is expected to be sorted in descending order
        3. if expected_value is a function object, you must define and import the function, or use a lambda function,
            reference list.sort() for more information.
    """
    assert isinstance(
        check_value, list
    ), f"type of check value must be list, but got: {type(check_value)}"
    assert isinstance(expect_value, Callable) or expect_value in [
        "ASC",
        "DSC",
    ], f"type of expected value should be Callable or the value is one of 'ASC', 'DSC', but got {type(expect_value)}"

    sorted_value = check_value.copy()

    if expect_value == "ASC":
        sorted_value.sort()
    elif expect_value == "DSC":
        sorted_value.sort(reverse=True)
    else:
        sorted_value.sort(key=expect_value)

    assert check_value == sorted_value, (
        f"{message}\n"
        f"the list is not sorted as expected: {expect_value}\n"
        f"actual value: {check_value}\n"
        f"expect value: {sorted_value}"
    )


def all_(
    check_value: Iterable,
    expect_value: Optional[Union[Callable, tuple[Callable, dict]]],
    message: Text = "",
    *,
    preprocessor_kwargs: dict = None,
):
    """Pass `check_value` to builtin function `all`.

    If `expect_value` is callable, `check_value` will be passed to it first, then pass the result to `all`.
    """
    preprocessor_kwargs = preprocessor_kwargs or {}

    preprocessor = None
    if expect_value:
        if callable(expect_value):
            preprocessor = expect_value
        elif isinstance(expect_value, tuple):
            preprocessor, kwargs = expect_value
            preprocessor_kwargs.update(kwargs)
        else:
            raise ParamsError(
                f"if expected_value is not None, it should be callable or a tuple, but got {type(expect_value)}"
            )

    if preprocessor:
        check_value = preprocessor(check_value, **preprocessor_kwargs)

    assert all(check_value), message


def match_json_schema(
    check_value: dict,
    expect_value: dict,
    message: Text = "",
):
    """Assert value matches the JSON schema."""
    try:
        jsonschema.validate(check_value, expect_value)
        jsonschema_error_message = None
    except Exception as e:
        jsonschema_error_message = e

    assert not jsonschema_error_message, f"{message}\n{jsonschema_error_message}"


def match_pydantic_model(
    check_value: dict,
    expect_value: BaseModel,
    message: Text = "",
):
    """Assert value matches the pydantic model."""
    try:
        expect_value.model_validate(check_value, strict=True)
        validate_error_message = None
    except Exception as e:
        validate_error_message = e

    assert not validate_error_message, f"{message}\n{validate_error_message}"


def is_truthy(check_value: Any, expect_value: Any, message: Text = ""):  # noqa
    """Assert value is truthy."""
    assert bool(check_value), message


def is_falsy(check_value: Any, expect_value: Any, message: Text = ""):  # noqa
    """Assert value is falsy."""
    assert not bool(check_value), message


def is_truthy_and_subset(
    check_value: Any, expected_value: Iterable, message: Text = ""
):
    """Assert check_value is considered true and every element in check_value is in expected_value."""
    assert check_value and set(check_value).issubset(set(expected_value)), message


def is_truthy_and_superset(
    check_value: Any, expected_value: Iterable, message: Text = ""
):
    """Assert check_value is considered true and every element in expected_value is in check_value."""
    assert check_value and set(check_value).issuperset(set(expected_value)), message


def assert_lambda(
    check_value: Any,
    expect_value: Union[Callable, tuple[Callable, dict]],
    message: Text = "",
    *,
    validator_kwargs: dict = None,
):
    """Assert with custom validator."""
    validator_kwargs = validator_kwargs or {}

    try:
        if isinstance(expect_value, Callable):
            validator = expect_value
        elif isinstance(expect_value, tuple):
            validator, kwargs = expect_value
            validator_kwargs.update(kwargs)
        else:
            raise ParamsError(
                f"expect_value should be callable or a tuple, but got {type(expect_value)}"
            )

        validator(check_value, **validator_kwargs)
    except AssertionError as e:
        raise AssertionError(f"{message}\n{e}")
