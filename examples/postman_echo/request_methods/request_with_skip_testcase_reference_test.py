# NOTE: Generated By HttpRunner v3.1.4
# FROM: request_methods/request_with_testcase_reference.yml


import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


from httprunner import HttpRunner, Config, Step, RunRequest, RunTestCase

from request_methods.request_with_functions_test import (
    TestCaseRequestWithFunctions as RequestWithFunctions,
)


class TestCaseRequestWithSkipTestcaseReference(HttpRunner):

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
    )

    teststeps = [
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
            .with_data("foo1=$foo1")
            .extract()
            .with_jmespath("status_code", "status_code")
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            RunTestCase("skip with skip_if")
            .skip_if("$status_code==200")
            .with_variables(**{"expect_foo1": "testsuite_config_bar1"})
            .setup_hook("${sleep(0.1)}")
            .call(RequestWithFunctions)
            .teardown_hook("${sleep(0.2)}")
            .export(*["foo3"])
        ),
        Step(
            RunTestCase("run with skip_if")
            .skip_if("$status_code!=200")
            .with_variables(**{"expect_foo1": "testsuite_config_bar1"})
            .setup_hook("${sleep(0.1)}")
            .call(RequestWithFunctions)
            .teardown_hook("${sleep(0.2)}")
            .export(*["foo3"])
        ),
        Step(
            RunTestCase("skip with skip_unless")
            .skip_unless("$status_code!=200")
            .with_variables(**{"expect_foo1": "testsuite_config_bar1"})
            .setup_hook("${sleep(0.1)}")
            .call(RequestWithFunctions)
            .teardown_hook("${sleep(0.2)}")
            .export(*["foo3"])
        ),
        Step(
            RunTestCase("run with skip_unless")
            .skip_unless("$status_code==200")
            .with_variables(**{"expect_foo1": "testsuite_config_bar1"})
            .setup_hook("${sleep(0.1)}")
            .call(RequestWithFunctions)
            .teardown_hook("${sleep(0.2)}")
            .export(*["foo3"])
        ),
    ]


if __name__ == "__main__":
    TestCaseRequestWithSkipTestcaseReference().test_start()
