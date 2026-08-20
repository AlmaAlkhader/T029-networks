"""Shared JSON-over-TCP protocol helpers.

Every protocol message is one UTF-8 encoded JSON object followed by exactly one
newline byte (``b"\n"``). The server welcome message has this shape::

    {"type": "welcome", "message": "..."}

A client request has this shape::

    {"command": "...", "parameter": "..."}

A server response has this shape::

    {
        "status": "Success" or "Failed",
        "command": "...",
        "parameter": "...",
        "output": "...",
        "execution_time": float,
        "timestamp": "ISO string",
        "error": "..."  # Optional; normally present only on failure.
    }
"""

from __future__ import annotations

import json
import weakref
from socket import socket
from typing import Any


PING = "PING"
TRACERT = "TRACERT"
NSLOOKUP = "NSLOOKUP"
IPCONFIG = "IPCONFIG"
ROUTE = "ROUTE"
ARP = "ARP"
NETSTAT = "NETSTAT"
EXIT = "EXIT"

ALLOWED_COMMANDS = frozenset(
    {PING, TRACERT, NSLOOKUP, IPCONFIG, ROUTE, ARP, NETSTAT, EXIT}
)

# A separate byte buffer is retained for each socket so bytes belonging to a
# later message are not lost when recv() returns several messages at once.
_receive_buffers: weakref.WeakKeyDictionary[socket, bytearray] = (
    weakref.WeakKeyDictionary()
)


def send_message(sock: socket, data: dict[str, Any]) -> None:
    """Send one dictionary as a newline-terminated UTF-8 JSON message.

    ``data`` must match one of the documented protocol shapes: a welcome
    message, client request, or server response. ``sendall`` is used because a
    socket send is not guaranteed to transmit the entire payload at once.
    """

    payload = json.dumps(data, ensure_ascii=False).encode("utf-8") + b"\n"
    sock.sendall(payload)


def receive_message(sock: socket) -> dict[str, Any]:
    """Receive, decode, and return one newline-terminated JSON object.

    The returned dictionary is one of the documented shapes: server welcome
    ``{"type": "welcome", "message": "..."}``, client request
    ``{"command": "...", "parameter": "..."}``, or server response with
    ``status``, ``command``, ``parameter``, ``output``, ``execution_time``, and
    ISO-string ``timestamp`` fields plus an optional ``error`` field.

    Bytes are buffered across calls. This handles both a message fragmented
    across multiple ``recv`` calls and multiple messages delivered by one
    ``recv`` call. A connection closed before a complete message raises
    ``ConnectionError``; malformed JSON or a non-object JSON value raises an
    appropriate decoding or ``ValueError`` exception.
    """

    buffer = _receive_buffers.setdefault(sock, bytearray())

    while b"\n" not in buffer:
        chunk = sock.recv(4096)
        if not chunk:
            _receive_buffers.pop(sock, None)
            raise ConnectionError("Socket closed before a complete message was received")
        buffer.extend(chunk)

    raw_message, _, remainder = buffer.partition(b"\n")
    buffer[:] = remainder
    decoded = json.loads(raw_message.decode("utf-8"))
    if not isinstance(decoded, dict):
        raise ValueError("Protocol message must be a JSON object")
    return decoded
