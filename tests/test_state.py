"""Tests file for Home Assistant CLI (hass-cli)."""
import json
import re

from click.testing import CliRunner
import requests_mock

import homeassistant_cli.cli as cli

EDITED_ENTITY = """
{
  "attributes": {
    "auto": false,
    "entity_id": [
      "remote.tv"
    ],
    "friendly_name": "all remotes",
    "hidden": true,
    "order": 16
  },
  "context": {
    "id": "4c511277c55647eb8e7e4acf10fcd617",
    "user_id": null
  },
  "entity_id": "group.all_remotes",
  "last_changed": "2018-12-04T10:13:05.914548+00:00",
  "last_updated": "2018-12-04T10:13:05.914548+00:00",
  "state": "off"
}
"""

LIST_EDITED_ENTITY = "[{}]".format(EDITED_ENTITY)


def test_state_list(basic_entities_text) -> None:
    """Test entities can be listed."""
    with requests_mock.Mocker() as mock:
        mock.get(
            "http://localhost:8123/api/states",
            text=basic_entities_text,
            status_code=200,
        )

        runner = CliRunner()
        result = runner.invoke(
            cli.cli, ["--output=json", "state", "list"], catch_exceptions=False
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert json.loads(basic_entities_text) == data
        assert len(data) == 3


def output_formats(cmd, data, output) -> None:
    """Test output formats."""
    with requests_mock.Mocker() as mock:
        mock.get(
            "http://localhost:8123/api/states", text=data, status_code=200
        )

        runner = CliRunner()
        result = runner.invoke(cli.cli, cmd, catch_exceptions=False)
        print('--seen--')
        print(result.output)
        print('----')
        print('---expected---')
        print(output)
        print('----')
        assert result.exit_code == 0
        assert result.output == output


def test_state_list_table(
    basic_entities_text, basic_entities_table_text
) -> None:
    """Test table."""
    output_formats(
        ["--output=table", "state", "list"],
        basic_entities_text,
        basic_entities_table_text,
    )


def test_state_default_list_table(
    basic_entities_text, basic_entities_table_text
) -> None:
    """Test table."""
    output_formats(
        ["state", "list"], basic_entities_text, basic_entities_table_text
    )


def test_state_list_tblformat(
    basic_entities_text, basic_entities_table_format_text
) -> None:
    """Test table format."""
    output_formats(
        ["--output=table", "--table-format=html", "state", "list"],
        basic_entities_text,
        basic_entities_table_format_text,
    )


def test_state_list_table_columns(
    basic_entities_text, basic_entities_table_columns_text
) -> None:
    """Test table columns."""
    output_formats(
        [
            "--output=table",
            "--columns=entity=attributes.friendly_name,state=state",
            "state",
            "list",
        ],
        basic_entities_text,
        basic_entities_table_columns_text,
    )


def test_state_list_table_columns_sortby(
    basic_entities_text, basic_entities_table_sorted_text
) -> None:
    """Test table columns."""
    output_formats(
        [
            "--output=table",
            (
                '--columns=entity=attributes.friendly_name,'
                'state=state,last_changed'
            ),
            "--sort-by=last_changed",
            "state",
            "list",
        ],
        basic_entities_text,
        basic_entities_table_sorted_text,
    )


def test_state_list_table_columns_width(
    basic_entities_text, basic_entities_table_fixed_width_text
) -> None:
    """Test table columns."""
    output_formats(
        ["--output=table", "--columns-width=15", "state", "list"],
        basic_entities_text,
        basic_entities_table_fixed_width_text,
    )


def test_state_list_no_header(
    basic_entities_text, basic_entities_table_no_header_text
) -> None:
    """Test table no header."""
    output_formats(
        ["--output=table", "--no-headers", "state", "list"],
        basic_entities_text,
        basic_entities_table_no_header_text,
    )


def test_state_get(basic_entities_text, basic_entities) -> None:
    """Test entity get."""
    with requests_mock.Mocker() as mock:
        sensorone = next(
            x for x in basic_entities if x['entity_id'] == 'sensor.one'
        )
        mock.get(
            "http://localhost:8123/api/states/sensor.one",
            json=sensorone,
            status_code=200,
        )

        runner = CliRunner()
        result = runner.invoke(
            cli.cli,
            ["--output=json", "state", "get", "sensor.one"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0

        data = json.loads(result.output)
        assert len(data) == 1
        assert "entity_id" in data[0]
        assert data[0]["entity_id"] == "sensor.one"


def test_state_edit(basic_entities_text, basic_entities) -> None:
    """Test basic edit of state."""
    with requests_mock.Mocker() as mock:
        get = mock.get(
            "http://localhost:8123/api/states",
            text=basic_entities_text,
            status_code=200,
        )
        sensorone = next(
            x for x in basic_entities if x['entity_id'] == 'sensor.one'
        )
        get = mock.get(
            "http://localhost:8123/api/states/sensor.one",
            json=sensorone,
            status_code=200,
        )
        post = mock.post(
            "http://localhost:8123/api/states/sensor.one",
            text=EDITED_ENTITY,
            status_code=200,
        )

        runner = CliRunner()
        result = runner.invoke(
            cli.cli,
            ["--output=json", "state", "edit", "sensor.one", "myspecialstate"],
            catch_exceptions=False,
        )

        assert result.exit_code == 0

        assert get.call_count == 1
        assert post.call_count == 1
        assert post.request_history[0].json()['state'] == 'myspecialstate'


def test_state_toggle(basic_entities_text, basic_entities) -> None:
    """Test basic edit of state."""
    with requests_mock.Mocker() as mock:
        mock.get(
            "http://localhost:8123/api/states",
            text=basic_entities_text,
            status_code=200,
        )
        post = mock.post(
            "http://localhost:8123/api/services/homeassistant/toggle",
            text=LIST_EDITED_ENTITY,
            status_code=200,
        )

        runner = CliRunner()
        result = runner.invoke(
            cli.cli,
            ["--output=json", "state", "toggle", "sensor.one"],
            catch_exceptions=False,
        )

        assert result.exit_code == 0
        assert post.call_count == 1

        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 1
        assert isinstance(data[0], dict)


def test_state_filter(default_entities) -> None:
    """Test entities can be listed with filter."""
    with requests_mock.Mocker() as mock:
        mock.get(
            "http://localhost:8123/api/states",
            json=default_entities,
            status_code=200,
        )

        runner = CliRunner()
        result = runner.invoke(
            cli.cli,
            ["--output=json", "state", "list", "bathroom"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 3

        ids = [d['entity_id'] for d in data]

        assert len(ids) == 3
        assert "timer.timer_small_bathroom" in ids
        assert "group.small_bathroom_motionview" in ids
        assert "light.small_bathroom_light" in ids


def test_state_history(default_entities) -> None:
    """Test entities can list history."""
    with requests_mock.Mocker() as mock:
        mock.get(
            "http://localhost:8123/api/states",
            json=default_entities,
            status_code=200,
        )

        mock.get(
            re.compile("http://localhost:8123/api/history/period"),
            json={},
            status_code=200,
            complete_qs=False,
        )

        runner = CliRunner()
        result = runner.invoke(
            cli.cli,
            ["--output=json", "state", "history", "bathroom"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        # TODO: actually have history result testing
