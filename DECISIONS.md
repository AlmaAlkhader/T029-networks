# Shared Project Decisions

These decisions are fixed for the ENCS3320 team project (Team T029).

---

## SETTLED DECISIONS

### Ports

Student ID 1240386 ends in 386. Adding 5000 gives TCP port 5386; adding
6000 gives HTTP port 6386.

### Message framing

Both client-to-server and server-to-client traffic uses one JSON object per
line. Every JSON object is terminated by a single newline character.

This applies only to core/protocol.py (our custom TCP diagnostic protocol).
web/http_server.py must follow the real HTTP specification instead, which
uses \r\n\r\n (carriage-return plus newline, twice) to mark the end of
request headers. This is a separate, required standard and must not be
replaced with our single-newline framing.

### Logging

The server log uses JSON Lines (.jsonl): one JSON object per completed
request. Each object has exactly these fields:

timestamp, client_ip, client_port, command, parameter, execution_time, status

### Logging must be thread-safe

server/logger.py must protect every write to the log file with one shared
threading.Lock(), since multiple client threads can finish commands and
try to write a log line at nearly the same moment. Without this lock, two
threads' writes can interleave mid-line, corrupting the log file (partial/
garbled JSON lines). This applies to every write, including rejected
requests and EXIT entries, not just successful diagnostic commands.

### Failure definition (general rule)

A request is Failed when the OS command returns a non-zero exit code, times
out, or raises an exception. Short or empty output alone does not make a
request fail.

### Folder ownership

- Person A (Mohammed): config/, server/tcp_server.py, server/client_handler.py
- Person B (Eman): server/command_executor.py, server/logger.py, server/statistics.py
- Person C (Alma): core/, client/, web/

### Startup requirements for run_server.py

run_server.py must call logger.init(config["log_file"]) once, immediately
after loading the config and before the TCP server starts accepting
clients. Without this, logger.log_request() will crash on the first request.

client_handler.py must call command_executor.execute() with the configured
timeout, not the default:

executor_module.execute(command, parameter, timeout=config["command_timeout_seconds"])

Without the timeout argument, command_timeout_seconds in config.json is
silently ignored and every command falls back to a 10-second default.

### Why command_timeout_seconds is 90

Originally set to 10 seconds, balancing "don't cut off a slow-but-working
command" against "don't let a hung command occupy a client thread - and
therefore a max_clients slot - for too long."

Raised to 90 by Eman after real testing showed TRACERT consistently
failed to complete within 10 seconds - it was being cut off as a timeout
every time, not because anything was actually wrong, just because a real
traceroute genuinely takes longer than that. 10 seconds was too aggressive
for this specific command.

Trade-off worth knowing: at 90 seconds, a single hung command can now
occupy a max_clients slot for far longer than before. With max_clients
set to 10, a handful of stuck connections could meaningfully reduce
available capacity. This hasn't caused a problem in testing, but it's
worth revisiting if max_clients-related issues come up later.

### Max clients exceeded

When the maximum number of clients is already connected, the server still
accepts the new connection, sends a server-full error message, and then
closes that connection.

### Protocol error message

The server-full rejection is a third message shape:

{"type": "error", "error": "...", ...}

This is separate from the welcome message and the normal command response.
Client code must check for "type": "error" before treating a received
message as a normal command result.

### Search matching

All search fields use partial, case-insensitive matching. This applies to
command type, hostname, and client IP searches.

### EXIT command - logging

EXIT is logged like every other request, with command: "EXIT",
parameter: "", execution_time: 0.0, and status: "Success". It fits the
normal log schema, and the spec requires every request to be stored, so
the logging layer must not special-case or discard it.

EXIT is included in Total executed commands and Command History. It is
excluded specifically from the most frequently used command statistic,
since almost every session ends with one EXIT and including it would
dominate that count.

### average_execution_time excludes non-executed entries

