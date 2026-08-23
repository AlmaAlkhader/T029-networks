# Shared Project Decisions

These decisions are fixed for the ENCS3320 team project.

## Ports

Student ID `1240386` ends in `386`. Adding `5000` gives TCP port `5386`; adding
`6000` gives HTTP port `6386`.

## Message framing

Both client-to-server and server-to-client traffic uses one JSON object per
line. Every JSON object is terminated by a single newline character.

## Logging

The server log uses JSON Lines (`.jsonl`): one JSON object per completed
request. Each object has exactly these fields:

`timestamp`, `client_ip`, `client_port`, `command`, `parameter`,
`execution_time`, `status`

## Failure definition

A request is `Failed` when the OS command returns a non-zero exit code, times
out, or raises an exception. Short or empty output alone does not make a
request fail.

## Folder ownership

- Person A: `config/`, `server/tcp_server.py`, and `server/client_handler.py`
- Person B: `server/command_executor.py`, `server/logger.py`, and
  `server/statistics.py`
- Person C: `core/`, `client/`, and `web/`

## Startup requirements for run_server.py

`run_server.py` must call `logger.init(config["log_file"])` once, immediately
after loading the config and before the TCP server starts accepting clients.
Without this, `logger.log_request()` will crash on the first request.

`client_handler.py` must call `command_executor.execute()` with the
configured timeout, not the default:

`executor_module.execute(command, parameter, timeout=config["command_timeout_seconds"])`

Without the `timeout` argument, `command_timeout_seconds` in config.json is
silently ignored and every command falls back to a 10-second default.

## Max clients exceeded

When the maximum number of clients is already connected, the server still
accepts the new connection, sends a server-full error message, and then closes
that connection.

## Protocol error message

The server-full rejection is a third message shape:

`{"type": "error", "error": "...", ...}`

This is separate from the welcome message and the normal command response.
Client code must check for `"type": "error"` before treating a received
message as a normal command result.

## Last execution time

The dashboard's **Last execution time** value is the duration of the most
recent command, such as `0.18 seconds`. It is not a timestamp.

## Search matching

All search fields use partial, case-insensitive matching. This applies to
command type, hostname, and client IP searches.

## EXIT command

`EXIT` is logged like every other request, with `command: "EXIT"`,
`parameter: ""`, `execution_time: 0.0`, and `status: "Success"`. It fits
the normal log schema, and the specification requires every request to be
stored, so the logging layer must not special-case or discard it.

`EXIT` is included in **Total executed commands** and **Command History**.
However, it is excluded specifically from the **most frequently used command**
statistic. Almost every session ends with one `EXIT`, so including it would
dominate that count and make the statistic less meaningful.

## Logging rejected requests

Requests that fail validation, including an unknown command or invalid
hostname, are still written to the log. Malformed JSON requests are also
logged rather than silently discarded.

Rejected requests use `execution_time: 0.0` and `status: "Failed"`. The
`command` field contains the command sent by the client when it can be parsed,
or `"INVALID"` when the command itself cannot be determined.

## NSLOOKUP failure detection

Unlike the other seven commands, `NSLOOKUP` cannot rely on the exit code alone
to determine `Success` or `Failed`. Some systems or versions return exit code
`0` even when the requested domain does not exist.

After running `NSLOOKUP`, the server must perform the normal exit-code check
and also search the output case-insensitively for any of these phrases:

- `can't find`
- `nxdomain`
- `non-existent domain`
- `server failed`

If any phrase is present, the result is `Failed` regardless of the exit code.
This output-text check applies only to `NSLOOKUP`. The other six diagnostic
commands continue to use the general failure definition and rely on the exit
code.

Before the final build, Eman must confirm the actual exit code and output text
produced by `nslookup` on both Windows and Linux. The behavior can vary by
operating system and `nslookup` version, so the phrase list may need to be
adjusted after testing the real command on both systems.

## PING partial packet loss

`PING` does not need special failure handling. Unlike `NSLOOKUP`, standard
`ping` implementations use exit code `0` when at least one reply is received
and a non-zero exit code for total packet loss. This matches the project's
definition of reachability, so `PING` follows the general failure rule and
trusts the exit code without an output-text override.

Partial packet loss is therefore not treated as a hard failure when the host
responds at least once. The exact results, such as `2 received, 50% packet
loss`, remain visible in the response's `output` field so a degraded
connection is still reported to the user.

Before the final build, Eman must confirm this exit-code behavior on Windows
using `ping.exe`. The evidence for this decision is solid on Linux, but it
has not yet been directly verified on Windows.

## Statistics persistence across restart

When the server starts, `statistics.py` reads the entire log file once and
rebuilds `total_commands`, `success_count`, `fail_count`, `command_counts`,
and `average_execution_time`. This keeps the Dashboard statistics consistent
with the Command History table after a restart.

`active_clients` and uptime always reset to zero on restart. They describe
only the currently running server process, not historical activity, so they
are not rebuilt from the log.

## Required console output

On startup, the server must print the following lines in this exact order and
with this exact wording:

```text
Loading configuration...
Logger initialized.
Statistics initialized.
TCP Server started on port <tcp_port>.
HTTP Server started on port <http_port>.
Waiting for client connections...
```

On each client connection, it must print:

```text
Client connected:
<client_ip>:<client_port>
Thread-<N> created.
```

On each client disconnection, it must print:

```text
Client disconnected:
<client_ip>:<client_port>
```

## Last execution time on restart

**BLOCKED:** This depends on Dr. Nimer's confirmation of whether **Last
execution time** means a command duration or a timestamp, as discussed in the
**Last execution time** section above.

Once the definition is confirmed, this value must also be rebuilt during
startup from the last entry in the log file. The server must use
`execution_time` if the confirmed meaning is duration, or `timestamp` if the
confirmed meaning is a timestamp.

Without rebuilding it, the Dashboard would show a blank or zero value
immediately after a restart even though Command History still contains real
past entries.
