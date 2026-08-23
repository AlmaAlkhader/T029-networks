"""HTML page renderers shared by the HTTP routes."""

import html
import json
from pathlib import Path

from server import statistics as server_statistics


STYLE = """
<style>
body { font-family: Arial, sans-serif; margin: 0; background: #f3f6fa; color: #172033; }
header { background: #173b67; color: white; padding: 1rem 2rem; }
nav a { color: white; margin-right: 1rem; text-decoration: none; }
main { max-width: 1000px; margin: 2rem auto; background: white; padding: 2rem; border-radius: 10px; box-shadow: 0 3px 14px #ccd5e0; }
h1, h2 { color: #173b67; }
table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
th, td { border: 1px solid #ccd5e0; padding: .65rem; text-align: left; }
th { background: #e8f0f8; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 1rem; }
.card { background: #eaf2fb; padding: 1rem; border-radius: 8px; }
label { display: inline-block; margin: .4rem; }
input { padding: .45rem; }
button { padding: .5rem 1rem; background: #173b67; color: white; border: 0; border-radius: 4px; }
.message { padding: 1rem; background: #fff4ce; border-radius: 6px; }
</style>
"""

NAVIGATION = """<nav>
<a href="/home">Home</a><a href="/dashboard">Dashboard</a>
<a href="/history">History</a><a href="/statistics">Statistics</a>
<a href="/search">Search</a><a href="/download">Download Log</a>
</nav>"""


def page(title, content):
    """Wrap page content in the required UTF-8 HTML document."""
    return (
        "<!DOCTYPE html>\n<html><head><meta charset=\"UTF-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        "<title>" + html.escape(title) + "</title>" + STYLE
        + "</head><body><header><strong>ENCS3320 Network Diagnostic System</strong>"
        + NAVIGATION + "</header><main>" + content + "</main></body></html>"
    )


def read_log_entries(log_file):
    """Read all valid JSON objects from the JSON Lines log afresh."""
    path = Path(log_file)
    if not path.exists():
        return []
    entries = []
    try:
        with path.open("r", encoding="utf-8") as log:
            for line in log:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(entry, dict):
                    entries.append(entry)
    except OSError:
        return []
    return entries


def home_page():
    content = """<h1>Team T029</h1>
<table><tr><th>Name</th><th>Student ID</th><th>Section</th></tr>
<tr><td>Mohammad Joudeh</td><td>1241945</td><td>2</td></tr>
<tr><td>Eman Zayed</td><td>1240916</td><td>2</td></tr>
<tr><td>Alma Alkhader</td><td>1240386</td><td>2</td></tr></table>
<h2>ENCS3320 - Computer Networks</h2>
<p>ENCS3320 explores socket programming, HTTP, client-server architecture, and DNS. The course also applies Application Layer concepts through practical network diagnostic tools.</p>
<p lang="ar" dir="rtl">مرحباً بكم في مشروع شبكات الحاسوب لفريق T029.</p>"""
    return page("Home", content)


def _format_uptime(seconds):
    seconds = max(0, int(seconds or 0))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def dashboard_page():
    snapshot = server_statistics.get_snapshot()
    last_time = snapshot.get("last_execution_time")
    last_display = "N/A" if last_time is None else f"{float(last_time):.2f} seconds"
    content = """<h1>Dashboard</h1><div class="cards">
<div class="card"><strong>Number of executed commands</strong><p>{total}</p></div>
<div class="card"><strong>Number of connected clients</strong><p>{active}</p></div>
<div class="card"><strong>Last execution time</strong><p>{last}</p></div>
<div class="card"><strong>Server uptime</strong><p>{uptime}</p></div>
</div>""".format(
        total=snapshot.get("total_commands", 0),
        active=snapshot.get("active_clients", 0),
        last=last_display,
        uptime=_format_uptime(snapshot.get("uptime_seconds", 0)),
    )
    return page("Dashboard", content)


def entries_table(entries):
    rows = []
    for entry in entries:
        rows.append(
            "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{:.3f}</td><td>{}</td></tr>".format(
                html.escape(str(entry.get("timestamp", ""))),
                html.escape(str(entry.get("client_ip", ""))),
                html.escape(str(entry.get("command", ""))),
                html.escape(str(entry.get("parameter", ""))),
                float(entry.get("execution_time", 0.0) or 0.0),
                html.escape(str(entry.get("status", ""))),
            )
        )
    return (
        "<table><thead><tr><th>Time</th><th>Client IP</th><th>Command</th>"
        "<th>Parameter</th><th>Execution Time</th><th>Status</th></tr></thead>"
        "<tbody>" + "".join(rows) + "</tbody></table>"
    )


def history_page(config):
    entries = list(reversed(read_log_entries(config["log_file"])))
    return page("Command History", "<h1>Command History</h1>" + entries_table(entries))


def statistics_page():
    snapshot = server_statistics.get_snapshot()
    most_frequent = snapshot.get("most_frequent_command") or "None"
    content = """<h1>Statistics</h1><div class="cards">
<div class="card"><strong>Most frequently used command</strong><p>{most}</p></div>
<div class="card"><strong>Average execution time</strong><p>{average:.3f} seconds</p></div>
<div class="card"><strong>Total successful requests</strong><p>{success}</p></div>
<div class="card"><strong>Total failed requests</strong><p>{failed}</p></div>
</div>""".format(
        most=html.escape(str(most_frequent)),
        average=float(snapshot.get("average_execution_time", 0.0)),
        success=snapshot.get("success_count", 0),
        failed=snapshot.get("fail_count", 0),
    )
    return page("Statistics", content)


def error_page(code, reason, message):
    return page(reason, f"<h1>{code} {html.escape(reason)}</h1><p>{html.escape(message)}</p>")
