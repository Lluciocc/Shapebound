import json
import os
from datetime import datetime,timezone
from pathlib import Path

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
