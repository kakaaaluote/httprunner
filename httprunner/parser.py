import ast
import builtins
import os
import re
import time
from typing import Any, Callable, Dict, List, Set, Text
from urllib.parse import urlparse

from dotwiz import DotWiz
from loguru import logger
from sentry_sdk import capture_exception

from httprunner import exceptions, loader, utils
from httprunner.exceptions import VariableNotFound
from httprunner.models import FunctionsMapping, StableDeepCopyDict, VariablesMapping

absolute_http_url_regexp = re.compile(r"^https?://", re.I)

# use $$ to escape $ notation
dollar_regex_compile = re.compile(r"\$\$")
# variable notation, e.g. ${var} or $var
variable_regex_compile = re.compile(r"\$\{(\w+)}|\$(\w+)")
# function notation, e.g. ${func1($var_1, $var_3)}
function_regex_compile = re.compile(r"\$\{(\w+)\(([$\w.\-/\s=,]*)\)}")
# python expression
expression_regex_compile = re.compile(r"""\$\{([$\w.[\]:'"]*[.[][$\w.[\]:'"]*)}""")
expression_leading_var_regex_compile = re.compile(r"(\w+)[.\[]")
# pyexp
pyexp_regex_compile = re.compile(r"\$\{pyexp\((.*)\)}")
# pyexec
pyexec_regex_compile = re.compile(r"\$\{pyexec\((.*)\)}")


def parse_string_value(str_value: Text) -> Any:
    """parse string to number if possible
    e.g. "123" => 123
         "12.2" => 12.3
         "abc" => "abc"
         "$var" => "$var"
    """
    try:
        return ast.literal_eval(str_value)
    except ValueError:
        return str_value
    except SyntaxError:
        # e.g. $var, ${func}
        return str_value


def build_url(base_url, path):
    """prepend url with base_url unless it's already an absolute URL"""
    if absolute_http_url_regexp.match(path):
        return path
    elif base_url:
        return "{}/{}".format(base_url.rstrip("/"), path.lstrip("/"))
    else:
        raise exceptions.ParamsError("base url missed!")


def update_url_origin(url: str, origin: str) -> str:
    """
    Substitute origin of specific url.

    >>> update_url_origin("http://foo.com/bar", "https://bar.com")
    'https://bar.com/bar'
    """
    parsed_new_origin = urlparse(origin)

    if not (new_scheme := parsed_new_origin.scheme):
        raise ValueError(f"no scheme found in origin '{origin}'")

    if not (new_netloc := parsed_new_origin.netloc):
        raise ValueError(f"no netloc found in origin '{origin}'")

    return urlparse(url)._replace(scheme=new_scheme, netloc=new_netloc).geturl()


def regex_findall_variables(raw_string: Text) -> List[Text]:
    """extract all variable names from content, which is in format $variable

    Args:
        raw_string (str): string content

    Returns:
        list: variables list extracted from string content

    Examples:
        >>> regex_findall_variables("$variable")
        ['variable']

        >>> regex_findall_variables("/blog/$postid")
        ['postid']

        >>> regex_findall_variables("/$var1/$var2")
        ['var1', 'var2']

        >>> regex_findall_variables("abc")
        []

        >>> regex_findall_variables("${obj.attr['$foo']}")
        ['obj', 'foo']
    """
    try:
        match_start_position = raw_string.index("$", 0)
    except ValueError:
        return []

    vars_list = []
    while match_start_position < len(raw_string):
        # Notice: notation priority
        # $$ > $var

        # search $$
        dollar_match = dollar_regex_compile.match(raw_string, match_start_position)
        if dollar_match:
            match_start_position = dollar_match.end()
            continue

        # search expression like ${obj.attr[0]}
        if expression_match := expression_regex_compile.match(
            raw_string, match_start_position
        ):
            raw_expression = expression_match.group(1)
            vars_list.append(
                expression_leading_var_regex_compile.match(raw_expression).group(1)
            )
            vars_list += regex_findall_variables(raw_expression)
            match_start_position = expression_match.end()
            continue

        # search variable like ${var} or $var
        var_match = variable_regex_compile.match(raw_string, match_start_position)
        if var_match:
            var_name = var_match.group(1) or var_match.group(2)
            vars_list.append(var_name)
            match_start_position = var_match.end()
            continue

        curr_position = match_start_position
        try:
            # find next $ location
            match_start_position = raw_string.index("$", curr_position + 1)
        except ValueError:
            # break while loop
            break

    return vars_list


