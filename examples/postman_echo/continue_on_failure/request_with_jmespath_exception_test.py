# NOTE: Generated By HttpRunner v3.1.4
# FROM: request_methods/request_with_variables.yml
import pytest

from httprunner import HttpRunner, Config, Step, RunRequest
from httprunner.exceptions import MultiStepsFailedError


@pytest.mark.xfail(raises=MultiStepsFailedError)
class TestJMESPathException(HttpRunner):

    config = (
        Config("continue on JMESPath exception")
        .variables(**{"foo1": "testcase_config_bar1", "foo2": "testcase_config_bar2"})
        .base_url("https://postman-echo.com")
        .verify(False)
        .continue_on_failure()
    )

    teststeps = [
        Step(
            RunRequest("raise JMESPath exception")
            .with_variables(**{"foo1": "bar11", "foo2": "bar21"})
            .get("/get")
            .with_params(**{"foo1": "$foo1", "foo2": "$foo2"})
            .with_headers(**{"User-Agent": "HttpRunner/3.0"})
            .extract()
            .with_jmespath("body.args.foo2", "foo3")
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("length(body.args.foo1.non_exist)", 1)
        ),
        Step(
            RunRequest("pass this step")
            .with_variables(**{"foo1": "bar11", "foo2": "bar21"})
            .get("/get")
            .with_params(**{"foo1": "$foo1", "foo2": "$foo2"})
            .with_headers(**{"User-Agent": "HttpRunner/3.0"})
            .extract()
            .with_jmespath("body.args.foo2", "foo3")
            .validate()
            .assert_equal("status_code", 200)
        ),
    ]