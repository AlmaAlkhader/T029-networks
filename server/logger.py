import json
import threading
from pathlib import Path

_log_lock = threading.Lock()

def log_request(log_file, entry):
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    line = json.dumps(entry)

    with _log_lock:
        with log_path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

