"""Thread-per-connection HTTP/1.1 server implemented with raw sockets."""

import socket
import threading

from web import router


HEADER_END = b"\r\n\r\n"
MAX_HEADER_BYTES = 65536


def _read_request(client_socket, buffer_size):
    buffer = bytearray()
    while HEADER_END not in buffer:
        chunk = client_socket.recv(buffer_size)
        if not chunk:
            raise ValueError("Incomplete HTTP request")
        buffer.extend(chunk)
        if len(buffer) > MAX_HEADER_BYTES:
            raise ValueError("HTTP headers are too large")
    return bytes(buffer.partition(HEADER_END)[0])


def _parse_request(raw_headers):
    try:
        text = raw_headers.decode("iso-8859-1")
    except UnicodeDecodeError as error:
        raise ValueError("Invalid HTTP header encoding") from error
    lines = text.split("\r\n")
    parts = lines[0].split()
    if len(parts) != 3:
        raise ValueError("Malformed HTTP request line")
    method, target, version = parts
    if method != "GET" or not target.startswith("/") or not version.startswith("HTTP/"):
        raise ValueError("Only valid GET requests are supported")
    headers = {}
    for line in lines[1:]:
        name, separator, value = line.partition(":")
        if not separator or not name.strip():
            raise ValueError("Malformed HTTP header")
        headers[name.strip().lower()] = value.strip()
    return method, target, version, headers


def _decoded_path(target):
    path = target.partition("?")[0]
    output = ""
    index = 0
    while index < len(path):
        if path[index] == "%" and index + 2 < len(path):
            try:
                output += chr(int(path[index + 1:index + 3], 16))
                index += 3
                continue
            except ValueError:
                pass
        output += path[index]
        index += 1
    return output


def _is_forbidden(target):
    path = _decoded_path(target)
    return ".." in path or path == "/logs" or path.startswith("/logs/") or path == "/data" or path.startswith("/data/")


def _response_bytes(status, content_type, body, extra_headers=None):
    if isinstance(body, str):
        body_bytes = body.encode("utf-8")
    else:
        body_bytes = bytes(body)
    reason = router.STATUS_REASONS[status]
    headers = [
        "HTTP/1.1 " + str(status) + " " + reason,
        "Content-Type: " + content_type,
        "Content-Length: " + str(len(body_bytes)),
        "Connection: close",
    ]
    for name, value in (extra_headers or {}).items():
        headers.append(str(name) + ": " + str(value))
    return ("\r\n".join(headers) + "\r\n\r\n").encode("iso-8859-1") + body_bytes


def _handle_connection(client_socket, config):
    try:
        raw_headers = _read_request(client_socket, config.get("buffer_size", 4096))
        _, target, _, _ = _parse_request(raw_headers)
        if _is_forbidden(target):
            response = router.error_response(403, "Access to this path is forbidden.")
        else:
            response = router.route(target, config)
    except (ValueError, OSError):
        response = router.error_response(400, "The HTTP request could not be parsed.")

    try:
        client_socket.sendall(_response_bytes(*response))
    except OSError:
        pass
    finally:
        try:
            client_socket.close()
        except OSError:
            pass


class HTTPServer:
    """Accept HTTP connections and delegate each one to a daemon thread."""

    def __init__(self, config, stop_event=None):
        self.config = config
        self.stop_event = stop_event or threading.Event()
        self._listener = None

    @property
    def listening_port(self):
        if self._listener is None:
            return None
        return self._listener.getsockname()[1]

    def open(self):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            listener.bind((self.config["server_host"], self.config["http_port"]))
            listener.listen()
            listener.settimeout(0.5)
        except Exception:
            listener.close()
            raise
        self._listener = listener

    def serve_forever(self):
        if self._listener is None:
            self.open()
        try:
            while not self.stop_event.is_set():
                try:
                    client_socket, _ = self._listener.accept()
                except socket.timeout:
                    continue
                except OSError:
                    if self.stop_event.is_set():
                        break
                    raise
                threading.Thread(
                    target=_handle_connection,
                    args=(client_socket, self.config),
                    daemon=True,
                ).start()
        finally:
            self.shutdown()

    def shutdown(self):
        self.stop_event.set()
        listener = self._listener
        self._listener = None
        if listener is not None:
            try:
                listener.close()
            except OSError:
                pass


def run_http_server(config, stop_event=None, ready_event=None):
    server = HTTPServer(config, stop_event=stop_event)
    server.open()
    if ready_event is not None:
        ready_event.set()
    server.serve_forever()
