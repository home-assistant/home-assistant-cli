"""Details for the auto-completion."""
import os
from typing import List, Tuple

from homeassistant_cli import const
from homeassistant_cli.config import Configuration
from homeassistant_cli.helper import req
from requests.exceptions import HTTPError


def _init_ctx(ctx: Configuration) -> None:
    """Initialize ctx."""
    # ctx is incomplete thus need to 'hack' around it
    # see bug https://github.com/pallets/click/issues/942
    if not hasattr(ctx, 'server'):
        ctx.server = os.environ.get('HASS_SERVER', const.DEFAULT_SERVER)

    if not hasattr(ctx, 'token'):
        ctx.token = os.environ.get('HASS_TOKEN')

    if not hasattr(ctx, 'timeout'):
        ctx.timeout = os.environ.get('HASS_TIMEOUT', const.DEFAULT_TIMEOUT)


def entities(
    ctx: Configuration, args: str, incomplete: str
) -> List[Tuple[str, str]]:
    """Entities."""
    _init_ctx(ctx)
    try:
        response = req(ctx, 'get', 'states')
    except HTTPError:
        response = None

    completions = []

    if response is not None:
        for entity in response:
            friendly_name = entity['attributes'].get('friendly_name', '')
            completions.append((entity['entity_id'], friendly_name))

        completions.sort()

        return [c for c in completions if incomplete in c[0]]

    return completions


def events(
    ctx: Configuration, args: str, incomplete: str
) -> List[Tuple[str, str]]:
    """Events."""
    _init_ctx(ctx)
    try:
        response = req(ctx, 'get', 'events')
    except HTTPError:
        response = None

    completions = []

    if response is not None:
        for entity in response:
            completions.append((entity['event'], ''))

        completions.sort()

        return [c for c in completions if incomplete in c[0]]

    return completions
