from dataclasses import dataclass
from enum import Enum
from typing import Dict
from .terrain import Position


class ResourceType(Enum):
    CRYSTAL = 10
    METAL = 20
    STRUCTURE = 50


@dataclass
class Resource:
    resource_type: ResourceType
    position: tuple[int, int]
    collected: bool = False


class ResourceMap:
    def __init__(self):
        self.resources: Dict[Position, Resource] = {}

    def add_resource(self, resource: Resource):
        self.resources[resource.position] = resource

    def get_resource(self, position: Position):
        return self.resources.get(position)

    def collect_resource(self, position: Position):
        resource = self.resources.get(position)
        if resource and not resource.collected:
            resource.collected = True
            return resource.resource_type.value
        return 0

    def has_small_resource(self, position: Position) -> bool:
        resource = self.resources.get(position)
        return (
            resource
            and not resource.collected
            and resource.resource_type == ResourceType.CRYSTAL
        )
