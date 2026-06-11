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

import random
from .solver import piece_orientations, solve_level # doesn't exist for now


PIECE_POOL = [
    "square2",
    "bar3",
    "l3",
    "t4",
    "z4",
    "z4_2",
    "l4",
    "l4_2",
    "bar4",
    "plus5",
    "corner5",
]


def _placement_cells(row, col, shape_cells):
    return tuple(sorted((row + dr, col + dc) for dr, dc in shape_cells))


def _in_bounds(cells, width, height):
    return all(0 <= row < height and 0 <= col < width for row, col in cells)


def _touches_existing(cells, occupied):
    if not occupied:
        return True

    for row, col in cells:
        neighbors = (
            (row - 1, col),
            (row + 1, col),
            (row, col - 1),
            (row, col + 1),
        )

        if any(neighbor in occupied for neighbor in neighbors):
            return True

    return False


def _build_candidate(width, height, rng, min_placements, max_placements):
    piece_count = rng.randint(3, 5)
    allowed_pieces = rng.sample(PIECE_POOL, piece_count)
    target_placements = rng.randint(min_placements, max_placements)
    occupied = set()
    placed = []
    retries = 0

    while len(placed) < target_placements and retries < 500:
        retries += 1
        piece_id = rng.choice(allowed_pieces)
        rotation, flipped, shape_cells = rng.choice(piece_orientations(piece_id))
        max_row = max(row for row, _ in shape_cells)
        max_col = max(col for _, col in shape_cells)

        if max_row >= height or max_col >= width:
            continue

        row = rng.randrange(height - max_row)
        col = rng.randrange(width - max_col)
        cells = _placement_cells(row, col, shape_cells)

        if not _in_bounds(cells, width, height):
            continue

        if any(cell in occupied for cell in cells):
            continue

        if not _touches_existing(cells, occupied):
            continue

        occupied.update(cells)
        placed.append(
            {
                "piece_id": piece_id,
                "row": row,
                "col": col,
                "rotation": rotation,
                "flipped": flipped,
                "cells": [list(cell) for cell in cells],
            }
        )

    return occupied, placed


def generate_level(
    width=None,
    height=None,
    wall_count=None,
    min_placements=5,
    max_placements=8,
    seed=None,
):
    rng = random.Random(seed)
    width = width or rng.choice([6, 7, 8])
    height = height or width
    min_free_cells = 18

    if wall_count is not None:
        min_free_cells = max(min_free_cells, width * height - wall_count)

    for _ in range(300):
        occupied, intended_solution = _build_candidate(
            width,
            height,
            rng,
            min_placements,
            max_placements,
        )

        used_piece_types = {placement["piece_id"] for placement in intended_solution}

        if len(intended_solution) < min_placements:
            continue

        if len(occupied) < min_free_cells:
            continue

        if len(used_piece_types) < 2:
            continue

        walls = [
            [row, col]
            for row in range(height)
            for col in range(width)
            if (row, col) not in occupied
        ]
        level = {
            "title": "Generated Puzzle",
            "subtitle": f"{width} × {height} · {len(intended_solution)} pieces minimum",
            "width": width,
            "height": height,
            "pieces": sorted(used_piece_types),
            "walls": walls,
        }
        solution = solve_level(level)

        if solution and len(solution) >= min_placements:
            return level

    raise RuntimeError("Could not generate a solvable procedural level")


if __name__ == "__main__":
    level = generate_level(
        width=8,
        height=8,
        min_placements=6,
    )
    solution = solve_level(level)

    print(f" here is the lvl generated:\n{level}")
    print(f" here is one solution:\n{solution}")
