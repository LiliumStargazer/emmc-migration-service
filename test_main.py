# test_main.py
import pytest
from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

from config import settings
from main import (
    _is_version_valid,
    app,
    check_serial,
    create_migration_file,
    find_available_port,
)
from mqtt_client import MqttClient
from ssh_client import SshClient

client = TestClient(app)


def test_version_valid() -> None:
    _is_version_valid("8.01")  # non deve lanciare eccezioni


def test_version_invalid() -> None:
    with pytest.raises(ValueError):
        _is_version_valid("8.02")  # deve lanciare ValueError


def test_check_serial_valid(mocker: MockerFixture) -> None:
    ssh_client = mocker.MagicMock(spec=SshClient)
    ssh_client.execute.return_value = "21546\n"
    check_serial("21546", ssh_client)  # non deve lanciare eccezioni


def test_check_serial_invalid(mocker: MockerFixture) -> None:
    ssh_client = mocker.MagicMock(spec=SshClient)
    ssh_client.execute.return_value = "99999\n"
    with pytest.raises(RuntimeError):
        check_serial("21546", ssh_client)


def test_create_migration_file_success(mocker: MockerFixture) -> None:
    ssh_client = mocker.MagicMock(spec=SshClient)
    create_migration_file(ssh_client)
    ssh_client.execute.assert_called_once()


def test_create_migration_file_failure(mocker: MockerFixture) -> None:
    ssh_client = mocker.MagicMock(spec=SshClient)
    ssh_client.execute.side_effect = Exception("SSH error")
    with pytest.raises(RuntimeError):
        create_migration_file(ssh_client)


def test_find_available_port_success(mocker: MockerFixture) -> None:
    mqtt_client = mocker.MagicMock(spec=MqttClient)
    ssh_client_mock = mocker.MagicMock(spec=SshClient)
    ssh_client_mock.is_busy.return_value = False

    mocker.patch("main.SshClient", return_value=ssh_client_mock)
    mocker.patch.object(settings, "command_port_map", {25: 55501})

    result = find_available_port("21546", mqtt_client)
    assert result == ssh_client_mock


def test_find_available_port_all_busy(mocker: MockerFixture) -> None:
    mqtt_client = mocker.MagicMock(spec=MqttClient)
    ssh_client_mock = mocker.MagicMock(spec=SshClient)
    ssh_client_mock.is_busy.return_value = True

    mocker.patch("main.SshClient", return_value=ssh_client_mock)
    mocker.patch.object(settings, "command_port_map", {25: 55501, 26: 55502})

    with pytest.raises(RuntimeError):
        find_available_port("21546", mqtt_client)


def test_migrate_invalid_version() -> None:
    response = client.post(
        "/migrate", json={"serial": "21546", "software_version": "0.0.1"}
    )
    assert response.status_code == 400


def test_migrate_success(mocker: MockerFixture) -> None:
    ssh_client_mock = mocker.MagicMock(spec=SshClient)
    ssh_client_mock.is_busy.return_value = False
    ssh_client_mock.execute.return_value = "21546"

    mocker.patch("main.SshClient", return_value=ssh_client_mock)
    mocker.patch("main.MqttClient", return_value=mocker.MagicMock(spec=MqttClient))
    mocker.patch.object(settings, "command_port_map", {25: 55501})

    response = client.post(
        "/migrate", json={"serial": "21546", "software_version": "8.01"}
    )
    assert response.status_code == 200


def test_migrate_no_ports_available(mocker: MockerFixture) -> None:
    ssh_client_mock = mocker.MagicMock(spec=SshClient)
    ssh_client_mock.is_busy.return_value = True

    mocker.patch("main.SshClient", return_value=ssh_client_mock)
    mocker.patch("main.MqttClient", return_value=mocker.MagicMock(spec=MqttClient))
    mocker.patch.object(settings, "command_port_map", {25: 55501})

    response = client.post(
        "/migrate", json={"serial": "21546", "software_version": "8.01"}
    )
    assert response.status_code == 503
