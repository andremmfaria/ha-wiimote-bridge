from typing import Any, Literal, TypeAlias


MqttTransport = Literal["tcp", "websockets"]
MessagePayload: TypeAlias = dict[str, Any]
DiscoveryStats: TypeAlias = dict[str, int]