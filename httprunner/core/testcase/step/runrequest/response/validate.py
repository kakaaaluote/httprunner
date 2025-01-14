from typing import Any, Callable, Literal, Optional, Text, Type, Union

from pydantic import BaseModel
from typing_extensions import deprecated

from httprunner.core.testcase.config import Config  # noqa
from httprunner.models import TStep, Validator

Number = Union[int, float]


class StepRequestValidation(object):
    """Class representing response validation."""

    def __init__(self, step_context: TStep):
        self._step_context = step_context

    def clear(self) -> "StepRequestValidation":
        """Clear all validators added."""
        self._step_context.validators.clear()
        return self

    def assert_equal(
        self,
        jmespath_expression: Text,
        expected_value: Any,
        message: Text = "",
    ) -> "StepRequestValidation":
        """Assert the value is equal to the expected value.

        :param jmespath_expression: JMESPath expression
        :param expected_value: expected value
        :param message: error message
        """
        self._step_context.validators.append(
            Validator(
                method="equal",
                expression=jmespath_expression,
                expect=expected_value,
                message=message,
            )
        )
        return self

    def assert_each_equal(
        self,
        jmespath_expression: Text,
        expected_value: Any,
        message: Text = "",
        *,
        is_not_empty: bool = True,
    ) -> "StepRequestValidation":
        """Assert each value is equal to the expected value.

        :param jmespath_expression: JMESPath expression
        :param expected_value: expected value
        :param message: error message
        :param is_not_empty: if True, the list must not be empty
        """
        self._step_context.validators.append(
            Validator(
                method="each_equal",
                expression=jmespath_expression,
                expect=expected_value,
                message=message,
                config={"is_not_empty": is_not_empty},
            )
        )
        return self

    def assert_not_equal(
        self, jmespath_expression: Text, expected_value: Any, message: Text = ""
    ) -> "StepRequestValidation":
        self._step_context.validators.append(
            Validator(
                method="not_equal",
                expression=jmespath_expression,
                expect=expected_value,
                message=message,
            )
        )
        return self

    def assert_greater_than(
        self,
        jmespath_expression: Text,
        expected_value: Union[int, float, str],
        message: Text = "",
    ) -> "StepRequestValidation":
        self._step_context.validators.append(
            Validator(
                method="greater_than",
                expression=jmespath_expression,
                expect=expected_value,
                message=message,
            )
        )
        return self

    def assert_less_than(
        self,
        jmespath_expression: Text,
        expected_value: Union[int, float, str],
        message: Text = "",
    ) -> "StepRequestValidation":
        self._step_context.validators.append(
            Validator(
                method="less_than",
                expression=jmespath_expression,
                expect=expected_value,
                message=message,
            )
        )
        return self

    def assert_greater_or_equals(
        self,
        jmespath_expression: Text,
        expected_value: Union[int, float, str],
        message: Text = "",
    ) -> "StepRequestValidation":
        self._step_context.validators.append(
            Validator(
                method="greater_or_equals",
                expression=jmespath_expression,
                expect=expected_value,
                message=message,
            )
        )
        return self

    def assert_less_or_equals(
        self,
        jmespath_expression: Text,
        expected_value: Union[int, float, str],
        message: Text = "",
    ) -> "StepRequestValidation":
        self._step_context.validators.append(
            Validator(
                method="less_or_equals",
                expression=jmespath_expression,
                expect=expected_value,
                message=message,
            )
        )
        return self

    def assert_length_equal(
        self,
        jmespath_expression: Text,
        expected_value: Union[int, str],
        message: Text = "",
    ) -> "StepRequestValidation":
        self._step_context.validators.append(
            Validator(
                method="length_equal",
                expression=jmespath_expression,
                expect=expected_value,
                message=message,
            )
        )
        return self

    def assert_length_greater_than(
        self,
        jmespath_expression: Text,
        expected_value: Union[int, str],
        message: Text = "",
    ) -> "StepRequestValidation":
        self._step_context.validators.append(
            Validator(
                method="length_greater_than",
                expression=jmespath_expression,
                expect=expected_value,
                message=message,
            )
        )
        return self

    def assert_length_less_than(
        self,
        jmespath_expression: Text,
        expected_value: Union[int, str],
        message: Text = "",
    ) -> "StepRequestValidation":
        self._step_context.validators.append(
            Validator(
                method="length_less_than",
                expression=jmespath_expression,
                expect=expected_value,
                message=message,
            )
        )
        return self

    def assert_length_greater_or_equals(
        self,
        jmespath_expression: Text,
        expected_value: Union[int, str],
        message: Text = "",
    ) -> "StepRequestValidation":
        self._step_context.validators.append(
            Validator(
                method="length_greater_or_equals",
                expression=jmespath_expression,
                expect=expected_value,
                message=message,
            )
        )
        return self

    def assert_length_less_or_equals(
        self,
        jmespath_expression: Text,
        expected_value: Union[int, str],
        message: Text = "",
    ) -> "StepRequestValidation":
        self._step_context.validators.append(
            Validator(
                method="length_less_or_equals",
                expression=jmespath_expression,
                expect=expected_value,
                message=message,
            )
        )
        return self

    def assert_string_equals(
        self, jmespath_expression: Text, expected_value: Any, message: Text = ""
    ) -> "StepRequestValidation":
        self._step_context.validators.append(
            Validator(
                method="string_equals",
                expression=jmespath_expression,
                expect=expected_value,
                message=message,
            )
        )
        return self

    def assert_startswith(
        self, jmespath_expression: Text, expected_value: Text, message: Text = ""
    ) -> "StepRequestValidation":
        self._step_context.validators.append(
            Validator(
                method="startswith",
                expression=jmespath_expression,
                expect=expected_value,
                message=message,
            )
        )
        return self

    def assert_endswith(
        self, jmespath_expression: Text, expected_value: Text, message: Text = ""
    ) -> "StepRequestValidation":
        self._step_context.validators.append(
            Validator(
                method="endswith",
                expression=jmespath_expression,
                expect=expected_value,
                message=message,
            )
        )
        return self

    def assert_regex_match(
        self, jmespath_expression: Text, expected_value: Text, message: Text = ""
    ) -> "StepRequestValidation":
        self._step_context.validators.append(
            Validator(
                method="regex_match",
                expression=jmespath_expression,
                expect=expected_value,
                message=message,
            )
        )
        return self

    def assert_contains(
        self, jmespath_expression: Text, expected_value: Any, message: Text = ""
    ) -> "StepRequestValidation":
        self._step_context.validators.append(
            Validator(
                method="contains",
                expression=jmespath_expression,
                expect=expected_value,
                message=message,
            )
        )
        return self

    def assert_not_contain(
        self, jmespath_expression: Text, expected_value: Any, message: Text = ""
    ) -> "StepRequestValidation":
        self._step_context.validators.append(
            Validator(
                method="not_contain",
                expression=jmespath_expression,
                expect=expected_value,
                message=message,
            )
        )
        return self

    def assert_not_contained_by(
        self, jmespath_expression: Text, expected_value: Any, message: Text = ""
    ) -> "StepRequestValidation":
        self._step_context.validators.append(
            Validator(
                method="not_contained_by",
                expression=jmespath_expression,
                expect=expected_value,
                message=message,
            )
        )
        return self

    def assert_no_keys_duplicate(
        self, jmespath_expression: Text, message: Text = ""
    ) -> "StepRequestValidation":
        """
        Assert no duplicates in the list specified by jmespath_expression.
        """
        self._step_context.validators.append(
            Validator(
                method="no_keys_duplicate",
                expression=jmespath_expression,
                expect=None,
                message=message,
            )
        )
        return self

    def assert_contained_by(
        self, jmespath_expression: Text, expected_value: Any, message: Text = ""
    ) -> "StepRequestValidation":
        self._step_context.validators.append(
            Validator(
                method="contained_by",
                expression=jmespath_expression,
                expect=expected_value,
                message=message,
            )
        )
        return self

    def assert_type_match(
        self, jmespath_expression: Text, expected_value: Any, message: Text = ""
    ) -> "StepRequestValidation":
        self._step_context.validators.append(
            Validator(
                method="type_match",
                expression=jmespath_expression,
                expect=expected_value,
                message=message,
            )
        )
        return self

    def assert_json_contains(
        self,
        jmespath_expression: Text,
        expected_value: Any,
        message: Text = "",
        *,
        ignore_string_type_changes: bool = False,
        ignore_numeric_type_changes: bool = False,
        ignore_type_in_groups: Union[tuple, list[tuple]] = None,
        **other_deepdiff_kwargs,
    ) -> "StepRequestValidation":
        """Equivalent to the JSONassert non-strict mode.

        By default, use java JSONassert (re-implemented with Python) as the comparator,
        fallback to deepdiff version if any of the following conditions are met: \n
            * ignore_string_type_changes is True
            * ignore_numeric_type_changes is True
            * ignore_type_in_groups is not None
            * other_deepdiff_kwargs is not empty
            * expected_value is neither a dict nor a list
            * check_value is neither a dict nor a list

        The original JSONassert library only supports comparing JSON objects and arrays,
        but when reimplemented based on deepdiff, it can also compare other types of data,
        to ensure compatibility, we also support comparing other types of data in this function too.

        :param jmespath_expression: JMESPath expression
        :param expected_value: expected value
        :param message: error message
        :param ignore_string_type_changes: whether to ignore string type changes or not.
            For example b"Hello" vs. "Hello" are considered the same if ignore_string_type_changes is set to True.
        :param ignore_numeric_type_changes: whether to ignore numeric type changes or not.
            For example 10 vs. 10.0 are considered the same if ignore_numeric_type_changes is set to True.
        :param ignore_type_in_groups: ignores types when t1 and t2 are both within the same type group.
            ref: https://zepworks.com/deepdiff/current/ignore_types_or_values.html
        :param other_deepdiff_kwargs: other kwargs supported by DeepDiff except:
            view, ignore_order, report_repetition, cutoff_intersection_for_pairs, cutoff_distance_for_pairs
        """
        # raise exception if these keys are in other_deepdiff_kwargs
        if other_deepdiff_kwargs and (
            blocked_args := set(other_deepdiff_kwargs)
            & {
                "view",
                "ignore_order",
                "report_repetition",
                "cutoff_intersection_for_pairs",
                "cutoff_distance_for_pairs",
            }
        ):
            raise ValueError(
                f"Keyword arguments {blocked_args} cannot be used in assert_json_contains."
            )

        self._step_context.validators.append(
            Validator(
                method="json_contains",
                expression=jmespath_expression,
                expect=expected_value,
                message=message,
                config={
                    "ignore_string_type_changes": ignore_string_type_changes,
                    "ignore_numeric_type_changes": ignore_numeric_type_changes,
                    "ignore_type_in_groups": ignore_type_in_groups,
                    **other_deepdiff_kwargs,
                },
            )
        )
        return self

    def assert_json_equal(
        self,
        jmespath_expression: Text,
        expected_value: Any,
        message: Text = "",
        *,
        ignore_string_type_changes: bool = False,
        ignore_numeric_type_changes: bool = False,
        ignore_type_in_groups: Union[tuple, list[tuple]] = None,
        **other_deepdiff_kwargs,
    ) -> "StepRequestValidation":
        """Equivalent to the JSONassert strict mode.

        By default, use java JSONassert (re-implemented with Python) as the comparator,
        fallback to deepdiff version if any of the following conditions are met: \n
            * ignore_string_type_changes is True
            * ignore_numeric_type_changes is True
            * ignore_type_in_groups is not None
            * other_deepdiff_kwargs is not empty
            * expected_value is neither a dict nor a list
            * check_value is neither a dict nor a list

        The original JSONassert library only supports comparing JSON objects and arrays,
        but when reimplemented based on deepdiff, it can also compare other types of data,
        to ensure compatibility, we also support comparing other types of data in this function too.

        :param jmespath_expression: JMESPath expression
        :param expected_value: expected value
        :param message: error message
        :param ignore_string_type_changes: whether to ignore string type changes or not.
            For example b"Hello" vs. "Hello" are considered the same if ignore_string_type_changes is set to True.
        :param ignore_numeric_type_changes: whether to ignore numeric type changes or not.
            For example 10 vs. 10.0 are considered the same if ignore_numeric_type_changes is set to True.
        :param ignore_type_in_groups: ignores types when t1 and t2 are both within the same type group.
            ref: https://zepworks.com/deepdiff/current/ignore_types_or_values.html
        :param other_deepdiff_kwargs: other kwargs supported by DeepDiff except:
            view, ignore_order, report_repetition, cutoff_intersection_for_pairs, cutoff_distance_for_pairs
        """
        # raise exception if these keys are in other_deepdiff_kwargs
        if other_deepdiff_kwargs and (
            blocked_args := set(other_deepdiff_kwargs)
            & {
                "view",
                "ignore_order",
                "report_repetition",
                "cutoff_intersection_for_pairs",
                "cutoff_distance_for_pairs",
            }
        ):
            raise ValueError(
                f"Keyword arguments {blocked_args} cannot be used in assert_json_contains."
            )

        self._step_context.validators.append(
            Validator(
                method="json_equal",
                expression=jmespath_expression,
                expect=expected_value,
                message=message,
                config={
                    "ignore_string_type_changes": ignore_string_type_changes,
                    "ignore_numeric_type_changes": ignore_numeric_type_changes,
                    "ignore_type_in_groups": ignore_type_in_groups,
                    **other_deepdiff_kwargs,
                },
            )
        )
        return self

    @deprecated(
        "This method is deprecated, use assert_json_contains() instead. "
        "Validator assert_json_contains() now use java-version JSONassert (re-implemented in Python) by default."
    )
    def assert_json_contains_with_java(
        self,
        jmespath_expression: Text,
        expected_value: Any,
        message: Text = "",
    ) -> "StepRequestValidation":
        """Equivalent to the JSONassert non-strict mode with java version."""
        self._step_context.validators.append(
            Validator(
                method="json_contains_v2",
                expression=jmespath_expression,
                expect=expected_value,
                message=message,
            )
        )
        return self

    @deprecated(
        "This method is deprecated, use assert_json_equal() instead. "
        "Validator assert_json_equal() now use java-version JSONassert (re-implemented in Python) by default."
    )
    def assert_json_equal_with_java(
        self,
        jmespath_expression: Text,
        expected_value: Any,
        message: Text = "",
    ) -> "StepRequestValidation":
        """Equivalent to the JSONassert strict mode with java version."""
        self._step_context.validators.append(
            Validator(
                method="json_equal_v2",
                expression=jmespath_expression,
                expect=expected_value,
                message=message,
            )
        )
        return self

    def assert_list_sorted_in(
        self,
        jmespath_expression: Text,
        expected_value: Union[Callable, Literal["ASC", "DSC"]],
        message: Text = "",
    ) -> "StepRequestValidation":
        """Assert the list is sorted in some specific order.

        Note:
        1. if expected_value is string 'ASC', the list is expected to be sorted in ascending order
        2. if expected_value is string 'DSC', the list is expected to be sorted in descending order
        3. if expected_value is a function object, you must define and import the function, or use a lambda function,
        reference list.sort() for more information.
        """
        self._step_context.validators.append(
            Validator(
                method="list_sorted_in",
                expression=jmespath_expression,
                expect=expected_value,
                message=message,
            )
        )
        return self

    def assert_is_close(
        self,
        jmespath_expression: Text,
        expected_value: Union[tuple[Number, Number], str],
        message: Text = "",
    ) -> "StepRequestValidation":
        """Return True if the values are close to each other and False otherwise.

        References:
            math.isclose() from https://docs.python.org/3/library/math.html

        :param jmespath_expression: JMESPath search result must be int or float
        :param expected_value: a tuple, the first element is the expected number, the second is the absolute tolerance
        :param message: error message
        """
        self._step_context.validators.append(
            Validator(
                method="is_close",
                expression=jmespath_expression,
                expect=expected_value,
                message=message,
            )
        )
        return self

    def assert_all(
        self,
        jmespath_expression: Text,
        preprocessor: Optional[Union[Callable, str]] = None,
        message: Text = "",
        *,
        preprocessor_kwargs: Optional[dict] = None,
    ):
        """Pass `jmespath_expression` searching result to builtin function `all`.

        If `preprocessor` is callable,
        the jmespath searching result will be pass to the callable as the first positional argument,
        `preprocessor_kwargs` specifies the other arguments,
        and finally the result of the callable will be used as the expected value.

        >>> def iterable_to_bool(iterable: dict, ignored: list):
        ...    return [v is not None for k, v in iterable.items() if v not in ignored]  # noqa
        >>> StepRequestValidation().assert_all("body.result", iterable_to_bool, preprocessor_kwargs={"ignored": ["foo", "bar"]})

        Reference: https://docs.python.org/3/library/functions.html#all
        """
        self._step_context.validators.append(
            Validator(
                method="all_",
                expression=jmespath_expression,
                expect=preprocessor,
                message=message,
                config={"preprocessor_kwargs": preprocessor_kwargs},
            )
        )
        return self

    def assert_match_json_schema(
        self,
        jmespath_expression: Text,
        expected_value: Union[dict, str],
        message: Text = "",
    ) -> "StepRequestValidation":
        """Assert part of response matches the JSON schema.

        >>> schema = {
        ...     "type" : "object",
        ...     "properties" : {
        ...         "price" : {"type" : "number"},
        ...         "name" : {"type" : "string"},
        ...     },
        ... }
        >>> StepRequestValidation().assert_match_json_schema("body.result", schema)
        """
        self._step_context.validators.append(
            Validator(
                method="match_json_schema",
                expression=jmespath_expression,
                expect=expected_value,
                message=message,
            )
        )
        return self

    def assert_match_pydantic_model(
        self,
        jmespath_expression: Text,
        expected_value: Union[Type[BaseModel], str],
        message: Text = "",
    ) -> "StepRequestValidation":
        """Assert part of response matches the pydantic model.

        Note:
            By default extra attributes will be ignored, you can change the behaviour via config `extra`.
            reference: https://docs.pydantic.dev/2.5/api/config/#pydantic.config.ConfigDict.extra

        >>> class Teacher(BaseModel)
        ...     name: str
        ...     age: int
        >>> class Student(BaseModel)
        ...     name: str
        ...     age: int
        ...     teacher: Teacher
        >>> StepRequestValidation().assert_match_pydantic_model("body.result", Student)
        """
        self._step_context.validators.append(
            Validator(
                method="match_pydantic_model",
                expression=jmespath_expression,
                expect=expected_value,
                message=message,
            )
        )
        return self

    def assert_is_truthy(self, jmespath_expression: Text, message: Text = ""):
        """Assert the value is considered true.

        Reference: https://docs.python.org/3/library/stdtypes.html#truth-value-testing
        """
        self._step_context.validators.append(
            Validator(
                method="is_truthy",
                expression=jmespath_expression,
                expect=None,
                message=message,
            )
        )
        return self

    def assert_is_falsy(self, jmespath_expression: Text, message: Text = ""):
        """Assert the value is considered false.

        Reference: https://docs.python.org/3/library/stdtypes.html#truth-value-testing
        """
        self._step_context.validators.append(
            Validator(
                method="is_falsy",
                expression=jmespath_expression,
                expect=None,
                message=message,
            )
        )
        return self

    def assert_is_truthy_and_subset(
        self, jmespath_expression: Text, expected_value: Any, message: Text = ""
    ):
        """Assert actual value is considered true and every element in the actual value is in the expected value."""
        self._step_context.validators.append(
            Validator(
                method="is_truthy_and_subset",
                expression=jmespath_expression,
                expect=expected_value,
                message=message,
            )
        )
        return self

    def assert_is_truthy_and_superset(
        self, jmespath_expression: Text, expected_value: Any, message: Text = ""
    ):
        """Assert actual value is considered true and every element in the expected value is in the actual value."""
        self._step_context.validators.append(
            Validator(
                method="is_truthy_and_superset",
                expression=jmespath_expression,
                expect=expected_value,
                message=message,
            )
        )
        return self

    def assert_lambda(
        self,
        jmespath_expression: Text,
        custom_validator: Union[Callable, str],
        message: Text = "",
        *,
        validator_kwargs: Optional[dict] = None,
    ):
        """Assert with custom validator.

        The `custom_validator` must be a callable and call `assert` to make the assertion,
        the jmespath searching result will be pass to the callable as the first positional argument,
        `validator_kwargs` specifies the other arguments.

        >>> def custom_validator_(response_data: dict, **kwargs):
        ...     assert response_data["foo"] == kwargs["expected_value"]
        >>> StepRequestValidation().assert_lambda(
        ...     "body.result", custom_validator_, validator_kwargs={"expected_value": "bar"})
        """
        self._step_context.validators.append(
            Validator(
                method="assert_lambda",
                expression=jmespath_expression,
                expect=custom_validator,
                message=message,
                config={"validator_kwargs": validator_kwargs},
            )
        )
        return self

    def perform(self) -> TStep:
        return self._step_context
