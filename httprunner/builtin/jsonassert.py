from typing import Any, Optional, Union

from deepdiff import DeepDiff
from dotwiz import DotWiz

from httprunner.builtin.jsonassert_formatter import DeepDiffFormatter
from httprunner.builtin.jsoncomparator.jsonassert import (
    json_contains_v2,
    json_equal_v2,
)


def json_assert(
    actual_value: Union[dict, list],
    expect_value: Union[dict, list],
    message: str,
    strict: bool,
    make_assertion: bool = True,
    **deepdiff_kwargs,
) -> Optional[str]:
    """Equivalent to java unit test lib JSONassert."""
    # assert data types of check value and expect value are the same
    if isinstance(expect_value, dict):
        assert isinstance(
            actual_value, dict
        ), f"the type of data is expected to be 'dict', but '{type(actual_value).__name__}' got."

    if isinstance(expect_value, list):
        assert isinstance(
            actual_value, list
        ), f"the type of data is expected to be 'list', but '{type(actual_value).__name__}' got."

    ignore_order = False
    report_repetition = False

    if not strict:
        ignore_order = True
        report_repetition = True

    ignore_type_in_groups = [(dict, DotWiz)]
    if "ignore_type_in_groups" in deepdiff_kwargs:
        user_ignore_type_in_groups = deepdiff_kwargs.pop("ignore_type_in_groups") or []
        ignore_type_in_groups.extend(user_ignore_type_in_groups)

    ddiff = DeepDiff(
        expect_value,
        actual_value,
        view="tree",
        ignore_order=ignore_order,
        report_repetition=report_repetition,
        cutoff_intersection_for_pairs=1,
        cutoff_distance_for_pairs=1,
        ignore_type_in_groups=ignore_type_in_groups,
        **deepdiff_kwargs,
    )

    formatter = DeepDiffFormatter(strict, ddiff)
    formatter.format()
    formatted_string = formatter.formatted_string

    if not strict and "dictionary_item_added" in ddiff.to_dict().keys():
        ddiff.pop("dictionary_item_added")

    if make_assertion:
        assert len(ddiff) == 0, f"{message}\n{formatted_string}"
    else:
        if len(ddiff) == 0:
            return None
        else:
            return formatted_string


def json_contains(
    check_value: Any,
    expect_value: Any,
    message: str = "",
    *,
    ignore_string_type_changes: bool = False,
    ignore_numeric_type_changes: bool = False,
    ignore_type_in_groups: Union[tuple, list[tuple]] = None,
    **other_deepdiff_kwargs,
) -> None:
    """Equivalent to the non-strict mode of java unit test lib JSONassert.

    By default, use java JSONassert (re-implemented with Python) as the comparator,
    fallback to deepdiff version if any of the following conditions are met:
        * ignore_string_type_changes is True
        * ignore_numeric_type_changes is True
        * ignore_type_in_groups is not None
        * other_deepdiff_kwargs is not empty
        * expected_value is neither a dict nor a list
        * check_value is neither a dict nor a list

    The original JSONassert library only supports comparing JSON objects and arrays,
    but when reimplemented based on deepdiff, it can also compare other types of data,
    to ensure compatibility, we also support comparing other types of data in this function too.
    """
    # fallback to deepdiff version if any of the following conditions are met.
    if (
        ignore_string_type_changes
        or ignore_numeric_type_changes
        or ignore_type_in_groups
        or other_deepdiff_kwargs
        or not isinstance(expect_value, (dict, list))
        or not isinstance(check_value, (dict, list))
    ):
        deepdiff_kwargs = {
            "ignore_string_type_changes": ignore_string_type_changes,
            "ignore_numeric_type_changes": ignore_numeric_type_changes,
            "ignore_type_in_groups": ignore_type_in_groups,
            **other_deepdiff_kwargs,
        }

        # note: specifying deepdiff arguments in tuple is not recommended, keep it for compatibility
        if isinstance(expect_value, tuple):
            if not isinstance(expect_value[1], dict):
                raise TypeError(
                    "the second element must be a dict if `expect_value` is a tuple"
                )
            expect_value, deepdiff_args = expect_value  # the real expect_value
            deepdiff_kwargs.update(deepdiff_args)

        return json_assert(
            check_value, expect_value, message, strict=False, **deepdiff_kwargs
        )

    # use java JSONassert (re-implemented with Python) as the comparator
    json_contains_v2(check_value, expect_value, message)


def json_equal(
    check_value: Union[dict, list],
    expect_value: Union[tuple, dict, list],
    message: str = "",
    *,
    ignore_string_type_changes: bool = False,
    ignore_numeric_type_changes: bool = False,
    ignore_type_in_groups: Union[tuple, list[tuple]] = None,
    **other_deepdiff_kwargs,
) -> None:
    """Equivalent to the strict mode of java unit test lib JSONassert.

    By default, use java JSONassert (re-implemented with Python) as the comparator,
    fallback to deepdiff version if any of the following conditions are met:
        * ignore_string_type_changes is True
        * ignore_numeric_type_changes is True
        * ignore_type_in_groups is not None
        * other_deepdiff_kwargs is not empty
        * expected_value is neither a dict nor a list
        * check_value is neither a dict nor a list

    The original JSONassert library only supports comparing JSON objects and arrays,
    but when reimplemented based on deepdiff, it can also compare other types of data,
    to ensure compatibility, we also support comparing other types of data in this function too.
    """
    # fallback to deepdiff version if any of the following conditions are met.
    if (
        ignore_string_type_changes
        or ignore_numeric_type_changes
        or ignore_type_in_groups
        or other_deepdiff_kwargs
        or not isinstance(expect_value, (dict, list))
        or not isinstance(check_value, (dict, list))
    ):
        deepdiff_kwargs = {
            "ignore_string_type_changes": ignore_string_type_changes,
            "ignore_numeric_type_changes": ignore_numeric_type_changes,
            "ignore_type_in_groups": ignore_type_in_groups,
            **other_deepdiff_kwargs,
        }

        # note: specifying deepdiff arguments in tuple is not recommended, keep it for compatibility
        if isinstance(expect_value, tuple):
            if not isinstance(expect_value[1], dict):
                raise TypeError(
                    "the second element must be a dict if `expect_value` is a tuple"
                )
            expect_value, deepdiff_args = expect_value  # the real expect_value
            deepdiff_kwargs.update(deepdiff_args)

        return json_assert(
            check_value, expect_value, message, strict=True, **deepdiff_kwargs
        )

    # use java JSONassert (re-implemented with Python) as the comparator
    json_equal_v2(check_value, expect_value, message)


def get_json_contains_diff_message(
    check_value: Union[dict, list], expect_value: Union[dict, list], message: str = ""
) -> Optional[str]:
    """
    Return None if check ok, else return formatted string.
    """
    return json_assert(
        check_value, expect_value, message, strict=False, make_assertion=False
    )
