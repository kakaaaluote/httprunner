from httprunner import HttpRunner, Config, Step, RunRequest


class TestCaseUpdateJson(HttpRunner):

    config = (
        Config("test update json")
        .variables(**{"foo": 1, "bar": 2, "baz": 3})
        .base_url("https://postman-echo.com")
        .verify(False)
    )

    teststeps = [
        Step(
            RunRequest("call once && is_update_before_json = True && both dict")
            .post("/post")
            .with_json({"foo": 3, "baz": "$invalid_var"})
            .update_json_object({"foo": "$foo", "bar": "$bar", "baz": "$baz"})
            .validate()
            .assert_equal("body.json.foo", 1)
            .assert_equal("body.json.bar", 2)
            .assert_equal("body.json.baz", 3)
        ),
        Step(
            RunRequest("call once && is_update_before_json = True && both str")
            .post("/post")
            .with_json("${get_json(1, 2)}")
            .update_json_object("${get_json(3, 4)}", True)
            .validate()
            .assert_equal("body.json.foo", 3)
            .assert_equal("body.json.bar", 4)
        ),
        Step(
            RunRequest("test deep is True")
            .post("/post")
            .with_json({"data": {"foo": 3, "baz": "$baz"}})
            .update_json_object({"data": {"foo": "$foo", "bar": "$bar"}})
            .validate()
            .assert_equal("body.json.data.foo", 1)
            .assert_equal("body.json.data.bar", 2)
            .assert_equal("body.json.data.baz", 3)
        ),
        Step(
            RunRequest("test deep is False")
            .post("/post")
            .with_json({"data": {"foo": 3, "baz": "$baz"}})
            .update_json_object({"data": {"foo": "$foo", "bar": "$bar"}}, False)
            .validate()
            .assert_equal("body.json.data.foo", "$foo")
            .assert_equal("body.json.data.bar", "$bar")
            .assert_equal("body.json.data.baz", None)
        ),
        Step(
            RunRequest("set json and json_update with variable")
            .with_variables(
                **{
                    "init_json": {"data": {"foo": 3, "baz": "$baz"}},
                    "update_json": {"data": {"foo": "$foo", "bar": "$bar"}},
                }
            )
            .post("/post")
            .with_json("$init_json")
            .update_json_object("$update_json", True)
            .validate()
            .assert_equal("body.json.data.foo", 1)
            .assert_equal("body.json.data.bar", 2)
            .assert_equal("body.json.data.baz", 3)
        ),
        Step(
            RunRequest("call twice")
            .post("/post")
            .with_json({"data": {"foo": "$foo"}})
            .update_json_object({"data": {"bar": "$bar"}})
            .update_json_object({"data": {"baz": "$baz"}})
            .validate()
            .assert_equal("body.json.data.foo", 1)
            .assert_equal("body.json.data.bar", 2)
            .assert_equal("body.json.data.baz", 3)
        ),
    ]


if __name__ == "__main__":
    TestCaseUpdateJson().test_start()
