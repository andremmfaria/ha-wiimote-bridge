from typing import TypedDict


class DiscoveryStats(TypedDict):
    controllers: int
    entities: int
    failed: int
