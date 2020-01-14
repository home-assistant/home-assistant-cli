"""Tests file for Home Assistant CLI (hass-cli)."""
import json
from unittest.mock import mock_open, patch

from click.testing import CliRunner
import requests_mock

import homeassistant_cli.autocompletion as autocompletion
import homeassistant_cli.cli as cli
from homeassistant_cli.config import Configuration
from homeassistant_cli.yaml import yaml, dumpyaml


def test_service_list(default_services) -> None:
    """Test services can be listed."""
    with requests_mock.Mocker() as mock:
        mock.get(
            "http://localhost:8123/api/services",
            json=default_services,
            status_code=200,
        )

        runner = CliRunner()
        result = runner.invoke(
            cli.cli,
            ["--output=json", "service", "list"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 12


def test_service_filter(default_services) -> None:
    """Test services can be listed."""
    with requests_mock.Mocker() as mock:
        mock.get(
            "http://localhost:8123/api/services",
            json=default_services,
            status_code=200,
        )

        runner = CliRunner()
        result = runner.invoke(
            cli.cli,
            ["--output=json", "service", "list", "homeassistant\\..*config.*"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 2


def test_service_completion(default_services) -> None:
    """Test completion for services with filter."""
    with requests_mock.Mocker() as mock:
        mock.get(
            'http://localhost:8123/api/services',
            json=default_services,
            status_code=200,
        )

        cfg = Configuration()

        result = autocompletion.services(
            cfg, ["service", "call"], "light.turn"
        )
        assert len(result) == 2

        resultdict = dict(result)

        assert "light.turn_on" in resultdict
        assert "light.turn_off" in resultdict


def test_service_call(default_services) -> None:
    """Test basic call of a service."""
    with requests_mock.Mocker() as mock:

        post = mock.post(
            "http://localhost:8123/api/services/homeassistant/restart",
            json={"result": "bogus"},
            status_code=200,
        )

        runner = CliRunner()
        result = runner.invoke(
            cli.cli,
            ["--output=json", "service", "call", "homeassistant.restart"],
            catch_exceptions=False,
        )

        assert result.exit_code == 0

        assert post.call_count == 1


def test_service_call_with_arguments(default_services) -> None:
    """Test basic call of a service."""
    with requests_mock.Mocker() as mock:

        post = mock.post(
            "http://localhost:8123/api/services/homeassistant/restart",
            json={"result": "bogus"},
            status_code=200,
        )

        runner = CliRunner()
        result = runner.invoke(
            cli.cli,
            ["--output=json", "service", "call", "homeassistant.restart",
             "--arguments", "foo=bar,test=call"],
            catch_exceptions=False,
        )

        assert result.exit_code == 0

        assert post.call_count == 1

        assert post.last_request.json() == {"foo": "bar", "test": "call"}


def test_service_call_with_json(default_services) -> None:
    """Test basic call of a service."""
    with requests_mock.Mocker() as mock:

        post = mock.post(
            "http://localhost:8123/api/services/homeassistant/restart",
            json={"result": "bogus"},
            status_code=200,
        )

        data = {"foo": "bar", "test": True}

        runner = CliRunner()
        result = runner.invoke(
            cli.cli,
            ["--output=json", "service", "call", "homeassistant.restart",
             "--json", json.dumps(data)],
            catch_exceptions=False,
        )

        assert result.exit_code == 0

        assert post.call_count == 1

        assert post.last_request.json() == data


def test_service_call_with_json_stdin(default_services) -> None:
    """Test basic call of a service."""
    with requests_mock.Mocker() as mock:

        post = mock.post(
            "http://localhost:8123/api/services/homeassistant/restart",
            json={"result": "bogus"},
            status_code=200,
        )

        data = {
            "foo": "bar",
            "test": True,
        }

        runner = CliRunner()
        result = runner.invoke(
            cli.cli,
            ["--output=json", "service", "call", "homeassistant.restart",
             "--json", "-"],
            catch_exceptions=False,
            input=json.dumps(data)
        )

        assert result.exit_code == 0

        assert post.call_count == 1

        assert post.last_request.json() == data


def test_service_call_with_yaml(default_services) -> None:
    """Test basic call of a service."""
    with requests_mock.Mocker() as mock:

        post = mock.post(
            "http://localhost:8123/api/services/homeassistant/restart",
            json={"result": "bogus"},
            status_code=200,
        )

        runner = CliRunner()
        result = runner.invoke(
            cli.cli,
            ["--output=json", "service", "call", "homeassistant.restart",
             "--yaml", "foo: bar"],
            catch_exceptions=False,
        )

        assert result.exit_code == 0

        assert post.call_count == 1

        assert post.last_request.json() == {"foo": "bar"}


def test_service_call_with_yaml_file(default_services) -> None:
    """Test basic call of a service."""
    with requests_mock.Mocker() as mock:

        post = mock.post(
            "http://localhost:8123/api/services/homeassistant/restart",
            json={"result": "bogus"},
            status_code=200,
        )

        data = {
            "foo": "bar",
            "test": True,
        }

        open_yaml_file = mock_open(read_data=dumpyaml(yaml(), data=data))

        runner = CliRunner()
        with patch('builtins.open', open_yaml_file) as mocked_open:
            result = runner.invoke(
                cli.cli,
                ["--output=json", "service", "call", "homeassistant.restart",
                 "--yaml", "@yaml_file.yml"],
                catch_exceptions=False,
            )

        assert result.exit_code == 0

        assert post.call_count == 1

        mocked_open.assert_called_once_with("yaml_file.yml", "r")

        assert post.last_request.json() == data
