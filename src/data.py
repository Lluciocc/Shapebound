# data.py
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
PIECES = {
    "square2": {"name": "2 × 2", "shape": [[1, 1], [1, 1]]},
    "square3": {"name": "3 × 3", "shape": [[1, 1, 1], [1, 1, 1], [1, 1, 1]]},
    "bar3": {"name": "3 Bar", "shape": [[1, 1, 1]]},
    "l3": {"name": "Small L", "shape": [[1, 0], [1, 1]]},
    "t4": {"name": "T Shape", "shape": [[1,1,1],[0,1,0]]},
    "z4": {"name": "Z Shape", "shape": [[1,1,0],[0,1,1]]},
    "z4_2": {"name": "Z Shape (2)", "shape": [[0,1,1],[1,1,0]]},
    "s4": {"name": "S Shape", "shape": [[0,1,1],[1,1,0]]},
    "l4": {"name": "Large L", "shape": [[1,0],[1,0],[1,1]]},
    "l4_2": {"name": "Large L (2)", "shape": [[1,1],[1,0],[1,0]]},
    "bar4": {"name": "4 Bar", "shape": [[1,1,1,1]]},
    "plus5": {"name": "Plus", "shape": [[0,1,0],[1,1,1],[0,1,0]]},
    "corner5": {"name": "Corner", "shape": [[1,0,0],[1,0,0],[1,1,1]]},
}

LEVELS = [
    {"title": "Level 1", "subtitle": "2 × 2 basics", "width": 4, "height": 4, "pieces": ["square2"], "walls": [[0,0],[0,1],[0,2],[0,3],[1,0],[1,1],[2,0],[2,1],[3,0],[3,1],[3,2],[3,3]]},
    {"title": "Level 2", "subtitle": "3 × 3 basics", "width": 4, "height": 4, "pieces": ["square3"], "walls": [[0,0],[1,0],[2,0],[3,0],[3,1],[3,2],[3,3]]},
    {"title": "Level 3", "subtitle": "Bars and small L", "width": 4, "height": 4, "pieces": ["square2", "bar3", "l3"], "walls": [[0,2],[0,3],[1,0],[1,3],[2,3],[3,3]]},
    {"title": "Level 4", "subtitle": "Squares together", "width": 5, "height": 5, "pieces": ["square3", "square2"], "walls": [[0,3],[0,4],[1,3],[1,4],[3,0],[4,0],[4,3],[4,4]]},
    {"title": "Level 5", "subtitle": "T required", "width": 4, "height": 4, "pieces": ["square2", "t4"], "walls": [[0,0],[0,1],[2,3],[3,0]]},
    {"title": "Level 6", "subtitle": "Z required", "width": 4, "height": 4, "pieces": ["square2", "z4", "z4_2"], "walls": [[0,0],[0,3],[3,0],[3,3]]},
    {"title": "Level 7", "subtitle": "Long shapes", "width": 4, "height": 4, "pieces": ["bar4", "l4"], "walls": [[0,1],[0,3],[1,1],[1,3],[2,3],[3,0],[3,1],[3,3]]},
    {"title": "Level 8", "subtitle": "Corner required", "width": 4, "height": 4, "pieces": ["corner5", "square2"], "walls": [[0,3],[3,0]]},
    {"title": "Level 9", "subtitle": "Plus required", "width": 4, "height": 4, "pieces": ["plus5", "square2"], "walls": [[0,2],[0,3],[1,3],[2,0],[3,0],[3,1],[3,3]]},
    {"title": "Level 10", "subtitle": "Rotation mix", "width": 4, "height": 4, "pieces": ["l3", "l4_2", "bar3"], "walls": [[0,3],[1,0],[1,1],[1,3],[3,0],[3,1]]},
    {"title": "Level 11", "subtitle": "Mixed shapes", "width": 4, "height": 4, "pieces": ["square2", "t4", "z4"], "walls": [[0,0],[3,0],[3,1],[3,3]]},
    {"title": "Level 12", "subtitle": "Dense plus", "width": 5, "height": 5, "pieces": ["square3", "plus5"], "walls": [[0,3],[0,4],[1,3],[1,4],[2,4],[3,0],[3,1],[4,0],[4,1],[4,2],[4,4]]},
    {"title": "Level 13", "subtitle": "Long mix", "width": 4, "height": 4, "pieces": ["bar4", "l4", "square2"], "walls": [[0,0],[1,0],[1,1],[3,2]]},
    {"title": "Level 14", "subtitle": "Corner and square3", "width": 4, "height": 4, "pieces": ["square3", "corner5"], "walls": [[0,3],[3,0]]},
    {"title": "Level 15", "subtitle": "Advanced rotation", "width": 4, "height": 4, "pieces": ["l4_2", "bar4", "t4"], "walls": [[1,1],[1,3],[3,1],[3,2]]},
    {"title": "Level 16", "subtitle": "Challenge mix", "width": 5, "height": 5, "pieces": ["plus5", "corner5", "square2"], "walls": [[0,0],[0,2],[2,0],[3,0],[3,1],[3,3],[3,4],[4,0],[4,1],[4,3],[4,4]]},
    {"title": "Level 17", "subtitle": "Final test", "width": 6, "height": 6, "pieces": ["square3", "plus5", "corner5", "t4"], "walls": [[0,0],[0,2],[0,4],[0,5],[1,4],[1,5],[2,0],[2,2],[3,0],[3,5],[4,5],[5,0],[5,5]]},
]
