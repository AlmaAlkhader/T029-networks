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