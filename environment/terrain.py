import random
from dataclasses import dataclass
from typing import List, Tuple, Set


@dataclass(frozen=True)
class Position:
    x: int
    y: int


class Terrain:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid = [[None for _ in range(width)] for _ in range(height)]
        self.obstacles: Set[Tuple[int, int]] = set()

    def add_obstacle(self, x: int, y: int):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.obstacles.add((x, y))

    def is_free(self, x: int, y: int) -> bool:
        return (
            0 <= x < self.width
            and 0 <= y < self.height
            and (x, y) not in self.obstacles
        )

    def get_random_adjacent_position(self, pos: Position) -> Position:
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        valid = [
            Position(pos.x + dx, pos.y + dy)
            for dx, dy in directions
            if self.is_free(pos.x + dx, pos.y + dy)
        ]
        return random.choice(valid) if valid else pos


def safe_move(grid, agent, new_pos, obstacles):
    x, y = new_pos
    if (x, y) in obstacles:
        return
    if 0 <= x < grid.width and 0 <= y < grid.height:
        grid.move_agent(agent, new_pos)
