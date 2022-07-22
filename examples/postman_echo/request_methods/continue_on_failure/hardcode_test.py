# NOTE: Generated By HttpRunner v3.1.4
# FROM: request_methods/hardcode.yml

import pytest

from httprunner import HttpRunner, Config, Step, RunRequest
from httprunner.exceptions import ValidationFailure


@pytest.mark.xfail(raises=ValidationFailure)
class TestCaseHardcode(HttpRunner):

    config = (
        Config("request methods testcase in hardcode")
        .base_url("https://postman-echo.com")
        .verify(False)
        .continue_on_failure()
    )

    teststeps = [
        Step(
            RunRequest("get with params")
            .get("/get")
            .with_params(**{"foo1": "bar1", "foo2": "bar2"})
            .with_headers(**{"User-Agent": "HttpRunner/3.0"})
            .validate()
            .assert_equal("status_code", 100)
        ),
        Step(
            RunRequest("post raw text")
            .post("/post")
            .with_headers(
                **{"User-Agent": "HttpRunner/3.0", "Content-Type": "text/plain"}
            )
            .with_data("This is expected to be sent back as part of response body.")
            .validate()
            .assert_equal("status_code", 100)
        ),
        Step(
            RunRequest("post form data")
            .post("/post")
            .with_headers(
                **{
                    "User-Agent": "HttpRunner/3.0",
                    "Content-Type": "application/x-www-form-urlencoded",
                }
            )
            .with_data("foo1=bar1&foo2=bar2")
            .validate()
            .assert_equal("status_code", 100)
        ),
        Step(
            RunRequest("put request")
            .put("/put")
            .with_headers(
                **{"User-Agent": "HttpRunner/3.0", "Content-Type": "text/plain"}
            )
            .with_data("This is expected to be sent back as part of response body.")
            .validate()
            .assert_equal("status_code", 100)
        ),
    ]


if __name__ == "__main__":
    TestCaseHardcode().test_start()
