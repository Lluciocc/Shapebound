# progress.py
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
import os
from datetime import datetime,timezone
from pathlib import Path

# todo: add a way to clear progress

# this is the most reliable method for me
def _progress_dir() -> Path:
    base = os.environ.get('XDG_CONFIG_HOME')
    if base:
        base_path = Path(base)
    else:
        base_path = Path.home() / '.config'
    return base_path / 'com.github.Lluciocc.Shapebound'


def _progress_file() -> Path:
    return _progress_dir() / 'progress.json'


def load_all_progress() -> dict:
    path = _progress_file()
    if not path.exists():
        print(f"{path} does not exist" )
        return {}
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception as e:
        print("Error when loading all progress " + e)
        return {}


def load_progress_for(level_index: int) -> dict | None:
    print(f"Loading progress for {level_index}...")
    data = load_all_progress()
    print("Loaded data:", data)
    return data.get(str(level_index))


def save_progress_for(level_index: int, score: int, moves: int) -> bool:
    print(f"Saving progress for {level_index}...")
    d = _progress_dir()
    d.mkdir(parents=True, exist_ok=True)
    p = _progress_file()
    data = load_all_progress()
    key = str(level_index)
    now = datetime.now(timezone.utc).isoformat()
    existing = data.get(key)
    # update only if new result is better or no existing
    update = False
    if not existing:
        update = True
    else:
        try:
            if score > int(existing.get('score', -1)):
                update = True
            if moves < int(existing.get('moves', 10**9)):
                update = True
        except Exception:
            update = True
    if update:
        print(f"Writing progress to {p}")

        data[key] = {
            'completed': True,
            'score': int(score),
            'moves': int(moves),
            'updated_at': now,
        }

        tmp = p.with_suffix('.tmp')
        tmp.write_text(json.dumps(data, indent=2), encoding='utf-8')
        print(f"Temporary file written: {tmp}")

        tmp.replace(p)
        print(f"Final file written: {p}")
    return update

def clear_progress():
    path = _progress_file()

    try:
        path.unlink(missing_ok=True)
        return True
    except Exception as e:
        print(f"Failed to clear progress: {e}")
        return False