def regex_findall_functions(content: Text) -> List[Text]:
    """extract all functions from string content, which are in format ${fun()}

    Args:
        content (str): string content

    Returns:
        list: functions list extracted from string content

    Examples:
        >>> regex_findall_functions("${func(5)}")
        ["func(5)"]

        >>> regex_findall_functions("${func(a=1, b=2)}")
        ["func(a=1, b=2)"]

        >>> regex_findall_functions("/api/1000?_t=${get_timestamp()}")
        ["get_timestamp()"]

        >>> regex_findall_functions("/api/${add(1, 2)}")
        ["add(1, 2)"]

        >>> regex_findall_functions("/api/${add(1, 2)}?_t=${get_timestamp()}")
        ["add(1, 2)", "get_timestamp()"]

    """
    try:
        return function_regex_compile.findall(content)
    except TypeError as ex:
        capture_exception(ex)
        return []


def extract_variables(content: Any) -> Set:
    """extract all variables in content recursively."""
    if isinstance(content, (list, set, tuple)):
        variables = set()
        for item in content:
            variables = variables | extract_variables(item)
        return variables

    # ignore DotMap
    # note: DotMap must be handled before `dict` for DotMap subclassed `dict`
    elif isinstance(content, DotWiz):
        return set()

    elif isinstance(content, dict):
        variables = set()
        for key, value in content.items():
            variables = variables | extract_variables(value) | extract_variables(key)
        return variables

    elif isinstance(content, str):
        return set(regex_findall_variables(content))

    return set()


def parse_function_params(params: Text) -> Dict:
    """parse function params to args and kwargs.

    Args:
        params (str): function param in string

    Returns:
        dict: function meta dict

            {
                "args": [],
                "kwargs": {}
            }

    Examples:
        >>> parse_function_params("")
        {'args': [], 'kwargs': {}}

        >>> parse_function_params("5")
        {'args': [5], 'kwargs': {}}

        >>> parse_function_params("1, 2")
        {'args': [1, 2], 'kwargs': {}}

        >>> parse_function_params("a=1, b=2")
        {'args': [], 'kwargs': {'a': 1, 'b': 2}}

        >>> parse_function_params("1, 2, a=3, b=4")
        {'args': [1, 2], 'kwargs': {'a':3, 'b':4}}

    """
    function_meta = {"args": [], "kwargs": {}}

    params_str = params.strip()
    if params_str == "":
        return function_meta

    args_list = params_str.split(",")
    for arg in args_list:
        arg = arg.strip()
        if "=" in arg:
            key, value = arg.split("=")
            function_meta["kwargs"][key.strip()] = parse_string_value(value.strip())
        else:
            function_meta["args"].append(parse_string_value(arg))

    return function_meta


def get_mapping_variable(
    variable_name: Text, variables_mapping: VariablesMapping
) -> Any:
    """get variable from variables_mapping.

    Args:
        variable_name (str): variable name
        variables_mapping (dict): variables mapping

    Returns:
        mapping variable value.

    Raises:
        exceptions.VariableNotFound: variable is not found.

    """
    # TODO: get variable from debugtalk module and environ
    try:
        return variables_mapping[variable_name]
    except KeyError:
        raise exceptions.VariableNotFound(
            f"`{variable_name}` not found, available vars: {list(variables_mapping.keys())}",
            variable_name,
        )


def get_mapping_function(
    function_name: Text, functions_mapping: FunctionsMapping
) -> Callable:
    """get function from functions_mapping,
        if not found, then try to check if builtin function.

    Args:
        function_name (str): function name
        functions_mapping (dict): functions mapping

    Returns:
        mapping function object.

    Raises:
        exceptions.FunctionNotFound: function is neither defined in debugtalk.py nor builtin.

    """
    if function_name in functions_mapping:
        return functions_mapping[function_name]

    elif function_name in ["parameterize", "P"]:
        return loader.load_csv_file

    elif function_name in ["environ", "ENV"]:
        return utils.get_os_environ

    elif function_name in ["multipart_encoder", "multipart_content_type"]:
        # extension for upload test
        from httprunner.ext import uploader

        return getattr(uploader, function_name)

    try:
        # check if HttpRunner builtin functions
        built_in_functions = loader.load_builtin_functions()
        return built_in_functions[function_name]
    except KeyError:
        pass

    try:
        # check if Python builtin functions
        return getattr(builtins, function_name)
    except AttributeError:
        pass

    raise exceptions.FunctionNotFound(f"{function_name} is not found.")


