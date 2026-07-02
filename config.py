# config.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ssh_host: str
    ssh_ports: list[int]
    ssh_user: str
    ssh_password: str
    ssh_key_path: str
    mqtt_broker: str
    mqtt_port: int
    mqtt_path: str
    mqtt_user: str
    mqtt_password: str
    command_port_map: dict[int, int]
    close_command: int

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


# pydantic reads values before calls __init__ so workaround with ignore type
settings = Settings()  # type: ignore
