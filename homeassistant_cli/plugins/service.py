"""Service plugin for Home Assistant CLI (hass-cli)."""
import logging
import re as reg
import sys
from typing import Any, Dict, List, Pattern  # noqa: F401
import json
import io

import click

import homeassistant_cli.autocompletion as autocompletion
from homeassistant_cli.cli import pass_context
from homeassistant_cli.config import Configuration
from homeassistant_cli.helper import format_output, to_attributes
import homeassistant_cli.remote as api
from homeassistant_cli.yaml import yaml

_LOGGING = logging.getLogger(__name__)


@click.group('service')
@pass_context
def cli(ctx):
    """Call and work with services."""


@cli.command('list')
@click.argument('servicefilter', default=".*", required=False)
@pass_context
def list_cmd(ctx: Configuration, servicefilter):
    """Get list of services."""
    ctx.auto_output('table')
    services = api.get_services(ctx)

    result = []  # type: List[Dict[Any,Any]]
    if servicefilter == ".*":
        result = services
    else:
        result = services
        servicefilterre = reg.compile(servicefilter)  # type: Pattern

        domains = []
        for domain in services:
            domain_name = domain['domain']
            domaindata = {}
            servicesdict = domain['services']
            servicedata = {}
            for service in servicesdict:
                if servicefilterre.search(
                    "{}.{}".format(domain_name, service)
                ):
                    servicedata[service] = servicesdict[service]

            if servicedata:
                domaindata["services"] = servicedata
                domaindata["domain"] = domain_name
                domains.append(domaindata)
        result = domains

    flattenresult = []  # type: List[Dict[str,Any]]
    for domain in result:
        for service in domain['services']:
            item = {}
            item['domain'] = domain['domain']
            item['service'] = service
            item = {**item, **domain['services'][service]}
            flattenresult.append(item)

    cols = [
        ('DOMAIN', 'domain'),
        ('SERVICE', 'service'),
        ('DESCRIPTION', 'description'),
    ]
    ctx.echo(
        format_output(
            ctx, flattenresult, columns=ctx.columns if ctx.columns else cols
        )
    )


def _argument_callback(ctx, param, value):
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


@cli.command('call')
@click.argument(
    'service',
    required=True,
    autocompletion=autocompletion.services,  # type: ignore
)
@click.option(
    '--arguments', help="""Comma separated key/value pairs to use as arguments.
if string is -, the data is read from stdin, and if it starts with the letter @
the rest should be a filename from which the data is read""",
    callback=_argument_callback,
    expose_value=False
)
@click.option(
    '--json', help="""Json string to use as arguments.
if string is -, the data is read from stdin, and if it starts with the letter @
the rest should be a filename from which the data is read""",
    callback=_argument_callback,
    expose_value=False
)
@click.option(
    '--yaml', help="""Yaml string to use as arguments.
if string is -, the data is read from stdin, and if it starts with the letter @
the rest should be a filename from which the data is read""",
    callback=_argument_callback,
    expose_value=False
)
@pass_context
def call(ctx: Configuration, service, data=None):
    """Call a service."""
    ctx.auto_output('data')
    _LOGGING.debug("service call <start>")
    parts = service.split(".")
    if len(parts) != 2:
        _LOGGING.error("Service name not following <domain>.<service> format")
        sys.exit(1)

    _LOGGING.debug("calling %s.%s(%s)", parts[0], parts[1], data)

    result = api.call_service(ctx, parts[0], parts[1], data)

    _LOGGING.debug("Formatting output")
    ctx.echo(format_output(ctx, result))