def parse_string(
    raw_string: Text,
    variables_mapping: VariablesMapping,
    functions_mapping: FunctionsMapping,
) -> Any:
    """parse string content with variables and functions mapping.

    Args:
        raw_string: raw string content to be parsed.
        variables_mapping: variables mapping.
        functions_mapping: functions mapping.

    Returns:
        str: parsed string content.

    Examples:
        >>> _raw_string = "abc${add_one($num)}def"
        >>> _variables_mapping = {"num": 3}
        >>> _functions_mapping = {"add_one": lambda x: x + 1}
        >>> parse_string(_raw_string, _variables_mapping, _functions_mapping)
            "abc4def"
    """
    # search ${pyexp()}
    if "$" in raw_string and pyexp_regex_compile.search(raw_string):
        pyexp_full_match = pyexp_regex_compile.fullmatch(raw_string)
        if not pyexp_full_match:
            raise SyntaxError(
                f"The whole string must match regular expression {pyexp_regex_compile} if you want to user pyexp"
            )
        else:
            globals_ = {}
            globals_.update(variables_mapping)
            globals_.update(functions_mapping)
            try:
                return eval(pyexp_full_match.group(1), globals_)
            except NameError as ne:
                # get the name not defined from exception, e.g. name 'baz' is not defined
                name_not_found = str(ne).split("'")[1]
                raise VariableNotFound(
                    f"`{name_not_found}` not found, available vars: {list(variables_mapping.keys())}",
                    name_not_found,
                ) from ne

    # search ${pyexec()}
    if "$" in raw_string and pyexec_regex_compile.search(raw_string):
        pyexec_full_match = pyexec_regex_compile.fullmatch(raw_string)
        if not pyexec_full_match:
            raise SyntaxError(
                f"The whole string must match regular expression {pyexec_regex_compile} if you want to user pyexec"
            )
        else:
            globals_ = {}
            globals_.update(variables_mapping)
            globals_.update(functions_mapping)
            try:
                # note: exec() always return None
                return exec(pyexec_full_match.group(1), globals_)
            except NameError as ne:
                # get the name not defined from exception, e.g. name 'baz' is not defined
                name_not_found = str(ne).split("'")[1]
                raise VariableNotFound(
                    f"`{name_not_found}` not found, available vars: {list(variables_mapping.keys())}",
                    name_not_found,
                ) from ne

    try:
        match_start_position = raw_string.index("$", 0)
        parsed_string = raw_string[0:match_start_position]
    except ValueError:
        parsed_string = raw_string
        return parsed_string

    while match_start_position < len(raw_string):
        # Notice: notation priority
        # $$ > ${func($a, $b)} > $var

        # search $$
        dollar_match = dollar_regex_compile.match(raw_string, match_start_position)
        if dollar_match:
            match_start_position = dollar_match.end()
            parsed_string += "$"
            continue

        # search expression like ${obj.attr[0]['key']}
        expression_match = expression_regex_compile.match(
            raw_string, match_start_position
        )
        if expression_match:
            # raw expression without leading "${" and ending "}"
            raw_expression = expression_match.group(1)

            # eval variables before eval expression
            raw_expression = parse_string(
                raw_expression, variables_mapping, functions_mapping
            )

            try:
                # copy variables_mapping for builtin function eval
                # will insert __builtins__ into it and change variables_mapping
                variables_mapping_copy = variables_mapping.copy()
                expression_eval_value = eval(raw_expression, variables_mapping_copy)
            except NameError as ex:
                raise exceptions.VariableNotFound(
                    f"{ex}, available vars: {list(variables_mapping.keys())}"
                )
            except Exception as ex:
                raise ValueError(
                    f"error occurs while evaluating expression '{raw_expression}'. {type(ex).__name__}: {ex}"
                )

            # raw_string is an expression, e.g. "${obj.attr[0]['key']}", return its eval value directly
            if expression_match.group(0) == raw_string:
                return expression_eval_value

            # raw_string contains not only expression, e.g. "${obj.attr[0]['key']}${func()}"
            parsed_string += str(expression_eval_value)
            match_start_position = expression_match.end()
            continue

        # search function like ${func($a, $b)}
        func_match = function_regex_compile.match(raw_string, match_start_position)
        if func_match:
            func_name = func_match.group(1)
            func_params_str = func_match.group(2)
            function_meta = parse_function_params(func_params_str)
            args = function_meta["args"]
            kwargs = function_meta["kwargs"]
            parsed_args = parse_data(args, variables_mapping, functions_mapping)
            parsed_kwargs = parse_data(kwargs, variables_mapping, functions_mapping)

            if func_name == "eval_var":
                # check arguments assigned to func 'eval_var'
                if len(args) != 1:
                    raise ValueError(
                        f"expect 1 positional argument when func name is 'eval_var', but got: {len(args)}"
                    )
                if len(kwargs) > 0:
                    raise ValueError(
                        f"no keyword arguments are expected when func name is 'eval_var', but got: {len(kwargs)}"
                    )

                # parse again
                func_eval_value = parse_data(
                    parsed_args[0], variables_mapping, functions_mapping
                )
            else:
                func = get_mapping_function(func_name, functions_mapping)
                try:
                    func_eval_value = func(*parsed_args, **parsed_kwargs)
                except Exception as ex:
                    logger.error(
                        f"call function error:\n"
                        f"func_name: {func_name}\n"
                        f"args: {parsed_args}\n"
                        f"kwargs: {parsed_kwargs}\n"
                        f"{type(ex).__name__}: {ex}"
                    )
                    raise

            func_raw_str = "${" + func_name + f"({func_params_str})" + "}"
            if func_raw_str == raw_string:
                # raw_string is a function, e.g. "${add_one(3)}", return its eval value directly
                return func_eval_value

            # raw_string contains one or many functions, e.g. "abc${add_one(3)}def"
            parsed_string += str(func_eval_value)
            match_start_position = func_match.end()
            continue

        # search variable like ${var} or $var
        var_match = variable_regex_compile.match(raw_string, match_start_position)
        if var_match:
            var_name = var_match.group(1) or var_match.group(2)
            var_value = get_mapping_variable(var_name, variables_mapping)

            if f"${var_name}" == raw_string or "${" + var_name + "}" == raw_string:
                # raw_string is a variable, $var or ${var}, return its value directly
                return var_value

            # raw_string contains one or many variables, e.g. "abc${var}def"
            parsed_string += str(var_value)
            match_start_position = var_match.end()
            continue

        curr_position = match_start_position
        try:
            # find next $ location
            match_start_position = raw_string.index("$", curr_position + 1)
            remain_string = raw_string[curr_position:match_start_position]
        except ValueError:
            remain_string = raw_string[curr_position:]
            # break while loop
            match_start_position = len(raw_string)

        parsed_string += remain_string

    return parsed_string


