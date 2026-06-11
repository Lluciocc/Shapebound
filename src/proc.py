# proc.py
#
# Copyright 2026 Lluciocc
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Im trying to add some procedural generation
# this is only a test
# this is random
from dataclasses import dataclass
import random
import json


@dataclass
class Shape:
    name: str
    cells: list[tuple[int, int]]


SHAPES = [
    Shape("square2", [
        (0, 0), (1, 0),
        (0, 1), (1, 1),
    ]),
    Shape("square3", [
        (0, 0), (1, 0), (2, 0),
        (0, 1), (1, 1), (2, 1),
        (0, 2), (1, 2), (2, 2),
    ]),
]


def can_place(board, shape, x, y):
    height = len(board)
    width = len(board[0])

    for dx, dy in shape.cells:
        nx = x + dx
        ny = y + dy

        if nx < 0 or ny < 0:
            return False

        if nx >= width or ny >= height:
            return False

        if board[ny][nx] != 0:
            return False

    return True


def place(board, shape, x, y, value):
    for dx, dy in shape.cells:
        board[y + dy][x + dx] = value


def generate_level(width=8, height=8, wall_count=2):
    board = [[0 for _ in range(width)] for _ in range(height)]
    walls = []

    while len(walls) < wall_count:
        x = random.randrange(width)
        y = random.randrange(height)

        if board[y][x] == 0:
            board[y][x] = -1
            walls.append([x, y])

    piece_id = 1

    attempts = 0

    while attempts < 1000:
        attempts += 1

        shape = random.choice(SHAPES)

        x = random.randrange(width)
        y = random.randrange(height)

        if can_place(board, shape, x, y):
            place(board, shape, x, y, piece_id)
            piece_id += 1

    return { # its json because the window parse json for now
        "title": "My ahh level",
        "subtitle": "subtitle",
        "width": width,
        "height": height,
        "pieces": [
            "square2",
            "square3"
        ],
        "walls": walls
    }


if __name__ == "__main__":
    level = generate_level(
        width=8,
        height=8,
        wall_count=3
    )

    print(f" here is the lvl generated:\n{level}")
