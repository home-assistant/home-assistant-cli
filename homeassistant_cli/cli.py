"""Home Assistant CLI (hass-cli)."""
import logging
import os
import sys
from typing import List, Optional, Union, cast

import click
from click.core import Command, Context, Group
import click_log

import homeassistant_cli.autocompletion as autocompletion
from homeassistant_cli.config import Configuration
import homeassistant_cli.const as const
from homeassistant_cli.helper import debug_requests_on, to_tuples

click_log.basic_config()

_LOGGER = logging.getLogger(__name__)

CONTEXT_SETTINGS = dict(auto_envvar_prefix='HOMEASSISTANT')

pass_context = click.make_pass_decorator(  # pylint: disable=invalid-name
    Configuration, ensure=True
)


def run() -> None:
    """Run entry point.

    Wraps click for full control over exception handling in Click.
    """
    # A hack to see if exception details should be printed.
    exceptionflags = ['-x']
    verbose = [c for c in exceptionflags if c in sys.argv]

    try:
        # Could use cli.invoke here to use the just created context
        # but then shell completion will not work. Thus calling
        # standalone mode to keep that working.
        result = cli.main(standalone_mode=False)
        if isinstance(result, int):
            sys.exit(result)

    # Exception handling below is done to use logger
    # and mimick as close as possible what click would
    # do normally in its main()
    except click.ClickException as ex:
        ex.show()  # let Click handle its own errors
        sys.exit(ex.exit_code)
    except click.Abort:
        _LOGGER.critical("Aborted!")
        sys.exit(1)
    except Exception as ex:  # pylint: disable=broad-except
        if verbose:
            _LOGGER.exception(ex)
        else:
            _LOGGER.error("%s: %s", type(ex).__name__, ex)
            _LOGGER.info(
                "Run with %s to see full exception information",
                " or ".join(exceptionflags),
            )
        sys.exit(1)


class HomeAssistantCli(click.MultiCommand):
    """The Home Assistant Command-line."""

    def list_commands(self, ctx: Context) -> List[str]:
        """List all command available as plugin."""
        cmd_folder = os.path.abspath(
            os.path.join(os.path.dirname(__file__), 'plugins')
        )

        commands = []
        for filename in os.listdir(cmd_folder):
            if filename.endswith('.py') and not filename.startswith('__'):
                commands.append(filename[:-3])
        commands.sort()

        return commands

    def get_command(
        self, ctx: Context, cmd_name: str
    ) -> Optional[Union[Group, Command]]:
        """Import the commands of the plugins."""
        try:
            mod = __import__(
                '{}.plugins.{}'.format(const.PACKAGE_NAME, cmd_name),
                {},
                {},
                ['cli'],
            )
        except ImportError:
            # todo: print out issue of loading plugins?
            return None
        return cast(Union[Group, Command], mod.cli)  # type: ignore


def _default_token() -> Optional[str]:
    """Handle the token provided as env variable."""
    return os.environ.get('HASS_TOKEN', os.environ.get('HASSIO_TOKEN', None))


@click.command(cls=HomeAssistantCli, context_settings=CONTEXT_SETTINGS)
@click_log.simple_verbosity_option(logging.getLogger(), "--loglevel", "-l")
@click.version_option(const.__version__)
@click.option(
    '--server',
    '-s',
    help=(
        'The server URL or `auto` for automatic detection. Can also be set '
        'with the environment variable HASS_SERVER.'
    ),
    default="auto",
    show_default=True,
    envvar='HASS_SERVER',
)
@click.option(
    '--token',
    default=_default_token,
    help=(
        'The Bearer token for Home Assistant instance. Can also be set with '
        'the environment variable HASS_TOKEN.'
    ),
    envvar='HASS_TOKEN',
)
@click.option(
    '--password',
    default=None,
    help=(
        'The API password for Home Assistant instance. Can also be set with '
        'the environment variable HASS_PASSWORD.'
    ),
    envvar='HASS_PASSWORD',
)
@click.option(
    '--timeout',
    help='Timeout for network operations.',
    default=const.DEFAULT_TIMEOUT,
    show_default=True,
)
@click.option(
    '--output',
    '-o',
    help="Output format.",
    type=click.Choice(['json', 'yaml', 'table', 'auto', 'ndjson']),
    default='auto',
    show_default=True,
)
@click.option(
    '-v',
    '--verbose',
    is_flag=True,
    default=False,
    help='Enables verbose mode.',
)
@click.option(
    '-x',
    'showexceptions',
    default=False,
    is_flag=True,
    help="Print backtraces when exception occurs.",
)
@click.option(
    '--cert',
    default=None,
    envvar="HASS_CERT",
    help="Path to client certificate file (.pem) to use when connecting.",
)
@click.option(
    '--insecure',
    is_flag=True,
    default=False,
    help=(
        'Ignore SSL Certificates.'
        ' Allow to connect to servers with self-signed certificates.'
        ' Be careful!'
    ),
)
@click.option(
    '--debug', is_flag=True, default=False, help='Enables debug mode.'
)
@click.option(
    '--columns',
    default=None,
    help=(
        'Custom columns key=value list.'
        ' Example: ENTITY=entity_id, NAME=attributes.friendly_name'
    ),
)
@click.option(
    '--columns-width',
    default=-1,
    type=click.INT,
    envvar='HASS_COL_WIDTH',
    show_default=True,
    help='Truncates column values (0: auto, -1: disable)',
)
@click.option(
    '--no-headers',
    default=False,
    is_flag=True,
    help="When printing tables don\'t use headers (default: print headers)",
)
@click.option(
    '--table-format',
    default='plain',
    help="Which table format to use.",
    autocompletion=autocompletion.table_formats,
)
@click.option(
    '--sort-by',
    default=None,
    help='Sort table by the jsonpath expression. Example: last_changed',
)
@click.version_option()
@pass_context
def cli(
    ctx: Configuration,
    verbose: bool,
    server: str,
    token: Optional[str],
    password: Optional[str],
    output: str,
    timeout: int,
    debug: bool,
    insecure: bool,
    showexceptions: bool,
    cert: str,
    columns: str,
    columns_width: int,
    no_headers: bool,
    table_format: str,
    sort_by: Optional[str],
) -> None:
    """Command line interface for Home Assistant."""
    ctx.verbose = verbose
    ctx.server = server
    ctx.token = token
    ctx.password = password
    ctx.timeout = timeout
    ctx.output = output
    ctx.debug = debug
    ctx.insecure = insecure
    ctx.showexceptions = showexceptions
    ctx.cert = cert
    ctx.columns = to_tuples(columns)
    ctx.columns_width = columns_width
    ctx.no_headers = no_headers
    ctx.table_format = table_format
    ctx.sort_by = sort_by  # type: ignore

    _LOGGER.debug("Using settings: %s", ctx)

    if debug:
        debug_requests_on()