EXIT and requests rejected by validation before reaching command_executor are
excluded from average_execution_time. This is for the same reason EXIT is
excluded from most_frequent_command: neither represents real diagnostic work,
so including their execution_time: 0.0 would misleadingly drag the average
toward zero.

Failed commands that did actually execute, including timeouts and unreachable
hosts, are still included because they represent real elapsed time spent
attempting a genuine diagnostic operation.

### EXIT and Total successful requests

EXIT counts toward Total successful requests, since it's logged with
status: "Success" and no rule excludes it from that total - a clean
disconnect is a request the server handled successfully. This is different
from the "most frequent command" exclusion, which exists only to stop EXIT
from misleadingly dominating a stat about diagnostic command popularity.

### Logging rejected requests

Requests that fail validation (unknown command, invalid hostname) are still
written to the log. Malformed JSON requests are also logged, not silently
discarded. Rejected requests use execution_time: 0.0 and status: "Failed".
The command field contains the command sent by the client when it can be
parsed, or "INVALID" when it can't be determined.

### NSLOOKUP failure detection

Unlike the other seven commands, NSLOOKUP cannot rely on exit code alone.
Some systems/versions return exit code 0 even when the domain doesn't
exist. After running NSLOOKUP, also search the output case-insensitively
for: "can't find", "nxdomain", "non-existent domain", "server failed". If
any phrase is present, the result is Failed regardless of exit code. This
applies only to NSLOOKUP - the other six commands use the general rule.

### PING partial packet loss

PING needs no special handling. Standard ping implementations use exit
code 0 when at least one reply is received, non-zero for total loss - this
matches our definition of reachability, so PING follows the general rule.
Partial loss is not a hard failure if the host responds at least once. The
exact numbers ("2 received, 50% packet loss") stay visible in the output
field, so a degraded connection is still reported honestly.

### Statistics persistence across restart

On startup, statistics.py reads the entire log file once and rebuilds
total_commands, success_count, fail_count, command_counts, and
average_execution_time, so the Dashboard stays consistent with Command
History after a restart. active_clients and uptime always reset to zero,
since they describe the current process, not history.

### Last execution time — CONFIRMED

Dashboard's "Last execution time" is the duration of the most recent
command (e.g. "0.18 seconds"), not a timestamp. Confirmed by Dr. Nimer -
"execution time" and "timestamp" are already two separate, distinct fields
per Part 1's response format ("execution status, command output, execution
time, timestamp"), so "Last execution time" reuses that same established
meaning (duration).

### Last execution time on restart

This value must be rebuilt at startup from the execution_time field of the
LAST entry in the log file. Without this, Dashboard would show a blank or
zero value right after a restart even though Command History still shows
real past entries.

### Required console output (exact wording)

On startup, in this exact order:

```text
Loading configuration...
Logger initialized.
Statistics initialized.
TCP Server started on port <tcp_port>.
HTTP Server started on port <http_port>.
Waiting for client connections...
```

On each client connection:

```text
Client connected:
<client_ip>:<client_port>
Thread-<N> created.
```

On each client disconnection:

```text
Client disconnected:
<client_ip>:<client_port>
```

---

## STILL NEED DECIDING / CONFIRMING

### NSLOOKUP - needs real verification

Eman must confirm the actual exit code and output text nslookup produces
on both Windows and Linux before the final build. The phrase list above is
based on documentation, not a direct test on our own machines yet.

### PING - needs real verification on Windows

The exit-code evidence is solid for Linux. Eman should confirm ping.exe on
Windows behaves the same way (exit 0 on partial loss) before this is
fully trusted.

### Minor, low-priority, not yet decided

- Command History table row order (newest-first vs oldest-first) - purely
  cosmetic, pick either, no need to overthink.
- Download page: serve the raw .jsonl log file as-is, or a reformatted
  version? Current lean is "raw file as-is" (simplest, matches "download
  the complete log file" literally) but never formally confirmed.
