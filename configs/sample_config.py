config = {
    "terrain": {"width": 10, "height": 10},
    "simulation": {
        "steps": 50,
        "storm_turn": 60,
    },
    "resources": [
        {"type": "CRYSTAL", "position": [2, 3]},
        {"type": "METAL", "position": [4, 5]},
        {"type": "STRUCTURE", "position": [6, 6]},
    ],
    "agents": [
        {"type": "REACTIVE", "position": [0, 1]},
        {"type": "STATE_BASED", "position": [1, 0]},
        {"type": "GOAL_BASED", "position": [2, 2]},
        {"type": "COOPERATIVE", "position": [3, 3]},
    ],
    "obstacles": [(4, 4), (4, 5), (5, 4), (1, 6), (2, 6), (3, 6), (4, 6)],
}