class ParseMe(object):
    """
    Instances of all classes subclassing this class will be resolved by function 'parse_data'.

    Note:
        You must inherit this class if you want to resolve attributes of instances,
        for resolving any class instances implicitly may cause problems,
        e.g. attributes containing $ will be recognized as variable and VariableNotFound exception may be thrown.
    """

    pass


def parse_data(
    raw_data: Any,
    variables_mapping: VariablesMapping = None,
    functions_mapping: FunctionsMapping = None,
) -> Any:
    """parse raw data with evaluated variables mapping.
    Notice: variables_mapping should not contain any variable or function.
    """
    if isinstance(raw_data, str):
        # content in string format may contain variables and functions
        variables_mapping = variables_mapping or {}
        functions_mapping = functions_mapping or {}
        # only strip whitespaces and tabs, \n\r is left because they maybe used in changeset
        # do not strip blank space, otherwise comparison will fail
        # raw_data = raw_data.strip(" \t")
        return parse_string(raw_data, variables_mapping, functions_mapping)

    elif isinstance(raw_data, list):
        # fix: do not create new list, otherwise the id of list will be changed
        for index, item in enumerate(raw_data):
            raw_data[index] = parse_data(item, variables_mapping, functions_mapping)
        return raw_data

    elif isinstance(raw_data, set):
        for item in raw_data:
            raw_data.remove(item)
            raw_data.add(parse_data(item, variables_mapping, functions_mapping))
        return raw_data

    # note: tuple cannot be modified, so we have to create a new tuple
    elif isinstance(raw_data, tuple):
        return tuple(
            [
                parse_data(item, variables_mapping, functions_mapping)
                for item in raw_data
            ]
        )

    # do not parse DotMap and return it as is
    # note: DotMap must be handled before `dict` for it subclassed `dict`
    elif isinstance(raw_data, DotWiz):
        return raw_data

    elif isinstance(raw_data, dict):
        # reference:
        for key in list(raw_data.keys()):
            parsed_key = parse_data(key, variables_mapping, functions_mapping)
            parsed_value = parse_data(
                raw_data[key], variables_mapping, functions_mapping
            )
            raw_data[parsed_key] = parsed_value

            if parsed_key != key:
                raw_data.pop(key)

        return raw_data

    elif isinstance(raw_data, ParseMe):
        raw_data.__dict__ = parse_data(
            raw_data.__dict__, variables_mapping, functions_mapping
        )
        return raw_data

    else:
        # other types, e.g. None, int, float, bool
        return raw_data


