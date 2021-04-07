"""Event plugin for Home Assistant CLI (hass-cli)."""
import json as json_
import logging
from typing import Dict

import click

import homeassistant_cli.autocompletion as autocompletion
from homeassistant_cli.cli import pass_context
from homeassistant_cli.config import Configuration
from homeassistant_cli.exceptions import HomeAssistantCliError
from homeassistant_cli.helper import format_output, raw_format_output
import homeassistant_cli.remote as api

_LOGGING = logging.getLogger(__name__)


@click.group('event')
@pass_context
def cli(ctx):
    """Interact with events."""


@cli.command()
@click.argument(
    'event',
    required=True,
    autocompletion=autocompletion.events,  # type: ignore
)
@click.option(
    '--json',
    help="Raw JSON state to use for event. Overrides any other state"
    "values provided.",
)
@pass_context
def fire(ctx: Configuration, event, json):
    """Fire event in Home Assistant."""
    if json:
        click.echo("Fire {}".format(event))
        response = api.fire_event(ctx, event, json_.loads(json))
    else:
        existing = raw_format_output(ctx.output, [{}], ctx.yaml())
        new = click.edit(existing, extension='.{}'.format(ctx.output))

        if new:
            click.echo("Fire {}".format(event))
            if ctx.output == 'yaml':
                data = ctx.yamlload(new)
            else:
                data = json_.loads(new)

            response = api.fire_event(ctx, event, data)
        else:
            click.echo("No edits/changes.")
            return

    if response:
        ctx.echo(raw_format_output(ctx.output, [response], ctx.yaml()))


@cli.command()
@click.argument('event_type', required=False)
@pass_context
def watch(ctx: Configuration, event_type):
    """Subscribe and print events.

    EVENT-TYPE even type to subscribe to. if empty subscribe to all.
    """
    frame = {'type': 'subscribe_events'}

    cols = [('EVENT_TYPE', 'event_type'), ('DATA', '$.data')]

    def _msghandler(msg: Dict) -> None:
        if msg['type'] == 'event':
            ctx.echo(
                format_output(
                    ctx,
                    msg['event'],
                    columns=ctx.columns if ctx.columns else cols,
                )
            )
        elif msg['type'] == 'auth_invalid':
            raise HomeAssistantCliError(msg.get('message'))

    if event_type:
        frame['event_type'] = event_type

    api.wsapi(ctx, frame, _msghandler)
