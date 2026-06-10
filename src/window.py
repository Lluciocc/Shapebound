# window.py
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

import json
import random
from dataclasses import dataclass
from pathlib import Path

from gi.repository import Adw, Gtk, Gdk, GLib, GObject, Gio
from .progress import load_progress_for, save_progress_for

COLORS = ["blue", "green", "yellow", "purple", "orange", "red", "teal"]

# todo: add procedural levels
#todo: add a menu (procedural, made by me)
# todo: add progression
# 

@dataclass(frozen=True)
class Piece:
    id: str
    name: str
    cells: frozenset[tuple[int, int]]


# those fallbacks are use only in the real json file are missing.... 
# I mean, they should always be there, but if something goes wrong with the file loading we don't want the whole app to break
FALLBACK_PIECES = {
    "square2": {"name": "2 × 2", "shape": [[1, 1], [1, 1]]},
    "square3": {"name": "3 × 3", "shape": [[1, 1, 1], [1, 1, 1], [1, 1, 1]]},
    "bar3": {"name": "3 Bar", "shape": [[1, 1, 1]]},
    "l3": {"name": "Small L", "shape": [[1, 0], [1, 1]]},
}

FALLBACK_LEVELS = [
    {"title": "Level 1", "subtitle": "4 × 4 · 2 × 2 blocks", "width": 4, "height": 4, "pieces": ["square2"], "walls": []},
    {"title": "Level 2", "subtitle": "6 × 6 · 3 × 3 blocks", "width": 6, "height": 6, "pieces": ["square3"], "walls": []},
    {"title": "Level 3", "subtitle": "6 × 6 · rotations", "width": 6, "height": 6, "pieces": ["square2", "bar3", "l3"], "walls": [[2, 2], [3, 3]]},
    {"title": "Level 4", "subtitle": "8 × 8 · walls force 2 × 2 blocks", "width": 8, "height": 8, "pieces": ["square3", "square2"], "walls": [[1, 6], [2, 6], [3, 6], [4, 4], [6, 1], [6, 2], [6, 3]]},
]


def project_root() -> Path:
    # simple helper to find the project root from this file
    # keeps code easy to read when loading data files
    return Path(__file__).resolve().parents[1]


def shape_to_cells(shape):
    # convert a 2d shape matrix to a set of (r, c) cells
    # used to store piece shapes in a compact form
    cells = set()
    for r, row in enumerate(shape):
        for c, value in enumerate(row):
            # truthy value means this cell is part of the shape
            if value:
                cells.add((r, c))
    return frozenset(cells)


