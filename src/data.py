PIECES = {
    "square2": {"name": "2 × 2", "shape": [[1, 1], [1, 1]]},
    "square3": {"name": "3 × 3", "shape": [[1, 1, 1], [1, 1, 1], [1, 1, 1]]},
    "bar3": {"name": "3 Bar", "shape": [[1, 1, 1]]},
    "l3": {"name": "Small L", "shape": [[1, 0], [1, 1]]},
}

LEVELS = [
    {"title": "Level 1", "subtitle": "4 × 4 · 2 × 2 blocks", "width": 4, "height": 4, "pieces": ["square2"], "walls": []},
    {"title": "Level 2", "subtitle": "6 × 6 · 3 × 3 blocks", "width": 6, "height": 6, "pieces": ["square3"], "walls": []},
    {"title": "Level 3", "subtitle": "6 × 6 · rotations", "width": 6, "height": 6, "pieces": ["square2", "bar3", "l3"], "walls": [[2, 2], [3, 3]]},
    {"title": "Level 4", "subtitle": "8 × 8 · walls force 2 × 2 blocks", "width": 8, "height": 8, "pieces": ["square3", "square2"], "walls": [[1, 6], [2, 6], [3, 6], [4, 4], [6, 1], [6, 2], [6, 3]]},
]
