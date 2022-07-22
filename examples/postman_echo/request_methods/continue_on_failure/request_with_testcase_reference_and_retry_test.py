# NOTE: Generated By HttpRunner v3.1.4
# FROM: request_methods/request_with_testcase_reference.yml


import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


from httprunner import HttpRunner, Config, Step, RunRequest, RunTestCase

from .request_with_retry_test import (
    TestCaseRequestWithRetry as RequestWithRetry,
)


import pytest
from httprunner.exceptions import ValidationFailure


@pytest.mark.xfail(raises=ValidationFailure)
class TestCaseRequestWithTestcaseReferenceAndRetry(HttpRunner):

    config = (
        Config("request methods testcase: reference testcase")
        .variables(
            **{
                "foo1": "testsuite_config_bar1",
                "expect_foo1": "testsuite_config_bar1",
                "expect_foo2": "config_bar2",
            }
        )
        .base_url("https://postman-echo.com")
        .verify(False)
        .continue_on_failure()
    )

    teststeps = [
        Step(
            RunTestCase("request with functions")
            .with_variables(
                **{"foo1": "testcase_ref_bar1", "expect_foo1": "testcase_ref_bar1"}
            )
            .setup_hook("${sleep(0.1)}")
            .call(RequestWithRetry)
            .teardown_hook("${sleep(0.2)}")
            .export(*["foo3"])
        ),
        Step(
            RunRequest("post form data")
            .with_variables(**{"foo1": "bar1"})
            .post("/post")
            .with_headers(
                **{
                    "User-Agent": "HttpRunner/${get_httprunner_version()}",
                    "Content-Type": "application/x-www-form-urlencoded",
                }
            )
            .with_data("foo1=$foo1&foo2=$foo3")
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.form.foo1", "bad")
            .assert_equal("body.form.foo2", "bar21")
        ),
    ]


if __name__ == "__main__":
    TestCaseRequestWithTestcaseReferenceAndRetry().test_start()
