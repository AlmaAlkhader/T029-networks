import threading
import time

_stats_lock = threading.Lock()

_stats = {
    "total_commands": 0,
    "success_count": 0,
    "fail_count": 0,
    "command_counts": {},
    "total_execution_time": 0.0,
    "active_clients": 0,
    "last_execution_time": None,
    "server_start_time": time.time()
}
def record_request(command, execution_time, success):
    with _stats_lock:
        _stats["total_commands"] += 1

        if success:
            _stats["success_count"] += 1
        else:
            _stats["fail_count"] += 1

        _stats["command_counts"][command] = _stats["command_counts"].get(command, 0) + 1

        _stats["total_execution_time"] += execution_time
        _stats["last_execution_time"] = time.time()

def client_connected():
    with _stats_lock:
        _stats["active_clients"] += 1


def client_disconnected():
    with _stats_lock:
        _stats["active_clients"] -= 1

def get_snapshot():
    with _stats_lock:
        total = _stats["total_commands"]

        if total > 0:
            average_execution_time = _stats["total_execution_time"] / total
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

