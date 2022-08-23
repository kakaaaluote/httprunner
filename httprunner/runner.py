import json
import os
import time
import uuid
from datetime import datetime
from typing import List, Dict, Text, NoReturn

from httprunner.builtin import expand_nested_json

try:
    import allure

    USE_ALLURE = True
except ModuleNotFoundError:
    USE_ALLURE = False

from loguru import logger

from httprunner import utils, exceptions
from httprunner.client import HttpSession
from httprunner.exceptions import ValidationFailure, ParamsError
from httprunner.ext.uploader import prepare_upload_step
from httprunner.loader import load_project_meta, load_testcase_file
from httprunner.parser import (
    build_url,
    parse_data,
    parse_variables_mapping,
    update_url_origin,
)
from httprunner.response import ResponseObject
from httprunner.testcase import Config, Step
from httprunner.utils import merge_variables
from httprunner.models import (
    TConfig,
    TStep,
    VariablesMapping,
    StepData,
    TestCaseSummary,
    TestCaseTime,
    TestCaseInOut,
    ProjectMeta,
    TestCase,
    Hooks,
    SessionData,
)


class HttpRunner(object):
    config: Config
    teststeps: List[Step]

    success: bool = False  # indicate testcase execution result
    __config: TConfig
    __teststeps: List[TStep]
    __project_meta: ProjectMeta = None
    __case_id: Text = ""
    __export: List[Text] = []
    __step_datas: List[StepData] = []
    __session: HttpSession = None
    __session_variables: VariablesMapping = {}
    # time
    __start_at: float = 0
    __duration: float = 0
    # log
    __log_path: Text = ""
    __continue_on_failure: bool = False

    def __init_tests__(self) -> NoReturn:
        self.__config = self.config.perform()
        self.__teststeps = []
        for step in self.teststeps:
            self.__teststeps.append(step.perform())
        self.__failed_steps: list[TStep] = []

    @property
    def raw_testcase(self) -> TestCase:
        if not hasattr(self, "__config"):
            self.__init_tests__()

        return TestCase(config=self.__config, teststeps=self.__teststeps)

    def with_project_meta(self, project_meta: ProjectMeta) -> "HttpRunner":
        self.__project_meta = project_meta
        return self

    def with_session(self, session: HttpSession) -> "HttpRunner":
        self.__session = session
        return self

    def with_case_id(self, case_id: Text) -> "HttpRunner":
        self.__case_id = case_id
        return self

    def with_variables(self, variables: VariablesMapping) -> "HttpRunner":
        self.__session_variables = variables
        return self

    def set_continue_on_failure(self, is_continue_on_failure: bool) -> "HttpRunner":
        self.__continue_on_failure = is_continue_on_failure
        return self

    def with_export(self, export: List[Text]) -> "HttpRunner":
        self.__export = export
        return self

    def __call_hooks(
        self,
        hooks: Hooks,
        step_variables: VariablesMapping,
        hook_msg: Text,
    ) -> NoReturn:
        """call hook actions.

        Args:
            hooks (list): each hook in hooks list maybe in two format.

                format1 (str): only call hook functions.
                    ${func()}
                format2 (dict): assignment, the value returned by hook function will be assigned to variable.
                    {"var": "${func()}"}

            step_variables: current step variables to call hook, include two special variables

                request: parsed request dict
                response: ResponseObject for current response

            hook_msg: setup/teardown request/testcase

        """
        logger.info(f"call hook actions: {hook_msg}")

        if not isinstance(hooks, List):
            logger.error(f"Invalid hooks format: {hooks}")
            return

        for hook in hooks:
            if isinstance(hook, Text):
                # format 1: ["${func()}"]
                logger.debug(f"call hook function: {hook}")
                parse_data(hook, step_variables, self.__project_meta.functions)
            elif isinstance(hook, Dict) and len(hook) == 1:
                # format 2: {"var": "${func()}"}
                var_name, hook_content = list(hook.items())[0]
                hook_content_eval = parse_data(
                    hook_content, step_variables, self.__project_meta.functions
                )
                logger.debug(
                    f"call hook function: {hook_content}, got value: {hook_content_eval}"
                )
                logger.debug(f"assign variable: {var_name} = {hook_content_eval}")
                step_variables[var_name] = hook_content_eval
            else:
                logger.error(f"Invalid hook format: {hook}")

    def __add_allure_attachments(
        self,
        session_data: SessionData,
        validation_results: dict,
        exported_vars: dict,
        is_success: bool,
    ) -> NoReturn:
        """
        Add attachments to allure.
        """
        # split session data into request, response, validation results, export vars, and stat
        # if only one request exists
        if len(session_data.req_resps) == 1:
            if is_success:
                result = "PASS"
            else:
                result = "FAIL"

            request_data = session_data.req_resps[0].request
            response_data = session_data.req_resps[0].response
            # save request data
            allure.attach(
                request_data.json(indent=4, ensure_ascii=False),
                "request",
                allure.attachment_type.JSON,
            )
            # save response data
            allure.attach(
                response_data.json(indent=4, ensure_ascii=False),
                "response",
                allure.attachment_type.JSON,
            )
            # save validation results
            allure.attach(
                json.dumps(
                    validation_results.get("validate_extractor", []),
                    indent=4,
                    ensure_ascii=False,
                ),
                f"validation results ({result})",
                allure.attachment_type.JSON,
            )
            # save export vars
            allure.attach(
                json.dumps(exported_vars, indent=4, ensure_ascii=False),
                "exported variables",
                allure.attachment_type.JSON,
            )
            # save stat
            allure.attach(
                session_data.stat.json(indent=4, ensure_ascii=False),
                "statistics",
                allure.attachment_type.JSON,
            )
        else:
            # put request, response, and validation results in one attachment
            allure.attach(
                self.__session.data.json(indent=4, ensure_ascii=False),
                "session data",
                allure.attachment_type.JSON,
            )
            # save export vars
            allure.attach(
                json.dumps(exported_vars, indent=4, ensure_ascii=False),
                "exported variables",
                allure.attachment_type.JSON,
            )

    def __save_allure_data(
        self,
        validation_results: dict,
        exported_vars: dict,
        max_retries: int,
        remaining_retry_times: int,
        is_success: bool,
    ) -> NoReturn:
        """
        Save session data as allure raw data after validation completed.

        Note:
            1. this function is exclusively used for method self.__run_step_request().
            2. if retry is needed (max_retries > 0), add new step as context
        """
        if not hasattr(self.__session, "data"):
            return

        if max_retries > 0:
            if is_success:
                result = "PASS"
            else:
                result = "FAIL"

            if max_retries == remaining_retry_times:
                title = f"first request ({result})"
            elif remaining_retry_times == 0:
                title = f"retry: {max_retries} - last retry ({result})"
            else:
                title = f"retry: {max_retries - remaining_retry_times} ({result})"
            with allure.step(title):
                self.__add_allure_attachments(
                    self.__session.data, validation_results, exported_vars, is_success
                )
        else:
            self.__add_allure_attachments(
                self.__session.data, validation_results, exported_vars, is_success
            )

    def __run_step_request(self, step: TStep) -> StepData:
        """run teststep: request"""
        step_data = StepData(name=step.name)

        # parse
        prepare_upload_step(step, self.__project_meta.functions)
        request_dict = step.request.dict()
        request_dict.pop("upload", None)
        parsed_request_dict = parse_data(
            request_dict, step.variables, self.__project_meta.functions
        )
        parsed_request_dict["headers"].setdefault(
            "HRUN-Request-ID",
            f"HRUN-{self.__case_id}-{str(int(time.time() * 1000))[-6:]}",
        )
        step.variables["request"] = parsed_request_dict
        step.variables["session"] = self.__session

        # setup hooks
        if step.setup_hooks:
            self.__call_hooks(step.setup_hooks, step.variables, "setup request")

        # prepare arguments
        method = parsed_request_dict.pop("method")
        url_path = parsed_request_dict.pop("url")
        url = build_url(self.__config.base_url, url_path)

        # substitute origin if request.origin is not None
        if origin := parsed_request_dict.pop("origin"):
            url = update_url_origin(url, origin)

        parsed_request_dict["verify"] = self.__config.verify
        parsed_request_dict["json"] = parsed_request_dict.pop("req_json", {})

        # request
        resp = self.__session.request(method, url, **parsed_request_dict)
        resp_obj = ResponseObject(resp)

        # expand nested json if headers contain 'X-Json-Control' and its value is 'expand'
        if parsed_request_dict["headers"].get("X-Json-Control") == "expand":
            expand_nested_json(resp_obj.body)

        step.variables["response"] = resp_obj

        # teardown hooks
        if step.teardown_hooks:
            self.__call_hooks(step.teardown_hooks, step.variables, "teardown request")

        def log_req_resp_details():
            err_msg = "\n{} DETAILED REQUEST & RESPONSE {}\n".format("*" * 32, "*" * 32)

            # log request
            err_msg += "====== request details ======\n"
            err_msg += f"url: {url}\n"
            err_msg += f"method: {method}\n"
            headers = parsed_request_dict.pop("headers", {})
            err_msg += f"headers: {headers}\n"
            for k, v in parsed_request_dict.items():
                v = utils.omit_long_data(v)
                err_msg += f"{k}: {repr(v)}\n"

            err_msg += "\n"

            # log response
            err_msg += "====== response details ======\n"
            err_msg += f"status_code: {resp.status_code}\n"
            err_msg += f"headers: {resp.headers}\n"
            err_msg += f"body: {repr(resp.text)}\n"
            logger.error(err_msg)

        # extract
        extractors: dict = step.extract

        # parse JMESPath
        # note: do not change variable 'extractors' directly to reduce surprise
        parsed_extractors = {}
        for var_name, jmespath in extractors.items():
            if "$" in jmespath:
                parsed_extractors[var_name] = parse_data(
                    jmespath, step.variables, self.__project_meta.functions
                )
            else:
                parsed_extractors[var_name] = jmespath

        extract_mapping = resp_obj.extract(parsed_extractors)
        step_data.export_vars = extract_mapping

        variables_mapping = step.variables
        variables_mapping.update(extract_mapping)

        # added by @deng at 2022.2.9
        export_mapping = {}
        # export local variables to make them usable for steps next
        for var in step.globalize:
            if isinstance(var, dict):
                if len(var) != 1:
                    raise ValueError(
                        f"length of dict can only be 1 but got {len(var)} for: {var}"
                    )
                local_var_name = list(var.keys())[0]
                export_as = list(var.values())[0]
            else:
                if not isinstance(var, str) or not var:
                    raise ValueError(
                        "type of var can only be dict or str, and must not be empty"
                    )
                local_var_name = var
                export_as = var

            # cannot export variables extracted
            if local_var_name in extract_mapping:
                raise ValueError(
                    f"cannot export variable {local_var_name} which is extracted from response"
                )

            if local_var_name not in variables_mapping:
                raise ValueError(
                    f"failed to export local step variable {local_var_name}, "
                    f"all step variables now: {variables_mapping}"
                )

            export_mapping[export_as] = variables_mapping[local_var_name]

        # extracted variables > local variables
        step_data.export_vars = merge_variables(step_data.export_vars, export_mapping)

        # validate
        validators = step.validators
        self.__session.data.success = (
            False  # default to False, re-assign it to make it more explicit
        )

        try:
            resp_obj.validate(
                validators, variables_mapping, self.__project_meta.functions
            )
            self.__session.data.validators = resp_obj.validation_results
            self.__session.data.success = True  # validate success
            self.__save_allure_data(
                resp_obj.validation_results,
                step_data.export_vars,
                step.max_retry_times,
                step.retry_times,
                self.__session.data.success,
            )
        except ValidationFailure as vf:
            self.__save_allure_data(
                resp_obj.validation_results,
                step_data.export_vars,
                step.max_retry_times,
                step.retry_times,
                self.__session.data.success,
            )
            self.__session.data.validators = resp_obj.validation_results
            # check if retry is needed
            if step.retry_times > 0:
                logger.warning(
                    f"step '{step.name}' validation failed, wait {step.retry_interval} seconds and try again"
                )
                step.retry_times -= 1
                time.sleep(step.retry_interval)
                step_data = self.__run_step_request(step)
                return step_data

            self.__failed_steps.append(step)
            log_req_resp_details()

            # log testcase duration before raise ValidationFailure
            self.__duration = time.time() - self.__start_at

            if self.__continue_on_failure:
                self.__session.data.exception = vf
            else:
                raise
        finally:
            if hasattr(self, "__failed_steps") and self.__failed_steps:
                self.success = False
            else:
                self.success = True

            step_data.success = self.__session.data.success

            if hasattr(self.__session, "data"):
                # httprunner.client.HttpSession, not locust.clients.HttpSession
                # save step data
                step_data.data = self.__session.data

        return step_data

    def __run_step_testcase(self, step: TStep) -> StepData:
        """run teststep: referenced testcase"""
        step_data = StepData(name=step.name)
        step_variables = step.variables
        step_export = step.export

        # setup hooks
        if step.setup_hooks:
            self.__call_hooks(step.setup_hooks, step_variables, "setup testcase")

        if hasattr(step.testcase, "config") and hasattr(step.testcase, "teststeps"):
            testcase_cls = step.testcase
            case_result = (
                testcase_cls()
                .set_continue_on_failure(self.__continue_on_failure)
                .with_session(self.__session)
                .with_case_id(self.__case_id)
                .with_variables(step_variables)
                .with_export(step_export)
                .run()
            )

        elif isinstance(step.testcase, Text):
            if os.path.isabs(step.testcase):
                ref_testcase_path = step.testcase
            else:
                ref_testcase_path = os.path.join(
                    self.__project_meta.RootDir, step.testcase
                )

            case_result = (
                HttpRunner()
                .set_continue_on_failure(self.__continue_on_failure)
                .with_session(self.__session)
                .with_case_id(self.__case_id)
                .with_variables(step_variables)
                .with_export(step_export)
                .run_path(ref_testcase_path)
            )

        else:
            raise exceptions.ParamsError(
                f"Invalid teststep referenced testcase: {step.dict()}"
            )

        # teardown hooks
        if step.teardown_hooks:
            self.__call_hooks(step.teardown_hooks, step.variables, "teardown testcase")

        step_data.data = case_result.get_step_datas()  # list of step data
        step_data.export_vars = case_result.get_export_variables()

        if case_result.get_failed_steps():
            step_data.success = False
            self.__failed_steps.append(step)
        else:
            step_data.success = True

        if self.__failed_steps:
            self.success = False
        else:
            self.success = True

        if step_data.export_vars:
            logger.info(f"export variables: {step_data.export_vars}")

        return step_data

    def __run_step(self, step: TStep) -> Dict:
        """run teststep, teststep maybe a request or referenced testcase"""
        is_skip_step = False
        logger.info(f"run step begin: {step.name} >>>>>>")
        step_data = StepData(name=step.name)

        # handle skip_if
        if step.skip_on_condition:
            parsed_skip_condition = parse_data(
                step.skip_on_condition, step.variables, self.__project_meta.functions
            )
            logger.debug(
                f"parsed skip condition: {parsed_skip_condition} ({type(parsed_skip_condition)})"
            )

            # eval again if type is str
            if isinstance(parsed_skip_condition, str):
                parsed_skip_condition = eval(parsed_skip_condition)

            if parsed_skip_condition:
                is_skip_step = True
                parsed_skip_reason = parse_data(
                    step.skip_reason, step.variables, self.__project_meta.functions
                )
                logger.info(f"skip condition was met, reason: {parsed_skip_reason}")

                # mark skipped step as success
                step_data.success = True
            else:
                logger.info("skip condition was not met, run the step")

        # handle skip_unless
        if step.run_on_condition:
            parsed_run_condition = parse_data(
                step.run_on_condition, step.variables, self.__project_meta.functions
            )
            logger.debug(
                f"parsed run condition: {parsed_run_condition} ({type(parsed_run_condition)})"
            )

            # eval again if type is str
            if isinstance(parsed_run_condition, str):
                parsed_run_condition = eval(parsed_run_condition)

            if not parsed_run_condition:
                is_skip_step = True
                parsed_skip_reason = parse_data(
                    step.skip_reason, step.variables, self.__project_meta.functions
                )
                logger.info(f"skip condition was met, reason: {parsed_skip_reason}")

                # mark skipped step as success
                step_data.success = True
            else:
                logger.info("run condition was met, run the step")

        if not is_skip_step:
            if step.request:
                step_data = self.__run_step_request(step)
            elif step.testcase:
                step_data = self.__run_step_testcase(step)
            else:
                raise ParamsError(
                    f"teststep is neither a request nor a referenced testcase: {step.dict()}"
                )

        self.__step_datas.append(step_data)
        logger.info(f"run step end: {step.name} <<<<<<\n")
        return step_data.export_vars

    def __parse_config(self, config: TConfig) -> NoReturn:
        config.variables.update(self.__session_variables)
        config.variables = parse_variables_mapping(
            config.variables, self.__project_meta.functions
        )
        config.name = parse_data(
            config.name, config.variables, self.__project_meta.functions
        )
        config.base_url = parse_data(
            config.base_url, config.variables, self.__project_meta.functions
        )

    def run_testcase(self, testcase: TestCase) -> "HttpRunner":
        """run specified testcase

        Examples:
            testcase_obj = TestCase(config=TConfig(...), teststeps=[TStep(...)])
            HttpRunner().with_project_meta(...).run_testcase(testcase_obj)
        """
        self.__config = testcase.config
        self.__teststeps = testcase.teststeps

        # prepare
        self.__project_meta = self.__project_meta or load_project_meta(
            self.__config.path
        )
        self.__parse_config(self.__config)

        self.__start_at = time.time()
        self.__step_datas: List[StepData] = []
        self.__session = self.__session or HttpSession()
        # save extracted variables of teststeps
        extracted_variables: VariablesMapping = {}

        # run teststeps
        for step in self.__teststeps:
            # override variables
            # step variables > extracted variables from previous steps
            step.variables = merge_variables(step.variables, extracted_variables)
            # step variables > testcase config variables
            step.variables = merge_variables(step.variables, self.__config.variables)

            # parse variables
            step.variables = parse_variables_mapping(
                step.variables, self.__project_meta.functions
            )

            # parse step name for allure report
            step.name = parse_data(
                step.name, step.variables, self.__project_meta.functions
            )

            # run step
            try:
                if USE_ALLURE:
                    with allure.step(f"step: {step.name}"):
                        extract_mapping = self.__run_step(step)

                        # raise exception to mark this step failed in allure report
                        # run only when self.__continue_on_failure is True
                        if not (step_data := self.__step_datas[-1]).success:
                            if step.request:
                                raise step_data.data.exception
                            else:
                                raise ValidationFailure(
                                    "self.__continue_on_failure is set to True and step.testcase failed"
                                )
                else:
                    extract_mapping = self.__run_step(step)
            except ValidationFailure:
                if not self.__continue_on_failure:
                    raise

            # save extracted variables to session variables
            extracted_variables.update(extract_mapping)

        self.__session_variables.update(extracted_variables)
        self.__duration = time.time() - self.__start_at
        return self

    def run_path(self, path: Text) -> "HttpRunner":
        if not os.path.isfile(path):
            raise exceptions.ParamsError(f"Invalid testcase path: {path}")

        testcase_obj = load_testcase_file(path)
        return self.run_testcase(testcase_obj)

    def run(self) -> "HttpRunner":
        """run current testcase

        Examples:
            TestCaseRequestWithFunctions().run()
        """
        self.__init_tests__()
        testcase_obj = TestCase(config=self.__config, teststeps=self.__teststeps)
        return self.run_testcase(testcase_obj)

    def get_step_datas(self) -> List[StepData]:
        return self.__step_datas

    def get_export_variables(self) -> Dict:
        # override testcase export vars with step export
        export_var_names = self.__export or self.__config.export
        export_vars_mapping = {}
        for var_name in export_var_names:
            if var_name not in self.__session_variables:
                raise ParamsError(
                    f"failed to export variable {var_name} from session variables {self.__session_variables}"
                )

            export_vars_mapping[var_name] = self.__session_variables[var_name]

        return export_vars_mapping

    def get_failed_steps(self) -> List[TStep]:
        """
        Returns failed steps.

        self.__failed_steps is a private attribute and cannot be accessed by instance directly.
        """
        return self.__failed_steps

    def get_summary(self) -> TestCaseSummary:
        """get testcase result summary"""
        start_at_timestamp = self.__start_at
        start_at_iso_format = datetime.utcfromtimestamp(start_at_timestamp).isoformat()
        return TestCaseSummary(
            name=self.__config.name,
            success=self.success,
            case_id=self.__case_id,
            time=TestCaseTime(
                start_at=self.__start_at,
                start_at_iso_format=start_at_iso_format,
                duration=self.__duration,
            ),
            in_out=TestCaseInOut(
                config_vars=self.__config.variables,
                export_vars=self.get_export_variables(),
            ),
            log=self.__log_path,
            step_datas=self.__step_datas,
        )

    def test_start(self, param: Dict = None) -> "HttpRunner":
        """main entrance, discovered by pytest"""
        self.__init_tests__()
        self.__continue_on_failure = self.__config.continue_on_failure
        self.__project_meta = self.__project_meta or load_project_meta(
            self.__config.path
        )
        self.__case_id = self.__case_id or str(uuid.uuid4())
        self.__log_path = self.__log_path or os.path.join(
            self.__project_meta.RootDir, "logs", f"{self.__case_id}.run.log"
        )
        # do not save logging messages to log files to free disk space
        # log_handler = logger.add(self.__log_path, level="DEBUG")

        # parse config name
        config_variables = self.__config.variables
        if param:
            config_variables.update(param)
        config_variables.update(self.__session_variables)
        self.__config.name = parse_data(
            self.__config.name, config_variables, self.__project_meta.functions
        )

        if USE_ALLURE:
            # update allure report meta
            allure.dynamic.title(self.__config.name)
            allure.dynamic.description(f"TestCase ID: {self.__case_id}")

        logger.info(
            f"Start to run testcase: {self.__config.name}, TestCase ID: {self.__case_id}"
        )

        try:
            case_result = self.run_testcase(
                TestCase(config=self.__config, teststeps=self.__teststeps)
            )

            # fail testcase finally after all steps were executed and failed steps existed
            if self.__continue_on_failure:
                if self.__failed_steps:
                    self.success = False
                    raise ValidationFailure(
                        f"continue_on_failure was set to True and {len(self.__failed_steps)} steps failed."
                    )
                else:
                    self.success = True

            return case_result
        finally:
            pass
            # logger.remove(log_handler)
            # logger.info(f"generate testcase log: {self.__log_path}")
