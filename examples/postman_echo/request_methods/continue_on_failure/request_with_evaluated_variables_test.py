# NOTE: Generated By HttpRunner v3.1.4
# FROM: request_methods/request_with_variables.yml


import pytest

from httprunner import HttpRunner, Config, Step, RunRequest
from httprunner.exceptions import ValidationFailure


@pytest.mark.xfail(raises=ValidationFailure)
class TestCaseRequestWithVariables(HttpRunner):

    config = (
        Config("request methods testcase with variables")
        .variables(**{"foo1": "testcase_config_bar1", "foo2": "testcase_config_bar2"})
        .base_url("https://postman-echo.com")
        .verify(False)
        .continue_on_failure()
    )

    teststeps = [
        Step(
            RunRequest("evaluate variable")
            .with_variables(
                **{
                    "func": "${get_raw_func()}",
                }
            )
            .post("/post")
            .with_json({"value": "${eval_var($func)}"})
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.data.value", [2, 1])
        ),
    ]


if __name__ == "__main__":
    TestCaseRequestWithVariables().test_start()
