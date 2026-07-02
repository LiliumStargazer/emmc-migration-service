import time

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
from paho.mqtt.properties import Properties
from paho.mqtt.reasoncodes import ReasonCode

from config import settings


class MqttClient:
    def __init__(self) -> None:
        self._client = mqtt.Client(
            CallbackAPIVersion.VERSION2,
            transport="websockets",  # ← usa quello importato
        )
        self._client.tls_set()  # abilita SSL
        self._client.username_pw_set(settings.mqtt_user, settings.mqtt_password)
        self._client.ws_set_options(path=settings.mqtt_path)
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect

    def connect(self) -> None:
        self._client.connect(
            settings.mqtt_broker, port=settings.mqtt_port, keepalive=180
        )
        self._client.loop_start()
        time.sleep(1)

    def disconnect(self) -> None:
        self._client.loop_stop()
        self._client.disconnect()

    def publish(self, topic: str, payload: str) -> None:
        print(f"Publishing to {topic}: {payload}")
        result = self._client.publish(topic, payload)
        print(f"Publish result: {result.rc}")

    def subscribe(self, topic: str) -> None:
        self._client.subscribe(topic)

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: None,
        flags: mqtt.ConnectFlags,
        rc: ReasonCode,
        properties: Properties | None = None,
    ) -> None:
        if rc.is_failure:
            print(f"MQTT connection failed: {rc}")
        else:
            print("MQTT connected")

    def _on_message(
        self, client: mqtt.Client, userdata: None, message: mqtt.MQTTMessage
    ) -> None:
        print(f"Message received: {message.topic} → {message.payload.decode()}")

    def _on_disconnect(
        self,
        client: mqtt.Client,
        userdata: None,
        disconnect_flags: mqtt.DisconnectFlags,
        rc: ReasonCode,
        properties: Properties | None = None,
    ) -> None:
        print(f"MQTT disconnected: {rc}")
