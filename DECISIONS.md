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