@Gtk.Template(resource_path='/com/github/Lluciocc/Shapebound/window.ui')
class ShapeboundWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'ShapeboundWindow'

    window_title = Gtk.Template.Child()
    previous_button = Gtk.Template.Child()
    next_button = Gtk.Template.Child()
    reset_button = Gtk.Template.Child()
    rotate_button = Gtk.Template.Child()
    check_button = Gtk.Template.Child()
    piece_box = Gtk.Template.Child()
    board_grid = Gtk.Template.Child()
    score_label = Gtk.Template.Child()
    feedback_label = Gtk.Template.Child()
    record_label = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pieces = self._load_piece_library()
        self.levels = self._load_levels()
        self.level_index = 0
        self.level = None
        self.width = 0
        self.height = 0
        self.walls = set()
        self.allowed_piece_ids = []
        self.selected_piece_id = None
        self.rotation = 0
        self.flipped = False
        self.score = 0
        self.moves = 0
        # ensure UI shows current score immediately when a level loads
        try:
            self._update_score()
        except Exception:
            pass
        self.next_placement_id = 1
        self.board = []
        self.buttons = {}
        self.placements = {}
        self.preview_cells = set()
        self.hovered_placement_id = None
        self.undo_stack = []
        self.redo_stack = []
        self.victory_dialog_open = False
        self._load_css()
        self._connect_ui()
        self._install_actions()
        self.load_level(0)

    def _load_piece_library(self):
        data_file = project_root() / 'data' / 'pieces.json'
        data = FALLBACK_PIECES
        if data_file.exists():
            try:
                data = json.loads(data_file.read_text(encoding='utf-8'))
            except Exception:
                data = FALLBACK_PIECES
        # build the piece objects
        # note: if the json is broken we just use fallback pieces, no crash
        return {pid: Piece(pid, info.get('name', pid), shape_to_cells(info['shape'])) for pid, info in data.items()}

    def _load_levels(self):
        levels_dir = project_root() / 'data' / 'levels'
        levels = []
        if levels_dir.exists():
            for path in sorted(levels_dir.glob('*.json')):
                try:
                    levels.append(json.loads(path.read_text(encoding='utf-8')))
                except Exception:
                    pass
        # try to read levels from disk, if nothing found use fallback set
        return levels or FALLBACK_LEVELS

    def _load_css(self):
        provider = Gtk.CssProvider()
        provider.load_from_resource('/com/github/Lluciocc/Shapebound/style.css')
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def _connect_ui(self):
        # connect ui signals, be defensive: template children may be missing
        if getattr(self, 'previous_button', None):
            self.previous_button.connect('clicked', lambda *_: self.load_level((self.level_index - 1) % len(self.levels)))
        if getattr(self, 'next_button', None):
            self.next_button.connect('clicked', lambda *_: self.load_level((self.level_index + 1) % len(self.levels)))
        if getattr(self, 'reset_button', None):
            self.reset_button.connect('clicked', lambda *_: self.reset_board())
        if getattr(self, 'rotate_button', None):
            self.rotate_button.connect('clicked', lambda *_: self.rotate_selected())
        if getattr(self, 'check_button', None):
            self.check_button.connect('clicked', lambda *_: self.check_board(show_incomplete=True))
        # add scroll controller only if board_grid exists
        if getattr(self, 'board_grid', None):
            scroll = Gtk.EventControllerScroll.new(Gtk.EventControllerScrollFlags.VERTICAL)
            scroll.connect('scroll', self._on_scroll_rotate) # scroll wheel rotates piece while hovering board
            self.board_grid.add_controller(scroll)
       

    def _install_actions(self):
        actions = {
            'rotate': lambda *_: self.rotate_selected(1),
            'rotate-back': lambda *_: self.rotate_selected(-1),
            'flip': lambda *_: self.flip_selected(),
            'undo': lambda *_: self.undo(),
            'redo': lambda *_: self.redo(),
            'delete-piece': lambda *_: self.remove_hovered_piece(),
            'restart': lambda *_: self.load_level(self.level_index),
            'previous-piece': lambda *_: self.select_relative_piece(-1),
            'next-piece': lambda *_: self.select_relative_piece(1),
            'check': lambda *_: self.check_board(show_incomplete=True),
        }
        for name, callback in actions.items():
            action = Gio.SimpleAction.new(name, None)
            action.connect('activate', callback)
            self.add_action(action)
        app = self.get_application()
        if app:
            app.set_accels_for_action('win.rotate', ['r', 'space'])
            app.set_accels_for_action('win.rotate-back', ['<shift>r'])
            app.set_accels_for_action('win.flip', ['f'])
            app.set_accels_for_action('win.undo', ['<control>z'])
            app.set_accels_for_action('win.redo', ['<control><shift>z', '<control>y'])
            app.set_accels_for_action('win.delete-piece', ['Delete', 'BackSpace'])
            app.set_accels_for_action('win.restart', ['<control>r'])
            app.set_accels_for_action('win.previous-piece', ['Left'])
            app.set_accels_for_action('win.next-piece', ['Right'])
            app.set_accels_for_action('win.check', ['c'])

    def _on_scroll_rotate(self, _controller, _dx, dy):
        # dy > 0 means scroll down, we map that to rotate direction
        self.rotate_selected(1 if dy > 0 else -1)
        return True

    def load_level(self, index):
        # load a level and reset most of the runtime state
        # keeps UI tidy and predictable when switching levels
        self.victory_dialog_open = False
        self.level_index = index
        self.level = self.levels[index]
        self.width = int(self.level.get('width', self.level.get('size', 6)))
        self.height = int(self.level.get('height', self.level.get('size', self.width)))
        self.walls = {tuple(w) for w in self.level.get('walls', [])}
        self.allowed_piece_ids = [pid for pid in self.level.get('pieces', []) if pid in self.pieces]
        if not self.allowed_piece_ids:
            self.allowed_piece_ids = [next(iter(self.pieces.keys()))]
        self.selected_piece_id = self.allowed_piece_ids[0]
        self.rotation = 0
        self.flipped = False
        self.score = 0
        self.moves = 0
        self.next_placement_id = 1
        self.board = [[None for _ in range(self.width)] for _ in range(self.height)]
        self.placements = {}
        self.undo_stack = []
        self.redo_stack = []
        self.hovered_placement_id = None
        # set title/subtitle if the header widget exists, otherwise set window title
        title = self.level.get('title', f'Level {index + 1}')
        subtitle = self.level.get('subtitle', 'Fill the board with reusable polyominoes')
        if getattr(self, 'window_title', None):
            try:
                self.window_title.set_title(title)
                self.window_title.set_subtitle(subtitle)
            except Exception:
                # fallback to the window's title if the template child is weird
                try:
                    self.set_title(title)
                except Exception:
                    pass
        else:
            try:
                self.set_title(title)
            except Exception:
                pass
        self._build_pieces()
        self._build_board()
        self._set_feedback('Drag a piece, or tap a piece then tap the board.', None)
        self._update_score()
        # show previous best for this level if present
        try:
            prog = load_progress_for(self.level_index)
            if prog:
                print("A best score has been found")
                text = f"Best: Score {prog.get('score',0)} · Moves {prog.get('moves',0)}"
                self._set_feedback(text, 'success')
                if getattr(self, 'record_label', None):
                    try:
                        self.record_label.set_label(text)
                        self.record_label.remove_css_class('success')
                        self.record_label.remove_css_class('error')
                        self.record_label.add_css_class('success')
                    except Exception:
                        pass
            else:
                print("No best score found")
                if getattr(self, 'record_label', None):
                    try:
                        self.record_label.set_label('')
                    except Exception:
                        pass
        except Exception as e:
            pass

    def generate_level(self):
        size = random.choice([6, 8])
        walls = set()
        if size == 8:
            for _ in range(random.randint(3, 7)):
                walls.add((random.randrange(size), random.randrange(size)))
        generated = {
            "title": "Generated Puzzle",
            "subtitle": f"{size} × {size} · generated layout",
            "width": size,
            "height": size,
            "pieces": ["square3", "square2"],
            "walls": sorted([list(w) for w in walls]),
        }
        self.levels.append(generated)
        self.load_level(len(self.levels) - 1)
        self._set_feedback('Generated. Fill the board with reusable pieces.', None)
        # generated levels are appended so user can go back if they want

    def _clear_children(self, widget):
        child = widget.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            widget.remove(child)
            child = nxt
        # helper to empty a container without gtk flacky methods

    def _build_pieces(self):
        # if the piece palette is missing in the template, skip building pieces
        if not getattr(self, 'piece_box', None):
            return
        self._clear_children(self.piece_box)
        for piece_id in self.allowed_piece_ids:
            button = Gtk.Button()
            button.add_css_class('piece-card')
            button.set_focusable(False)
            button.set_tooltip_text(f'{self.pieces[piece_id].name} · infinite uses. R rotates, F flips.')
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            box.set_halign(Gtk.Align.CENTER)
            box.append(self._piece_grid(piece_id, self.rotation if piece_id == self.selected_piece_id else 0, small=True, flipped=self.flipped if piece_id == self.selected_piece_id else False))
            label = Gtk.Label(label=self.pieces[piece_id].name)
            label.add_css_class('caption')
            label.add_css_class('dim-label')
            box.append(label)
            button.set_child(box)
            button.connect('clicked', self._on_piece_clicked, piece_id)
            drag = Gtk.DragSource(actions=Gdk.DragAction.COPY)
            drag.connect('prepare', self._on_drag_prepare, piece_id)
            drag.connect('drag-begin', self._on_drag_begin, button, piece_id)
            drag.connect('drag-end', self._on_drag_end, button)
            button.add_controller(drag)
            self.piece_box.append(button)
        self._refresh_piece_selection()
        # each piece gets a small ui card and can be dragged onto the board

    def _piece_grid(self, piece_id, rotation, small=False, flipped=False):
        grid = Gtk.Grid(row_spacing=3, column_spacing=3)
        grid.add_css_class('piece-shape')
        cells = self._rotated_cells(self.pieces[piece_id].cells, rotation, flipped)
        max_r = max(r for r, _ in cells)
        max_c = max(c for _, c in cells)
        size = 16 if small else 22
        for r in range(max_r + 1):
            for c in range(max_c + 1):
                cell = Gtk.Box()
                cell.set_size_request(size, size)
                if (r, c) in cells:
                    cell.add_css_class('mini-cell')
                grid.attach(cell, c, r, 1, 1)
        return grid
        # draw a small grid representing the piece
        # small=True used for the palette, false used for drag icon

    def _on_piece_clicked(self, _button, piece_id):
        self.selected_piece_id = piece_id
        self.rotation = 0
        self.flipped = False
        self._refresh_piece_selection()
        self._set_feedback('Tap the board to place it. Use Rotate before placing.', None)

    def _refresh_piece_selection(self):
        child = self.piece_box.get_first_child()
        i = 0
        while child:
            pid = self.allowed_piece_ids[i]
            if pid == self.selected_piece_id:
                child.add_css_class('selected')
            else:
                child.remove_css_class('selected')
            child = child.get_next_sibling()
            i += 1

    def _on_drag_prepare(self, _source, _x, _y, piece_id):
        payload = f'{piece_id}:{self.rotation}:{int(self.flipped)}'
        return Gdk.ContentProvider.new_for_value(payload)

    def _on_drag_begin(self, _source, drag, button, piece_id):
        self.selected_piece_id = piece_id
        button.add_css_class('dragging')
        icon = Gtk.DragIcon.get_for_drag(drag)
        icon.set_child(self._piece_grid(piece_id, self.rotation, small=False, flipped=self.flipped))
        self._refresh_piece_selection()

    def _on_drag_end(self, _source, _drag, _delete_data, button):
        button.remove_css_class('dragging')
        self._clear_preview()

    def rotate_selected(self, direction=1):
        self.rotation = (self.rotation + direction) % 4
        self._rebuild_selected_preview()
        self._set_feedback('Piece rotated.', None)

    def flip_selected(self):
        self.flipped = not self.flipped
        self._rebuild_selected_preview()
        self._set_feedback('Piece flipped.', None)

    def _rebuild_selected_preview(self):
        self._build_pieces()
        self._refresh_piece_selection()

    def select_relative_piece(self, delta):
        if not self.allowed_piece_ids:
            return
        idx = self.allowed_piece_ids.index(self.selected_piece_id) if self.selected_piece_id in self.allowed_piece_ids else 0
        self.selected_piece_id = self.allowed_piece_ids[(idx + delta) % len(self.allowed_piece_ids)]
        self.rotation = 0
        self.flipped = False
        self._refresh_piece_selection()
        self._set_feedback(f'Selected {self.pieces[self.selected_piece_id].name}.', None)

    def _build_board(self):
        # if the board grid is missing just skip building board (safe fallback)
        if not getattr(self, 'board_grid', None):
            self.buttons = {}
            return
        self._clear_children(self.board_grid)
        self.buttons = {}
        for r in range(self.height):
            for c in range(self.width):
                button = Gtk.Button()
                button.add_css_class('board-cell')
                button.set_focusable(False)
                if (r, c) in self.walls:
                    button.add_css_class('wall')
                    button.set_sensitive(False)
                else:
                    button.add_css_class('empty')
                    click = Gtk.GestureClick()
                    click.set_button(0)
                    click.connect('pressed', self._on_cell_pressed, r, c)
                    button.add_controller(click)
                    motion = Gtk.EventControllerMotion()
                    motion.connect('enter', self._on_cell_enter, r, c)
                    motion.connect('leave', self._on_cell_leave)
                    button.add_controller(motion)
                    drop = Gtk.DropTarget.new(GObject.TYPE_STRING, Gdk.DragAction.COPY)
                    drop.connect('enter', self._on_drop_enter, r, c)
                    drop.connect('leave', self._on_drop_leave)
                    drop.connect('drop', self._on_drop, r, c)
                    button.add_controller(drop)
                self.board_grid.attach(button, c, r, 1, 1)
                self.buttons[(r, c)] = button

    def _on_cell_pressed(self, gesture, n_press, _x, _y, r, c):
        button = gesture.get_current_button()
        # debug: log click info to help diagnose why clicks may not place pieces
        try:
            print(f"_on_cell_pressed: btn={button} n_press={n_press} r={r} c={c} selected={self.selected_piece_id}")
        except Exception:
            pass
        if button == 3 or n_press >= 2:
            self.remove_piece_at(r, c)
            return
        if self.board[r][c] is not None:
            self.remove_piece_at(r, c)
            return
        self.place_piece(self.selected_piece_id, self.rotation, r, c, self.flipped)

    def _on_cell_enter(self, _motion, _x, _y, r, c):
        if self.board[r][c] is not None:
            self._highlight_piece_at(r, c, True)
        else:
            self._show_preview(self.selected_piece_id, self.rotation, r, c, self.flipped)

    def _on_cell_leave(self, *_args):
        self._clear_preview()
        self._clear_hover()

    def _on_drop_enter(self, _drop, _x, _y, r, c):
        self._show_preview(self.selected_piece_id, self.rotation, r, c, self.flipped)
        return Gdk.DragAction.COPY

    def _on_drop_leave(self, *_args):
        self._clear_preview()

    def _on_drop(self, _drop, value, _x, _y, r, c):
        try:
            parts = value.split(':')
            piece_id = parts[0]
            rotation = int(parts[1])
            flipped = bool(int(parts[2])) if len(parts) > 2 else False
        except Exception:
            piece_id, rotation, flipped = self.selected_piece_id, self.rotation, self.flipped
        ok = self.place_piece(piece_id, rotation, r, c, flipped)
        self._clear_preview()
        return ok

    def _on_board_button_clicked(self, button, r, c):
        # fallback click handler for environments where gesture pressed isn't fired
        try:
            print(f"_on_board_button_clicked: r={r} c={c} board={self.board[r][c]} selected={self.selected_piece_id}")
        except Exception:
            pass
        if self.board[r][c] is not None:
            self.remove_piece_at(r, c)
            return
        self.place_piece(self.selected_piece_id, self.rotation, r, c, self.flipped)

    def _rotated_cells(self, cells, rotation, flipped=False):
        # geometry helper: apply flip then rotations and normalize to origin
        pts = list(cells)
        # flip horizontally by mirroring across max column
        if flipped:
            max_c = max(c for _, c in pts)
            pts = [(r, max_c - c) for r, c in pts]
        # rotate 90deg steps, repeated rotation for requested amount
        for _ in range(rotation % 4):
            max_r = max(r for r, _ in pts)
            # (r, c) -> (c, max_r - r) is a clockwise rotation around origin
            pts = [(c, max_r - r) for r, c in pts]
        # shift so smallest row/col is zero (top-left anchor)
        min_r = min(r for r, _ in pts)
        min_c = min(c for _, c in pts)
        return frozenset((r - min_r, c - min_c) for r, c in pts)

    def _target_cells(self, piece_id, rotation, anchor_r, anchor_c, flipped=False):
        return {(anchor_r + r, anchor_c + c) for r, c in self._rotated_cells(self.pieces[piece_id].cells, rotation, flipped)}

    def _best_cells_for_target(self, piece_id, rotation, target_r, target_c, flipped=False):
        """Return cells for a placement near the target cell.

        The old prototype treated the clicked cell as the piece's top-left corner.
        That feels wrong while dragging: if the cursor is over any square of the
        ghost piece, the piece should still snap there. We now try the top-left
        placement first, then every offset that makes one cell of the piece land
        on the target cell, and pick the first valid candidate.
        """
        # try to find a valid placement near the target cell
        # direct = treat target cell as top-left of the shape
        shape = self._rotated_cells(self.pieces[piece_id].cells, rotation, flipped)
        direct = {(target_r + r, target_c + c) for r, c in shape}
        if self._can_place(direct):
            # neat fit using top-left anchoring
            return direct
        # otherwise try offsets so any cell of the piece lands on target
        candidates = []
        for off_r, off_c in sorted(shape):
            anchor_r = target_r - off_r
            anchor_c = target_c - off_c
            cells = {(anchor_r + r, anchor_c + c) for r, c in shape}
            if self._can_place(cells):
                # first good candidate wins, this matches user expectation
                return cells
            candidates.append(cells)
        # fallback: return the direct attempt (even if out of bounds) or first candidate
        return direct if direct else (candidates[0] if candidates else set())

    def _can_place(self, cells):
        # simple check: inside board, not a wall, and not already occupied
        for r, c in cells:
            if not (0 <= r < self.height and 0 <= c < self.width):
                return False
            if (r, c) in self.walls or self.board[r][c] is not None:
                return False
        return True

    def place_piece(self, piece_id, rotation, r, c, flipped=False):
        # main flow for placing a piece
        # debug: log placement attempts
        try:
            print(f"place_piece attempt: piece={piece_id} rot={rotation} flipped={flipped} target=({r},{c}) allowed={piece_id in self.allowed_piece_ids}")
        except Exception:
            pass
        # check allowed for this level
        if piece_id not in self.allowed_piece_ids:
            self._set_feedback('That piece is not allowed in this level.', 'error')
            return False
        # find best candidate cells near the target click/drop
        cells = self._best_cells_for_target(piece_id, rotation, r, c, flipped)
        try:
            print(f" -> candidate cells: {cells} can_place={self._can_place(cells)}")
        except Exception:
            pass
        if not self._can_place(cells):
            # visual pulse + message to explain why it failed
            self._pulse(cells, 'invalid')
            self._set_feedback('That piece does not fit there.', 'error')
            return False
        # save undo state before mutating board
        self._push_undo_state()
        placement_id = self.next_placement_id
        self.next_placement_id += 1
        color = COLORS[(placement_id - 1) % len(COLORS)]
        # store placement metadata so we can remove or highlight it later
        self.placements[placement_id] = {"piece_id": piece_id, "cells": cells, "rotation": rotation, "flipped": flipped, "color": color}
        for cr, cc in cells:
            self.board[cr][cc] = placement_id
            self._refresh_cell(cr, cc)
            self._pop(cr, cc)
        # scoring and simple stats, non critical for game logic
        self.moves += 1
        self.score += len(cells) * 10
        self._update_score()
        self._set_feedback('Placed. Click, double-click, or press Delete over a piece to remove it.', None)
        # quick autocheck for completion
        self.check_board(show_incomplete=False)
        return True

    def remove_piece_at(self, r, c):
        # debug: log removal attempts to help trace issue
        try:
            print(f"remove_piece_at: target=({r},{c}) board_has={self.board[r][c]}")
        except Exception:
            pass
        placement_id = self.board[r][c]
        if placement_id is None:
            return
        self._push_undo_state()
        cells = self.placements.get(placement_id, {}).get('cells', set())
        for cr, cc in cells:
            self.board[cr][cc] = None
            self._refresh_cell(cr, cc)
        self.placements.pop(placement_id, None)
        self.moves += 1
        self.score = max(0, self.score - len(cells) * 4)
        self._update_score()
        self._set_feedback('Piece removed.', None)

    def remove_hovered_piece(self):
        try:
            print(f"remove_hovered_piece: hovered={self.hovered_placement_id}")
        except Exception:
            pass
        if self.hovered_placement_id is None or self.hovered_placement_id not in self.placements:
            self._set_feedback('Hover a placed piece, then press Delete to remove it.', 'error')
            return
        cells = self.placements[self.hovered_placement_id].get('cells', set())
        if cells:
            r, c = next(iter(cells))
            self.remove_piece_at(r, c)

    def _highlight_piece_at(self, r, c, active):
        placement_id = self.board[r][c]
        if placement_id is None:
            return
        self.hovered_placement_id = placement_id if active else None
        for cell in self.placements.get(placement_id, {}).get('cells', set()):
            if cell in self.buttons:
                if active:
                    self.buttons[cell].add_css_class('hover-piece')
                else:
                    self.buttons[cell].remove_css_class('hover-piece')

    def _clear_hover(self):
        self.hovered_placement_id = None
        for button in self.buttons.values():
            button.remove_css_class('hover-piece')

    def _refresh_cell(self, r, c):
        button = self.buttons[(r, c)]
        for cls in ['empty', 'blue', 'green', 'yellow', 'purple', 'orange', 'red', 'teal', 'preview-ok', 'preview-bad', 'invalid', 'pop', 'hover-piece']:
            button.remove_css_class(cls)
        placement_id = self.board[r][c]
        if placement_id is None:
            button.add_css_class('empty')
        else:
            button.add_css_class(self.placements[placement_id]['color'])

    def _show_preview(self, piece_id, rotation, r, c, flipped=False):
        self._clear_preview()
        cells = self._best_cells_for_target(piece_id, rotation, r, c, flipped)
        ok = self._can_place(cells)
        self.preview_cells = {(cr, cc) for cr, cc in cells if (cr, cc) in self.buttons and (cr, cc) not in self.walls}
        for cr, cc in self.preview_cells:
            self.buttons[(cr, cc)].add_css_class('preview-ok' if ok else 'preview-bad')

    def _clear_preview(self):
        for r, c in self.preview_cells:
            if (r, c) in self.buttons:
                self.buttons[(r, c)].remove_css_class('preview-ok')
                self.buttons[(r, c)].remove_css_class('preview-bad')
        self.preview_cells = set()

    def _pulse(self, cells, cls):
        visible = [(r, c) for r, c in cells if (r, c) in self.buttons]
        for r, c in visible:
            self.buttons[(r, c)].add_css_class(cls)
        GLib.timeout_add(260, lambda: self._remove_class(visible, cls))

    def _pop(self, r, c):
        self.buttons[(r, c)].add_css_class('pop')
        GLib.timeout_add(220, lambda: self._remove_class([(r, c)], 'pop'))

    def _remove_class(self, cells, cls):
        for r, c in cells:
            if (r, c) in self.buttons:
                self.buttons[(r, c)].remove_css_class(cls)
        return GLib.SOURCE_REMOVE

    def reset_board(self):
        self._push_undo_state()
        self.victory_dialog_open = False
        for r in range(self.height):
            for c in range(self.width):
                if (r, c) not in self.walls:
                    self.board[r][c] = None
                    self._refresh_cell(r, c)
        self.placements = {}
        self.score = 0
        self.moves = 0
        self.next_placement_id = 1
        self._update_score()
        self._set_feedback('Board reset.', None)

    def _snapshot(self):
        return {
            'board': [row[:] for row in self.board],
            # placements cells converted to plain set for serialisability in undo
            'placements': {pid: {**data, 'cells': set(data.get('cells', set()))} for pid, data in self.placements.items()},
            'score': self.score,
            'moves': self.moves,
            'next_placement_id': self.next_placement_id,
        }

    def _restore_snapshot(self, snap):
        # restore everything needed for undo/redo to work
        self.board = [row[:] for row in snap['board']]
        self.placements = {pid: {**data, 'cells': set(data.get('cells', set()))} for pid, data in snap['placements'].items()}
        self.score = snap['score']
        self.moves = snap['moves']
        self.next_placement_id = snap['next_placement_id']
        self.victory_dialog_open = False
        self.hovered_placement_id = None
        # refresh ui 
        for r in range(self.height):
            for c in range(self.width):
                if (r, c) not in self.walls:
                    self._refresh_cell(r, c)
        self._update_score()

    def _push_undo_state(self):
        # keep a rolling history of snapshots so undo is cheap
        if self.board:
            self.undo_stack.append(self._snapshot())
            self.redo_stack.clear()
            # avoid unbounded memory growth
            if len(self.undo_stack) > 100:
                self.undo_stack.pop(0)

    def undo(self):
        if not self.undo_stack:
            self._set_feedback('Nothing to undo.', 'error')
            return
        self.redo_stack.append(self._snapshot())
        self._restore_snapshot(self.undo_stack.pop())
        self._set_feedback('Undone.', None)

    def redo(self):

        if not self.redo_stack:
            self._set_feedback('Nothing to redo.', 'error')
            return
        self.undo_stack.append(self._snapshot())
        self._restore_snapshot(self.redo_stack.pop())
        self._set_feedback('Redone.', None)

    def _is_complete(self):
        for r in range(self.height):
            for c in range(self.width):
                if (r, c) not in self.walls and self.board[r][c] is None:
                    return False
        return True

    def check_board(self, show_incomplete=True):
        # validate board completeness and show victory if solved
        if self.victory_dialog_open:
            return True
        if not self._is_complete():
            if show_incomplete:
                self._set_feedback('Fill every free cell before checking.', 'error')
            return False
        # ensure all placed pieces are allowed for this level
        for placement in self.placements.values():
            if placement['piece_id'] not in self.allowed_piece_ids:
                self._set_feedback('A placed piece is not allowed in this level.', 'error')
                return False
        self.score += 100 # award a small bonus so user sees they solved it
        self._update_score()
        try:
            # persist result (store best score / best moves)
            updated = save_progress_for(self.level_index, self.score, self.moves)
            if updated and getattr(self, 'record_label', None):
                try:
                    text = f"Best: Score {self.score} · Moves {self.moves}"
                    self.record_label.set_label(text)
                    self.record_label.remove_css_class('success')
                    self.record_label.remove_css_class('error')
                    self.record_label.add_css_class('success')
                except Exception:
                    pass
        except Exception:
            pass
        self._set_feedback('Solved. Every free cell is filled.', 'success')
        self._show_victory_dialog()
        return True

    def _show_victory_dialog(self):
        if self.victory_dialog_open:
            return
        self.victory_dialog_open = True
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading='Puzzle Complete!',
            body=f"{self.level.get('title', 'Level')} solved.\nScore: {self.score}\nMoves: {self.moves}",
        )
        dialog.add_response('restart', 'Restart')
        dialog.add_response('next', 'Next Level')
        dialog.set_default_response('next')
        dialog.set_response_appearance('next', Adw.ResponseAppearance.SUGGESTED)
        dialog.connect('response', self._on_victory_response)
        dialog.present()

    def _on_victory_response(self, _dialog, response):
        self.victory_dialog_open = False
        if response == 'restart':
            self.load_level(self.level_index)
        else:
            self.load_level((self.level_index + 1) % len(self.levels))

    def _update_score(self):
        self.score_label.set_label(f'Score {self.score} · Moves {self.moves}')

    def _set_feedback(self, text, state):
        self.feedback_label.set_label(text)
        self.feedback_label.remove_css_class('success')
        self.feedback_label.remove_css_class('error')
        if state:
            self.feedback_label.add_css_class(state)
