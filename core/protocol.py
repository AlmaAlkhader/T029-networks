"""
Shared protocol stuff for talking over the TCP socket.

Basic idea: every message we send is one JSON object followed by a newline.
The newline is how the other side knows where one message ends and the next
one starts, since TCP doesn't give you message boundaries for free - it's
just a stream of bytes.
"""
import json
import weakref

PING = "PING"
TRACERT = "TRACERT"
NSLOOKUP = "NSLOOKUP"
IPCONFIG = "IPCONFIG"
ROUTE = "ROUTE"
ARP = "ARP"
NETSTAT = "NETSTAT"
EXIT = "EXIT"

ALLOWED_COMMANDS = frozenset({PING, TRACERT, NSLOOKUP, IPCONFIG, ROUTE, ARP, NETSTAT, EXIT})

# every connected socket gets its own leftover-bytes buffer here. if we used
# one shared buffer for everyone, one client's half-finished message could
# get mixed up with another client's message. WeakKeyDictionary just means
# we don't have to manually clean this up - it clears itself out once a
# socket object is gone.
_receive_buffers = weakref.WeakKeyDictionary()


def send_message(sock, data):
    # dict -> JSON text -> bytes, then tack a newline on the end so the
    # other side knows where this message stops
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8") + b"\n"
    sock.sendall(payload)  # using sendall because send() can stop partway through


def receive_message(sock):
    # grab this socket's buffer, or start a fresh one if we haven't seen it before
    buffer = _receive_buffers.setdefault(sock, bytearray())

    # keep reading off the socket until we actually have a full message.
    # recv() might hand back only half a message, or two messages stuck
    # together, so we can't just trust one recv() call to be "one message"
    while b"\n" not in buffer:
        chunk = sock.recv(4096)
        if not chunk:
            # recv() returning nothing means the other side hung up
            _receive_buffers.pop(sock, None)
            raise ConnectionError("socket closed before we got a full message")
        buffer.extend(chunk)

    # cut off just the first complete message, save whatever's left over
    # for the next call (in case two messages arrived back to back)
    raw_message, _, remainder = buffer.partition(b"\n")
    buffer[:] = remainder

    decoded = json.loads(raw_message.decode("utf-8"))
    if not isinstance(decoded, dict):
        raise ValueError("expected a JSON object, got something else")
    return decoded
