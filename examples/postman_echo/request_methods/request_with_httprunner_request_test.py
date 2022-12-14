# NOTE: Generated By HttpRunner v3.1.4
# FROM: request_methods/request_with_variables.yml


from httprunner import HttpRunner, Config, Step, RunRequest
from httprunner.testcase import HttpRunnerRequest, RequestConfig


class PostmanEchoPost(HttpRunnerRequest):
    config = RequestConfig("default name").variables(
        **{
            "foo": "request_config_foo",
            "bar": "request_config_bar",
            "qux": "request_config_qux",
            "fred": "request_config_fred",
        }
    )
    request = (
        RunRequest("")
        .with_variables(**{"foo": "step_init_foo", "bar": "step_init_bar"})
        .post("/post")
        .with_headers(**{"User-Agent": "HttpRunner/3.0", "Content-Type": "text/plain"})
        .with_data("$foo-$bar")
    )


class TestCaseRequestWithHttpRunnerRequest(HttpRunner):
    """
    variables priority:
        step append vars > step init vars > extract vars > testcase config vars > request config vars
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
            PostmanEchoPost("step append vars > step init vars")
            .with_variables(**{"foo": "step_append_foo", "bar": "step_append_bar"})
            .with_data("$foo-$bar")
            .validate()
            .assert_equal(
                "body.data",
                "step_append_foo-step_append_bar",
            )
        ),
        Step(
            RunRequest("extract variables")
            .get("/get")
            .with_params(
                **{"foo": "extract_foo", "bar": "extract_bar", "baz": "extract_baz"}
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
            PostmanEchoPost("step init vars > extract vars")
            .with_data("$foo-$bar")
            .validate()
            .assert_equal(
                "body.data",
                "step_init_foo-step_init_bar",
            )
        ),
        Step(
            PostmanEchoPost("extract vars > testcase config vars")
            .with_data("$foo-$bar-$baz")
            .validate()
            .assert_equal(
                "body.data",
                "step_init_foo-step_init_bar-extract_baz",
            )
        ),
        Step(
            PostmanEchoPost("testcase config vars > request config vars")
            .with_data("$foo-$bar-$baz-$qux")
            .validate()
            .assert_equal(
                "body.data",
                "step_init_foo-step_init_bar-extract_baz-testcase_config_qux",
            )
        ),
        Step(
            PostmanEchoPost("merge request config vars")
            .with_data("$foo-$bar-$baz-$qux-$fred")
            .validate()
            .assert_equal(
                "body.data",
                "step_init_foo-step_init_bar-extract_baz-testcase_config_qux-request_config_fred",
            )
        ),
    ]


class PostmanEchoPostWithExtractAndValidators(HttpRunnerRequest):
    config = RequestConfig("default name").variables(
        **{
            "foo": "request_config_foo",
            "bar": "request_config_bar",
            "qux": "request_config_qux",
            "fred": "request_config_fred",
        }
    )
    request = (
        RunRequest("")
        .with_variables(**{"foo": "step_init_foo", "bar": "step_init_bar"})
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
