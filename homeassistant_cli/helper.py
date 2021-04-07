"""Helpers used by Home Assistant CLI (hass-cli)."""
import contextlib
from http.client import HTTPConnection
import json
import logging
import shlex
from typing import Any, Dict, Generator, List, Optional, Tuple, Union, cast
from typing import TextIO
import sys
import io

from ruamel.yaml import YAML
from tabulate import tabulate

from homeassistant_cli.config import Configuration
import homeassistant_cli.const as const
import homeassistant_cli.yaml as yaml

_LOGGING = logging.getLogger(__name__)


def to_attributes(entry: Union[str, TextIO]) -> Dict[str, str]:
    """Convert list of key=value pairs to dictionary."""
    if not entry:
        return {}

    lexer = shlex.shlex(entry, posix=True)
    lexer.whitespace_split = True
    lexer.whitespace = ','
    attributes_dict = {}  # type: Dict[str, str]
    attributes_dict = dict(
        pair.split('=', 1) for pair in lexer  # type: ignore
    )
    return attributes_dict


def to_tuples(entry: str) -> List[Tuple[str, str]]:
    """Convert list of key=value pairs to list of tuples."""
    if not entry:
        return []

    lexer = shlex.shlex(entry, posix=True)
    lexer.whitespace_split = True
    lexer.whitespace = ','
    attributes_list = []  # type: List[Tuple[str,str]]
    attributes_list = list(
        tuple(pair.split('=', 1)) for pair in lexer  # type: ignore
    )
    return attributes_list


def raw_format_output(
    output: str,
    data: Union[Dict[str, Any], List[Dict[str, Any]]],
    yamlparser: YAML,
    columns: Optional[List] = None,
    no_headers: bool = False,
    table_format: str = 'plain',
    sort_by: Optional[str] = None,
) -> str:
    """Format the raw output."""
    if output == 'auto':
        _LOGGING.debug("Output `auto` thus using %s", const.DEFAULT_DATAOUTPUT)
        output = const.DEFAULT_DATAOUTPUT

    if sort_by and isinstance(data, List):
        _sort_table(data, sort_by)

    if output == 'json':
        try:
            return json.dumps(data, indent=2, sort_keys=False)
        except ValueError:
            return str(data)
    elif output == 'ndjson':
        try:
            return json.dumps(data)
        except ValueError:
            return str(data)
    elif output == 'yaml':
        try:
            return cast(str, yaml.dumpyaml(yamlparser, data))
        except ValueError:
            return str(data)
    elif output == 'table':
        from jsonpath_ng import parse

        if not columns:
            columns = const.COLUMNS_DEFAULT

        fmt = [(v[0], parse(v[1] if len(v) > 1 else v[0])) for v in columns]

        result = []

        if no_headers:
            headers = []  # type: List[str]
        else:
            headers = [v[0] for v in fmt]

        # In case data passed in is a single element
        # we turn it into a single item list for better table output
        if not isinstance(data, List):
            data = [data]

        for item in data:
            row = []
            for fmtpair in fmt:
                val = [match.value for match in fmtpair[1].find(item)]
                row.append(", ".join(map(str, val)))
            result.append(row)

        res = tabulate(
            result, headers=headers, tablefmt=table_format
        )  # type: str
        return res
    else:
        raise ValueError(
            "Output Format was {}, expected either 'json' or 'yaml'".format(
                output
            )
        )


def _sort_table(result: List[Any], sort_by: str) -> List[Any]:
    """Sort the content of a table."""
    from jsonpath_ng import parse

    expr = parse(sort_by)

    def _internal_sort(row: Dict[Any, str]) -> Any:
        val = next(iter([match.value for match in expr.find(row)]), None)
        return (val is None, val)

    result.sort(key=_internal_sort)
    return result


def format_output(
    ctx: Configuration,
    data: List[Dict[str, Any]],
    columns: Optional[List] = None,
) -> str:
    """Format data to output based on settings in ctx/Context."""
    return raw_format_output(
        ctx.output,
        data,
        ctx.yaml(),
        columns,
        ctx.no_headers,
        ctx.table_format,
        ctx.sort_by,
    )


def debug_requests_on() -> None:
    """Switch on logging of the requests module."""
    HTTPConnection.set_debuglevel(cast(HTTPConnection, HTTPConnection), 1)

    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger('requests.packages.urllib3')
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True


def debug_requests_off() -> None:
    """Switch off logging of the requests module.

    Might have some side-effects.
    """
    HTTPConnection.set_debuglevel(cast(HTTPConnection, HTTPConnection), 1)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)
    root_logger.handlers = []
    requests_log = logging.getLogger('requests.packages.urllib3')
    requests_log.setLevel(logging.WARNING)
    requests_log.propagate = False


@contextlib.contextmanager
def debug_requests() -> Generator:
    """Yieldable way to turn on debugs for requests.

    with debug_requests(): <do things>
    """
    debug_requests_on()
    yield
    debug_requests_off()


def argument_callback(ctx, param, value):
    """Helper to parse json, yaml and key-value arguments"""
    _LOGGING.debug("_argument_callback called, %s(%s)", param.name, value)

    # We get called with value None
    # for all the callbacks which aren't provided.
    if value is None:
        return

    if 'data' in ctx.params and ctx.params['data'] is not None:
        _LOGGING.error("You can only specify one type of the argument types!")
        _LOGGING.debug(ctx.params)
        ctx.exit()

    if value == '-':  # read from stdin
        _LOGGING.debug("Loading value from stdin")
        value = sys.stdin
    elif value.startswith('@'):  # read from file
        _LOGGING.debug("Loading value from file: %s", value[1:])
        value = open(value[1:], 'r')
    else:
        _LOGGING.debug("Using value as is: %s", value)

    if param.name == 'arguments':
        result = to_attributes(value)
    elif param.name == 'json':
        # We need to use different json calls to load from stream or string
        if isinstance(value, str):
            result = json.loads(value)
        else:
            result = json.load(value)
    elif param.name == 'yaml':
        result = yaml().load(value)
    else:
        _LOGGING.error("Parameter name is unknown: %s", param.name)
        ctx.exit()

    if isinstance(value, io.IOBase):
        value.close()

    ctx.params['data'] = result
