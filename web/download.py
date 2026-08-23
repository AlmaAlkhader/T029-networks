"""Raw JSON Lines log download route."""

from pathlib import Path


def log_download(config):
    path = Path(config["log_file"])
    try:
        body = path.read_bytes() if path.exists() else b""
    except OSError:
        body = b""
    headers = {
        "Content-Disposition": 'attachment; filename="server_log.jsonl"',
    }
    return 200, "application/octet-stream", body, headers
