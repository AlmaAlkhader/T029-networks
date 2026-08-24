"""HTML page renderers shared by the HTTP routes."""

import html
import json
from pathlib import Path

from server import statistics as server_statistics


STYLE = """
<style>
* { box-sizing: border-box; }
body { margin: 0; font-family: Arial, Helvetica, sans-serif; background: #F8F5EF; color: #2B2B26; line-height: 1.5; }
header { background: #781F31; color: #FFFFFF; border-bottom: 4px solid #781F31; }
.header-inner { max-width: 960px; margin: 0 auto; padding: 1rem 1.25rem .8rem; }
.site-title { margin: 0 0 .65rem; font-size: 1.25rem; font-weight: bold; }
nav { display: flex; flex-wrap: wrap; gap: .35rem 1.25rem; }
nav a { color: #FFFFFF; text-decoration: none; border-bottom: 1px solid transparent; }
nav a:hover { color: #FFFFFF; border-bottom-color: #386641; }
main { max-width: 960px; margin: 1.5rem auto 2rem; padding: 1.5rem; background: #FFFFFF; border-top: 3px solid #781F31; }
h1 { margin: 0 0 1rem; color: #781F31; font-size: 1.75rem; }
h2 { margin: 1.5rem 0 .5rem; color: #781F31; font-size: 1.25rem; }
p { max-width: 720px; }
.section { margin-top: 1.75rem; padding-top: .25rem; border-top: 1px solid #CFC5B4; }
.table-wrap { width: 100%; overflow-x: auto; }
table { width: 100%; min-width: 680px; margin-top: .75rem; border-collapse: collapse; }
th, td { padding: .65rem; text-align: left; border: 1px solid #CFC5B4; }
th { background: #781F31; color: #FFFFFF; font-weight: bold; }
tbody tr:nth-child(even) { background: #E7DDCB; }
.status-success { color: #386641; font-weight: bold; }
.status-failed { color: #781F31; font-weight: bold; }
.stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.stat-item { padding: 1rem; background: #E7DDCB; border: 1px solid #CFC5B4; border-left: 4px solid #781F31; border-radius: 3px; }
.stat-label { margin: 0; font-size: .95rem; }
.stat-value { margin: .25rem 0 0; color: #781F31; font-size: 1.45rem; font-weight: bold; }
.search-form { display: grid; grid-template-columns: 1fr 1fr 1fr auto; gap: .75rem; align-items: end; padding-bottom: 1.25rem; border-bottom: 1px solid #CFC5B4; }
.form-field label { display: block; margin-bottom: .25rem; font-weight: bold; }
input { width: 100%; padding: .5rem; border: 1px solid #CFC5B4; border-radius: 3px; font: inherit; }
input:focus { outline: 2px solid #386641; outline-offset: 1px; }
button { padding: .55rem 1rem; background: #386641; color: #FFFFFF; border: 1px solid #386641; border-radius: 3px; font: inherit; font-weight: bold; cursor: pointer; }
button:hover { background: #FFFFFF; color: #386641; }
.message { margin-top: 1rem; padding: .75rem; border-left: 4px solid #386641; background: #E7DDCB; }
.error-box { padding: 1rem 0; border-top: 1px solid #CFC5B4; }
@media (max-width: 650px) {
    .header-inner, main { padding-left: 1rem; padding-right: 1rem; }
    main { margin-top: 1rem; }
    .stats-grid, .search-form { grid-template-columns: 1fr; }
    .search-form button { width: 100%; }
}
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
        + "</head><body><header><div class=\"header-inner\">"
        + "<div class=\"site-title\">ENCS3320 Network Diagnostic System</div>"
        + NAVIGATION + "</div></header><main>" + content + "</main></body></html>"
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
    content = """<h1>ENCS3320 - Computer Networks</h1>
<p>ENCS3320 explores socket programming, HTTP, client-server architecture, and DNS. The course also applies Application Layer concepts through practical network diagnostic tools.</p>
<section class="section"><h2>Team T029</h2>
<div class="table-wrap">
<table><tr><th>Name</th><th>Student ID</th><th>Section</th></tr>
<tr><td>Mohammad Joudeh</td><td>1241945</td><td>2</td></tr>
<tr><td>Eman Zayed</td><td>1240916</td><td>2</td></tr>
<tr><td>Alma Alkhader</td><td>1240386</td><td>2</td></tr></table>
</div></section>"""
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
    content = """<h1>Dashboard</h1><div class="stats-grid">
<div class="stat-item"><p class="stat-label">Number of executed commands</p><p class="stat-value">{total}</p></div>
<div class="stat-item"><p class="stat-label">Number of connected clients</p><p class="stat-value">{active}</p></div>
<div class="stat-item"><p class="stat-label">Last execution time</p><p class="stat-value">{last}</p></div>
<div class="stat-item"><p class="stat-label">Server uptime</p><p class="stat-value">{uptime}</p></div>
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
        status = str(entry.get("status", ""))
        status_class = "status-success" if status == "Success" else "status-failed"
        rows.append(
            "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{:.3f}</td>"
            "<td class=\"{}\">{}</td></tr>".format(
                html.escape(str(entry.get("timestamp", ""))),
                html.escape(str(entry.get("client_ip", ""))),
                html.escape(str(entry.get("command", ""))),
                html.escape(str(entry.get("parameter", ""))),
                float(entry.get("execution_time", 0.0) or 0.0),
                status_class,
                html.escape(status),
            )
        )
    return (
        "<div class=\"table-wrap\"><table><thead><tr><th>Time</th><th>Client IP</th><th>Command</th>"
        "<th>Parameter</th><th>Execution Time</th><th>Status</th></tr></thead>"
        "<tbody>" + "".join(rows) + "</tbody></table></div>"
    )


def history_page(config):
    entries = list(reversed(read_log_entries(config["log_file"])))
    return page("Command History", "<h1>Command History</h1>" + entries_table(entries))


def statistics_page():
    snapshot = server_statistics.get_snapshot()
    most_frequent = snapshot.get("most_frequent_command") or "None"
    content = """<h1>Statistics</h1><div class="stats-grid">
<div class="stat-item"><p class="stat-label">Most frequently used command</p><p class="stat-value">{most}</p></div>
<div class="stat-item"><p class="stat-label">Average execution time</p><p class="stat-value">{average:.3f} seconds</p></div>
<div class="stat-item"><p class="stat-label">Total successful requests</p><p class="stat-value">{success}</p></div>
<div class="stat-item"><p class="stat-label">Total failed requests</p><p class="stat-value">{failed}</p></div>
</div>""".format(
        most=html.escape(str(most_frequent)),
        average=float(snapshot.get("average_execution_time", 0.0)),
        success=snapshot.get("success_count", 0),
        failed=snapshot.get("fail_count", 0),
    )
    return page("Statistics", content)


def error_page(code, reason, message):
    return page(
        reason,
        f"<h1>{code} {html.escape(reason)}</h1>"
        f"<div class=\"error-box\"><p>{html.escape(message)}</p></div>",
    )
