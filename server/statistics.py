import threading
import time

_stats_lock = threading.Lock()

_stats = {
    "total_commands": 0,
    "success_count": 0,
    "fail_count": 0,
    "command_counts": {},
    "executed_count": 0,
    "executed_execution_time_total": 0.0,
    "active_clients": 0,
    "last_execution_time": None,
    "server_start_time": time.time()
}


def rebuild_from_log(log_file):
    """Rebuild in-memory stats from a saved .jsonl log file after a
    restart. The log schema (fixed by the project spec) has no explicit
    "was this really executed" field, so this approximates it: entries
    with command == "EXIT" or command == "INVALID" are excluded from
    command_counts and the average_execution_time calculation, the same
    way live requests are excluded via the executed=False flag. A rejected
    request that kept a real command name (e.g. a rejected PING with a bad
    hostname) will be slightly over-counted in this approximation - this
    is a known, accepted limitation given the log's fixed schema."""
    from pathlib import Path
    import json

    log_path = Path(log_file)
    if not log_path.exists():
        return  # fresh install, nothing to rebuild

    with _stats_lock:
        _stats["total_commands"] = 0
        _stats["success_count"] = 0
        _stats["fail_count"] = 0
        _stats["command_counts"] = {}
        _stats["executed_count"] = 0
        _stats["executed_execution_time_total"] = 0.0
        _stats["last_execution_time"] = None

        with log_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                _stats["total_commands"] += 1
                if entry.get("status") == "Success":
                    _stats["success_count"] += 1
                else:
                    _stats["fail_count"] += 1

                command = entry.get("command", "")
                execution_time = entry.get("execution_time", 0.0)

                if command not in ("EXIT", "INVALID"):
                    _stats["command_counts"][command] = (
                        _stats["command_counts"].get(command, 0) + 1
                    )
                    _stats["executed_count"] += 1
                    _stats["executed_execution_time_total"] += execution_time
                    _stats["last_execution_time"] = execution_time


def record_request(command, execution_time, success, executed=True):
    with _stats_lock:
        _stats["total_commands"] += 1

        if success:
            _stats["success_count"] += 1
        else:
            _stats["fail_count"] += 1

        if executed:
            _stats["command_counts"][command] = _stats["command_counts"].get(command, 0) + 1
            _stats["executed_count"] += 1
            _stats["executed_execution_time_total"] += execution_time
            _stats["last_execution_time"] = execution_time

def client_connected():
    with _stats_lock:
        _stats["active_clients"] += 1


def client_disconnected():
    with _stats_lock:
        _stats["active_clients"] -= 1

def get_snapshot():
    with _stats_lock:
        total = _stats["total_commands"]

        if _stats["executed_count"] > 0:
            average_execution_time = _stats["executed_execution_time_total"] / _stats["executed_count"]
        else:
            average_execution_time = 0.0

        if _stats["command_counts"]:
            most_frequent_command = max(
                _stats["command_counts"],
                key=_stats["command_counts"].get
            )
        else:
            most_frequent_command = None

        uptime_seconds = time.time() - _stats["server_start_time"]

        snapshot = {
            "total_commands": total,
            "success_count": _stats["success_count"],
            "fail_count": _stats["fail_count"],
            "most_frequent_command": most_frequent_command,
            "average_execution_time": round(average_execution_time, 3),
            "active_clients": _stats["active_clients"],
            "last_execution_time": _stats["last_execution_time"],
            "uptime_seconds": round(uptime_seconds, 1)
        }

        return snapshot
