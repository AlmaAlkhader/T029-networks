import json
import threading
from pathlib import Path

_log_lock = threading.Lock()

_log_file_path = None

def init(log_file):
    global _log_file_path
    _log_file_path = log_file

def log_request(entry):
    log_path = Path(_log_file_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    line = json.dumps(entry)

    with _log_lock:
        with log_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

