from httprunner import HttpRunner, Config, Step, RunRequest
from httprunner.testcase import HttpRunnerRequest, RequestConfig


class PostmanEchoPost(HttpRunnerRequest):
    config = RequestConfig("default name").variables(
        **{
            "foo": "builtin_config_foo",
            "bar": "builtin_config_bar",
            "baz": "builtin_config_baz",
            "qux": "builtin_config_qux",
            "fred": "builtin_config_fred",
        }
    )
    request = (
        RunRequest("")
        .with_variables(
            **{
                "foo": "builtin_request_foo",
            }
        )
        .post("/post")
        .with_headers(**{"User-Agent": "HttpRunner/3.0", "Content-Type": "text/plain"})
        .with_data("$foo-$bar")
    )


class TestVariablePriority(HttpRunner):
    """
    variables priority:
        private vars > step.with_variables > extracted vars > testcase config vars > request config vars
    """

    config = (
        Config("test variables priority")
        .variables(
            **{
                "foo": "testcase_config_foo",
                "bar": "testcase_config_bar",
                "baz": "testcase_config_baz",
                "qux": "testcase_config_qux",
            }
        )
        .base_url("https://postman-echo.com")
        .verify(False)
    )

    teststeps = [
        Step(PostmanEchoPost()),  # test default name from config
        Step(
            RunRequest("extract variables")
            .get("/get")
            .with_params(
                **{
                    "foo": "extract_foo",
                    "bar": "extract_bar",
                    "baz": "extract_baz",
                }
            )
            .with_headers(**{"User-Agent": "HttpRunner/3.0"})
            .extract()
            .with_jmespath("body.args.foo", "foo")
            .with_jmespath("body.args.bar", "bar")
            .with_jmespath("body.args.baz", "baz")
            .validate()
            .assert_equal("status_code", 200)
        ),
        Step(
            PostmanEchoPost(
                "builtin request vars > step.with_variables > extracted vars > testcase config vars "
                "> builtin config vars"
            )
            .with_variables(
                **{
                    "foo": "step.with_variables_foo",
                    "bar": "step.with_variables_bar",
                }
            )
            .with_data("$foo-$bar-$baz-$qux-$fred")
            .validate()
            .assert_equal(
                "body.data",
                "builtin_request_foo-step.with_variables_bar-extract_baz-testcase_config_qux-builtin_config_fred",
            )
        ),
    ]


class PostmanEchoPostWithExtractAndValidators(HttpRunnerRequest):
    config = RequestConfig("default name").variables(
        **{
            "foo": "builtin_config_foo",
            "bar": "builtin_config_bar",
            "qux": "builtin_config_qux",
            "fred": "builtin_config_fred",
        }
    )
    request = (
        RunRequest("")
        .post("/post")
        .with_headers(**{"User-Agent": "HttpRunner/3.0", "Content-Type": "text/plain"})
        .with_data("$foo-$bar")
        .extract()
        .with_jmespath("[?bad-expression", "wont-export")
        .validate()
        .assert_equal("status_code", 204)
    )


class TestCaseRequestWithHttpRunnerRequestAndClear(HttpRunner):

    config = (
        Config("test clear")
        .variables(
            **{
                "foo": "testcase_config_foo",
                "bar": "testcase_config_bar",
                "baz": "testcase_config_baz",
                "qux": "testcase_config_qux",
            }
        )
        .base_url("https://postman-echo.com")
        .verify(False)
    )

    teststeps = [
        Step(
            PostmanEchoPostWithExtractAndValidators("test clear")
            .with_variables(**{"foo": "step_append_foo", "bar": "step_append_bar"})
            .with_data("$foo-$bar")
            .extract()
            .clear()
            .validate()
            .clear()
            .assert_equal(
                "body.data",
                "step_append_foo-step_append_bar",
            )
        ),
    ]


class PostmanEchoPostWithNestedVars(HttpRunnerRequest):
    config = RequestConfig("default name").variables(
        **{
            "foo": "builtin_config_foo",
            "bar": "builtin_config_bar",
            "qux": "builtin_config_qux",
            "fred": "builtin_config_fred",
            "user": {"account_id": "$account_id", "token": "$token"},
        }
    )
    request = (
        RunRequest("")
        .with_variables(
            **{
                "foo": "builtin_request_foo",
                "bar": "builtin_request_bar",
                "account_id": "${user['account_id']}",
                "token": "${user['token']}",
            }
        )
        .post("/post")
        .with_headers(**{"User-Agent": "HttpRunner/3.0"})
        .with_json(
            {
                "foo": "$foo",
                "bar": "$bar",
                "account_id": "$account_id",
                "token": "$token",
            }
        )
        .validate()
        .assert_equal("status_code", 200)
    )


class TestCaseRequestWithHttpRunnerRequestWithNestedVariableUser(HttpRunner):

    config = (
        Config("test nested variable user")
        .variables(
            **{
                "foo": "testcase_config_foo",
                "bar": "testcase_config_bar",
                "baz": "testcase_config_baz",
                "qux": "testcase_config_qux",
                "user": {"account_id": 1, "token": "some-token"},
            }
        )
        .base_url("https://postman-echo.com")
        .verify(False)
    )

    teststeps = [
        Step(
            PostmanEchoPostWithNestedVars("test clear")
            .with_variables(**{"foo": "step_append_foo", "bar": "step_append_bar"})
            .validate()
            .assert_equal("body.json.account_id", 1)
            .assert_equal("body.json.token", "some-token")
        ),
    ]


class TestCaseRequestWithHttpRunnerRequestWithNestedVariableUserParts(HttpRunner):

    config = (
        Config("test nested variable user")
        .variables(
            **{
                "foo": "testcase_config_foo",
                "bar": "testcase_config_bar",
                "baz": "testcase_config_baz",
                "qux": "testcase_config_qux",
                "account_id": 1,
                "token": "some-token",
            }
        )
        .base_url("https://postman-echo.com")
        .verify(False)
    )

    teststeps = [
        Step(
            PostmanEchoPostWithNestedVars("test clear")
            .with_variables(**{"foo": "step_append_foo", "bar": "step_append_bar"})
            .validate()
            .assert_equal("body.json.account_id", 1)
            .assert_equal("body.json.token", "some-token")
        ),
    ]
