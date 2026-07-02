from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from config import settings
from constants import MATRICOLA_PATH, MIGRATION_FILE, SUPPORTED_VERSIONS
from mqtt_client import MqttClient
from ssh_client import SshClient

app = FastAPI()


class MigrateRequest(BaseModel):
    serial: str
    software_version: str


def _is_version_valid(version: str) -> None:
    if not any(v in version for v in SUPPORTED_VERSIONS):
        raise ValueError(f"Version not supported: {version}")


def open_ssh_with_mqtt(serial: str, command: int, mqtt_client: MqttClient) -> None:
    try:
        mqtt_client.publish(f"/remoterequest/{serial.zfill(5)}", str(command))
    except Exception as e:
        raise RuntimeError(f"MQTT error: {e}") from e


def _try_port(
    serial: str, command: int, port: int, mqtt_client: MqttClient
) -> SshClient | None:
    print("sono in try port")
    open_ssh_with_mqtt(serial, command, mqtt_client)
    print("sono dopo public")
    ssh_client = SshClient()
    print("ho creato ssh_client")
    ssh_client.connect(port)
    print("dopo il tentativo di collegamento")
    if ssh_client.is_busy(port):
        ssh_client.disconnect()
        return None
    return ssh_client


def find_available_port(serial: str, mqtt_client: MqttClient) -> SshClient:
    print("sono in available port")
    for command, port in settings.command_port_map.items():
        print("port: ", port)
        ssh_client = _try_port(serial, command, port, mqtt_client)
        print("sono dopo la prova della porta")
        if ssh_client is not None:
            return ssh_client

    raise RuntimeError("Nessuna porta disponibile")


def check_serial(serial: str, ssh_client: SshClient) -> None:
    output = ssh_client.execute(f"cat {MATRICOLA_PATH}")
    if output.strip() != serial:
        raise RuntimeError(f"Serial mismatch: expected {serial}, got {output.strip()}")


def create_migration_file(ssh_client: SshClient) -> None:
    try:
        ssh_client.execute(f"touch {MIGRATION_FILE}")
    except Exception as e:
        raise RuntimeError(f"Failed to create migration file: {e}") from e


@app.post("/migrate")
def migrate(request: MigrateRequest) -> JSONResponse:
    ssh_client = None
    mqtt_client = MqttClient()
    try:
        _is_version_valid(request.software_version)
        mqtt_client.connect()
        print("dopo mqtt connect")
        ssh_client = find_available_port(request.serial, mqtt_client)
        print("sono ssh client", ssh_client)
        check_serial(request.serial, ssh_client)
        create_migration_file(ssh_client)

    except ValueError as e:
        return JSONResponse(status_code=400, content={"error": str(e)})
    except RuntimeError as e:
        return JSONResponse(status_code=503, content={"error": str(e)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        if ssh_client:
            ssh_client.disconnect()
        if mqtt_client:
            mqtt_client.publish(
                f"/remoterequest/{request.serial.zfill(5)}", str(settings.close_command)
            )
            mqtt_client.disconnect()

    return JSONResponse(status_code=200, content={"message": "Migration started"})
