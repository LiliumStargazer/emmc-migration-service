# ssh_client.py

import paramiko

from config import settings


class SshClient:
    def __init__(self) -> None:
        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self, port: int) -> None:
        self._client.connect(
            hostname=settings.ssh_host,
            port=port,
            key_filename=settings.ssh_key_path,
            username=settings.ssh_user,
            password=settings.ssh_password,
        )

    def disconnect(self) -> None:
        self._client.close()

    def execute(self, command: str) -> str:
        _, stdout, stderr = self._client.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()
        if error:
            raise RuntimeError(f"SSH error: {error}")
        return output

    def is_busy(self, port: int) -> bool:
        hex_port = format(port, "04X")
        output = self.execute("cat /proc/net/tcp")
        established = [
            line
            for line in output.strip().splitlines()
            if hex_port in line and line.split()[3] == "01"
        ]
        # ogni connessione appare 2 volte, la tua occupa già 2 righe
        return len(established) > 2
