"""Small client-side wrapper around the shared TCP protocol."""

import socket

from core import protocol


def connect_to_server(host, port):
    """Connect to the diagnostic server and return the connected socket."""
    try:
        return socket.create_connection((host, port))
    except ConnectionRefusedError as error:
        raise ConnectionRefusedError(
            "Could not connect to server - is it running?"
        ) from error


def receive_welcome(sock):
    """Receive the initial welcome or server-full error message."""
    message = protocol.receive_message(sock)
    if message.get("type") == "error":
        return message
    if message.get("type") != "welcome":
        raise ValueError("Expected a welcome message from the server")
    return message


def send_request(sock, command, parameter=""):
    """Send one diagnostic command request."""
    protocol.send_message(
        sock,
        {"command": command, "parameter": parameter},
    )


def receive_response(sock):
    """Return a normal response or a distinct ``type=error`` message."""
    message = protocol.receive_message(sock)
    if message.get("type") in ("error", "welcome"):
        return message
    return message
