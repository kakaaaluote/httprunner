# NOTE: Generated By HttpRunner v3.1.4
# FROM: request_methods/request_with_variables.yml
from dotwiz import DotWiz

from httprunner import HttpRunner, Config, Step, RunRequest


class TestCaseRequestWithVariables(HttpRunner):

    config = (
        Config("request methods testcase with variables")
        .variables(**{"foo1": "testcase_config_bar1", "foo2": "testcase_config_bar2"})
        .base_url("https://postman-echo.com")
        .verify(False)
    )

    teststeps = [
        Step(
            RunRequest("get with params")
            .with_variables(**{"foo1": "bar11", "foo2": "bar21"})
            .get("/get")
            .with_params(**{"foo1": "$foo1", "foo2": "$foo2"})
            .with_headers(**{"User-Agent": "HttpRunner/3.0"})
            .extract()
            .with_jmespath("body.args.foo2", "foo3")
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.args.foo1", "bar11")
            .assert_equal("body.args.foo2", "bar21")
        ),
        Step(
            RunRequest("post raw text")
            .with_variables(**{"foo1": "bar12", "foo3": "bar32"})
            .post("/post")
            .with_headers(
                **{"User-Agent": "HttpRunner/3.0", "Content-Type": "text/plain"}
            )
            .with_data(
                "This is expected to be sent back as part of response body: $foo1-$foo2-$foo3."
            )
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal(
                "body.data",
                "This is expected to be sent back as part of response body: bar12-testcase_config_bar2-bar32.",
            )
        ),
        Step(
            RunRequest("post form data")
            .with_variables(**{"foo2": "bar23"})
            .post("/post")
            .with_headers(
                **{
                    "User-Agent": "HttpRunner/3.0",
                    "Content-Type": "application/x-www-form-urlencoded",
                }
            )
            .with_data("foo1=$foo1&foo2=$foo2&foo3=$foo3")
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.form.foo1", "testcase_config_bar1")
            .assert_equal("body.form.foo2", "bar23")
            .assert_equal("body.form.foo3", "bar21")
        ),
        Step(
            RunRequest("post form data using json")
            .with_variables(
                **{
                    "foo2": "bar23",
                    "jsondata": {"foo1": "$foo1", "foo2": "$foo2", "foo3": "$foo3"},
                }
            )
            .post("/post")
            .with_headers(
                **{"User-Agent": "HttpRunner/3.0", "Content-Type": "application/json"}
            )
            .with_json("$jsondata")
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.data.foo1", "testcase_config_bar1")
            .assert_equal("body.data.foo2", "bar23")
            .assert_equal("body.data.foo3", "bar21")
        ),
        Step(
            RunRequest(
                "variable contains DotDict and accessing/changing 'attribute' with dot"
            )
            .with_variables(
                **{
                    "foo": DotWiz({"a": {"b": {"c": 1}}}),
                    "bar": DotWiz({"a": 1}),
                    "no_return": "${pyexp(setattr(bar, 'a', 2))}",
                }
            )
            .post("/post")
            .with_headers(
                **{"User-Agent": "HttpRunner/3.0", "Content-Type": "application/json"}
            )
            .with_json(
                {
                    "foo": "${pyexp(foo.to_dict())}",
                    "bar": "${pyexp(bar.to_dict())}",
                    "baz": "$foo"
                }
            )
            .export()
            .variable("foo")
            .validate()
            .assert_equal("status_code", 200)
            .assert_equal("body.json.foo.a.b.c", "${foo.a.b.c}")
            .assert_equal("body.json.baz.a.b.c", "${foo.a.b.c}")
            .assert_equal("body.json.bar.a", 2)
        ),
    ]


if __name__ == "__main__":
    TestCaseRequestWithVariables().test_start()
