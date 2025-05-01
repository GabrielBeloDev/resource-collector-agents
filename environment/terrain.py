import random
from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class Position:
    x: int
    y: int


class Terrain:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid = [[None for _ in range(width)] for _ in range(height)]
        self.obstacles = set()

    def is_valid(self, position: Position) -> bool:
        return (
            0 <= position.x < self.width
            and 0 <= position.y < self.height
            and position not in self.obstacles
        )

    def add_obstacle(self, position: Position):
        if self.is_valid(position):
            self.obstacles.add(position)

    def get_random_adjacent_position(self, position: Position) -> Position:
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        valid_positions = [
            Position(position.x + dx, position.y + dy)
            for dx, dy in directions
            if self.is_valid(Position(position.x + dx, position.y + dy))
        ]
        return random.choice(valid_positions) if valid_positions else position