def parse_variables_mapping(
    variables_mapping: VariablesMapping, functions_mapping: FunctionsMapping = None
) -> StableDeepCopyDict:
    """
    All variables specified in argument 'variables_mapping' must be parsed on variables_mapping and functions_mapping.

    Note:
        Variables whose name starting with '_r_' will be marked as parsed and the value will be kept as is.
    """
    parsed_variables: StableDeepCopyDict = StableDeepCopyDict()
    not_found_variables: set = set()

    start = time.time()

    while len(parsed_variables) != len(variables_mapping):
        elapsed = time.time() - start
        if elapsed > 15:
            not_parsed_variables = {
                name: variables_mapping[name]
                for name in set(variables_mapping.keys()) - set(parsed_variables.keys())
            }
            not_found_variables = not_found_variables - set(parsed_variables.keys())
            raise TimeoutError(
                f"\nvariable mapping that cannot be parsed: {not_parsed_variables}"
                f"\nvariables not found: {list(not_found_variables)}"
            )

        for outer_var_name in variables_mapping:
            if outer_var_name in parsed_variables:
                continue

            outer_var_value = variables_mapping[outer_var_name]

            # mark variables whose name starting with '_r_' as parsed and keep the value as is
            if outer_var_name.startswith("_r_"):
                parsed_variables[outer_var_name] = outer_var_value
                continue

            inner_variables = extract_variables(outer_var_value)

            # check if reference variable itself
            if outer_var_name in inner_variables:
                # e.g.
                # variables_mapping = {"token": "abc$token"}
                # variables_mapping = {"key": ["$key", 2]}
                raise exceptions.VariableNotFound(outer_var_name)

            # check if reference variable not in variables_mapping
            not_defined_variables = [
                v_name for v_name in inner_variables if v_name not in variables_mapping
            ]
            if not_defined_variables:
                # e.g. {"varA": "123$varB", "varB": "456$varC"}
                # e.g. {"varC": "${sum_two($a, $b)}"}
                raise exceptions.VariableNotFound(not_defined_variables)

            try:
                parsed_outer_var_value = parse_data(
                    outer_var_value, parsed_variables, functions_mapping
                )
            except exceptions.VariableNotFound as exc:
                # get variables from exception arguments, e.g. ("baz not found in {'foo': 1, 'bar': 2}", "baz")
                if len(exc.args) >= 2:
                    not_found_variables.add(exc.args[1])
                continue

            parsed_variables[outer_var_name] = parsed_outer_var_value

    return parsed_variables


