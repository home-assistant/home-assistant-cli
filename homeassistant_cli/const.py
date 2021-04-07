"""Constants used by Home Assistant CLI (hass-cli)."""
PACKAGE_NAME = 'homeassistant_cli'

__version__ = '0.10.0.dev0'

AUTO_SERVER = 'auto'
DEFAULT_SERVER = 'http://localhost:8123'
DEFAULT_SERVER_MDNS = 'http://homeassistant.local:8123'
DEFAULT_TIMEOUT = 5
DEFAULT_OUTPUT = 'json'  # TODO: Have default be human table relevant output

DEFAULT_DATAOUTPUT = 'yaml'

COLUMNS_DEFAULT = [('ALL', '$')]
COLUMNS_ENTITIES = [
    ('ENTITY', 'entity_id'),
    ('DESCRIPTION', 'attributes.friendly_name'),
    ('STATE', 'state'),
    ('CHANGED', 'last_changed'),
]
COLUMNS_SERVICES = [('DOMAIN', 'domain'), ("SERVICE", "domain.services[*]")]

COLUMNS_WIDTH_DEFAULT = -1
COLUMNS_WIDTH_STR = "\u2026"
