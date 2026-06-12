# solver.py
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

from __future__ import annotations

from dataclasses import dataclass
from .data import PIECES


@dataclass(frozen=True)
class Placement:
    piece_id: str
    row: int
    col: int
    rotation: int
    flipped: bool
    cells: tuple[tuple[int, int], ...]

    def as_dict(self) -> dict:
        return {
            "piece_id": self.piece_id,
            "row": self.row,
            "col": self.col,
            "rotation": self.rotation,
            "flipped": self.flipped,
            "cells": [list(cell) for cell in self.cells],
        }


def shape_to_cells(shape: list[list[int]]) -> frozenset[tuple[int, int]]:
    cells = set()

    for row, values in enumerate(shape):
        for col, value in enumerate(values):
            if value:
                cells.add((row, col))

    return frozenset(cells)


def transformed_cells(
    cells: frozenset[tuple[int, int]],
    rotation: int = 0,
    flipped: bool = False,
) -> tuple[tuple[int, int], ...]:
    points = list(cells)

    if flipped:
        max_col = max(col for _, col in points)
        points = [(row, max_col - col) for row, col in points]

    for _ in range(rotation % 4):
        max_row = max(row for row, _ in points)
        points = [(col, max_row - row) for row, col in points]

    min_row = min(row for row, _ in points)
    min_col = min(col for _, col in points)

    return tuple(sorted((row - min_row, col - min_col) for row, col in points))


def piece_orientations(
    piece_id: str,
    allow_flips: bool = False,
) -> tuple[tuple[int, bool, tuple[tuple[int, int], ...]], ...]:
    base_cells = shape_to_cells(PIECES[piece_id]["shape"])
    orientations = []
    seen = set()
    flips = (False, True) if allow_flips else (False,)

    for flipped in flips:
        for rotation in range(4):
            cells = transformed_cells(base_cells, rotation, flipped)

            if cells in seen:
                continue

            seen.add(cells)
            orientations.append((rotation, flipped, cells))

    return tuple(orientations)


def _placements_for_level(level: dict) -> tuple[list[Placement], set[tuple[int, int]]]:
    width = int(level.get("width", level.get("size", 0)))
    height = int(level.get("height", level.get("size", width)))
    walls = {tuple(wall) for wall in level.get("walls", [])}
    target = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in walls
    }
    placements = []

    for piece_id in level.get("pieces", []):
        if piece_id not in PIECES:
            continue

        for rotation, flipped, shape_cells in piece_orientations(
            piece_id,
            allow_flips=level.get("allow_flips", False),
        ):
            max_row = max(row for row, _ in shape_cells)
            max_col = max(col for _, col in shape_cells)

            for row in range(height - max_row):
                for col in range(width - max_col):
                    cells = tuple(sorted((row + dr, col + dc) for dr, dc in shape_cells))

                    if all(cell in target for cell in cells):
                        placements.append(
                            Placement(piece_id, row, col, rotation, flipped, cells)
                        )

    return placements, target


def solve_level(level: dict, max_solutions: int = 1) -> list[dict] | None:
    placements, uncovered = _placements_for_level(level)

    if not uncovered:
        return []

    by_cell = {cell: [] for cell in uncovered}

    for placement in placements:
        for cell in placement.cells:
            by_cell[cell].append(placement)

    if any(not choices for choices in by_cell.values()):
        return None

    solution: list[Placement] = []
    solutions: list[list[Placement]] = []

    def search(remaining: set[tuple[int, int]]) -> bool:
        if not remaining:
            solutions.append(solution.copy())
            return len(solutions) >= max_solutions

        cell = min(remaining, key=lambda item: len(by_cell[item]))

        for placement in by_cell[cell]:
            placement_cells = set(placement.cells)

            if not placement_cells <= remaining:
                continue

            solution.append(placement)

            if search(remaining - placement_cells):
                return True

            solution.pop()

        return False

    search(set(uncovered))

    if not solutions:
        return None

    return [placement.as_dict() for placement in solutions[0]]


def is_solvable(level: dict) -> bool:
    return solve_level(level) is not None


if __name__ == "__main__":
    from .proc import generate_level

    level = generate_level()
    solution = solve_level(level)

    print(level)
    print(solution)