def parse_parameters(parameters: Dict, is_allpairs: bool = False) -> List[Dict]:
    """parse parameters and generate cartesian product.

    Args:
        parameters (Dict) parameters: parameter name and value mapping
            parameter value may be in three types:
                (1) data list, e.g. ["iOS/10.1", "iOS/10.2", "iOS/10.3"]
                (2) call built-in parameterize function, "${parameterize(account.csv)}"
                (3) call custom function in debugtalk.py, "${gen_app_version()}"
        is_allpairs (bool) parameters: 是否使用正交实验法生成用例集，默认不使用


    Returns:
        list: cartesian product list or allpairs product list

    Examples:
        >>> _parameters = {
            "user_agent": ["iOS/10.1", "iOS/10.2", "iOS/10.3"],
            "username-password": "${parameterize(account.csv)}",
            "app_version": "${gen_app_version()}",
        }
        >>> parse_parameters(_parameters)

    """
    parsed_parameters_list: List[List[Dict]] = []

    # load project_meta functions
    project_meta = loader.load_project_meta(os.getcwd())
    functions_mapping = project_meta.functions

    for parameter_name, parameter_content in parameters.items():
        parameter_name_list = parameter_name.split("-")

        if isinstance(parameter_content, List):
            # (1) data list
            # e.g. {"app_version": ["2.8.5", "2.8.6"]}
            #       => [{"app_version": "2.8.5", "app_version": "2.8.6"}]
            # e.g. {"username-password": [["user1", "111111"], ["test2", "222222"]}
            #       => [{"username": "user1", "password": "111111"}, {"username": "user2", "password": "222222"}]
            parameter_content_list: List[Dict] = []
            for parameter_item in parameter_content:
                if not isinstance(parameter_item, (list, tuple)):
                    # "2.8.5" => ["2.8.5"]
                    parameter_item = [parameter_item]

                # ["app_version"], ["2.8.5"] => {"app_version": "2.8.5"}
                # ["username", "password"], ["user1", "111111"] => {"username": "user1", "password": "111111"}
                parameter_content_dict = dict(zip(parameter_name_list, parameter_item))
                parameter_content_list.append(parameter_content_dict)

        elif isinstance(parameter_content, Text):
            # (2) & (3)
            parsed_parameter_content: List = parse_data(
                parameter_content, {}, functions_mapping
            )
            if not isinstance(parsed_parameter_content, List):
                raise exceptions.ParamsError(
                    f"parameters content should be in List type, got {parsed_parameter_content} for {parameter_content}"
                )

            parameter_content_list: List[Dict] = []
            for parameter_item in parsed_parameter_content:
                if isinstance(parameter_item, Dict):
                    # get subset by parameter name
                    # {"app_version": "${gen_app_version()}"}
                    # gen_app_version() => [{'app_version': '2.8.5'}, {'app_version': '2.8.6'}]
                    # {"username-password": "${get_account()}"}
                    # get_account() => [
                    #       {"username": "user1", "password": "111111"},
                    #       {"username": "user2", "password": "222222"}
                    # ]
                    parameter_dict: Dict = {
                        key: parameter_item[key] for key in parameter_name_list
                    }
                elif isinstance(parameter_item, (List, tuple)):
                    if len(parameter_name_list) == len(parameter_item):
                        # {"username-password": "${get_account()}"}
                        # get_account() => [("user1", "111111"), ("user2", "222222")]
                        parameter_dict = dict(zip(parameter_name_list, parameter_item))
                    else:
                        raise exceptions.ParamsError(
                            f"parameter names length are not equal to value length.\n"
                            f"parameter names: {parameter_name_list}\n"
                            f"parameter values: {parameter_item}"
                        )
                elif len(parameter_name_list) == 1:
                    # {"user_agent": "${get_user_agent()}"}
                    # get_user_agent() => ["iOS/10.1", "iOS/10.2"]
                    # parameter_dict will get: {"user_agent": "iOS/10.1", "user_agent": "iOS/10.2"}
                    parameter_dict = {parameter_name_list[0]: parameter_item}
                else:
                    raise exceptions.ParamsError(
                        f"Invalid parameter names and values:\n"
                        f"parameter names: {parameter_name_list}\n"
                        f"parameter values: {parameter_item}"
                    )

                parameter_content_list.append(parameter_dict)

        else:
            raise exceptions.ParamsError(
                f"parameter content should be List or Text(variables or functions call), got {parameter_content}"
            )

        parsed_parameters_list.append(parameter_content_list)
    if is_allpairs:
        return utils.gen_allpairs_product(parsed_parameters_list)
    else:
        return utils.gen_cartesian_product(*parsed_parameters_list)
