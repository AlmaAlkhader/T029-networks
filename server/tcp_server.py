"""Multi-threaded TCP accept loop for the Network Diagnostic System."""

import socket
import threading
from datetime import datetime


class TCPServer:
    """Accept clients in one thread and delegate each client to its own thread."""

    def __init__(
        self,
        config,
        stop_event=None,
        client_handler_module=None,
        statistics_module=None,
        protocol_module=None,
    ):
        if client_handler_module is None:
            from server import client_handler as client_handler_module
        if statistics_module is None:
            from server import statistics as statistics_module
        if protocol_module is None:
            from core import protocol as protocol_module

        self.config = config
        self.stop_event = stop_event or threading.Event()
        self.client_handler = client_handler_module
        self.statistics = statistics_module
        self.protocol = protocol_module

        self._listener = None
        self._shutdown_lock = threading.Lock()
        self._thread_counter_lock = threading.Lock()
        self._thread_counter = 0
        self._client_slots = threading.BoundedSemaphore(config["max_clients"])

    @property
    def listening_port(self):
        if self._listener is None:
            return None
        return self._listener.getsockname()[1]

    def _next_thread_name(self):
        with self._thread_counter_lock:
            self._thread_counter += 1
            return "Thread-" + str(self._thread_counter)

    def open(self, announce=True):
        """Create, configure, bind, and listen without entering accept()."""
        if self._listener is not None:
            return

        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind((self.config["server_host"], self.config["tcp_port"]))
            listener.listen(self.config["max_clients"])
            listener.settimeout(0.5)
        except Exception:
            listener.close()
            raise

        self._listener = listener
        if announce:
            print("TCP Server started on port " + str(self.listening_port) + ".")

    def _at_client_limit(self):
        reserved = self._client_slots.acquire(blocking=False)
        if not reserved:
            return True

        try:
            active_clients = self.statistics.get_snapshot().get("active_clients", 0)
        except Exception:
            active_clients = 0

        if active_clients >= self.config["max_clients"]:
            self._client_slots.release()
            return True
        return False

    def _reject_full_client(self, client_socket):
        try:
            self.protocol.send_message(
                client_socket,
                {
                    "type": "error",
                    "status": "Failed",
                    "command": "",
                    "parameter": "",
                    "output": "",
                    "error": "Server full: maximum number of clients reached.",
                    "execution_time": 0.0,
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                },
            )
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            try:
                client_socket.close()
            except OSError:
                pass

    def _dispatch_client(self, client_socket, client_address):
        print("Client connected:")
        print(str(client_address[0]) + ":" + str(client_address[1]))

        if self._at_client_limit():
            print("Connection rejected: server full.")
            rejection_thread = threading.Thread(
                target=self._reject_full_client,
                args=(client_socket,),
                name="Server-Full-Rejection",
                daemon=True,
            )
            rejection_thread.start()
            return

        thread_name = self._next_thread_name()
        client_thread = threading.Thread(
            target=self.client_handler.handle_client,
            args=(
                client_socket,
                client_address,
                self.config,
                self._client_slots.release,
            ),
            name=thread_name,
            daemon=True,
        )
        print(thread_name + " created.")

        try:
            client_thread.start()
        except Exception:
            self._client_slots.release()
            client_socket.close()
            raise

    def serve_forever(self, announce_waiting=True):
        """Run only the required accept-and-spawn loop in the calling thread."""
        if self._listener is None:
            self.open(announce=True)

        if announce_waiting:
            print("Waiting for client connections...")

        try:
            while not self.stop_event.is_set():
                try:
                    client_socket, client_address = self._listener.accept()
                except socket.timeout:
                    continue
                except OSError:
                    if self.stop_event.is_set():
                        break
                    raise

                self._dispatch_client(client_socket, client_address)
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()

    def shutdown(self):
        """Stop accepting clients and close the listening socket safely."""
        self.stop_event.set()
        with self._shutdown_lock:
            listener = self._listener
            self._listener = None
            if listener is None:
                return
            try:
                listener.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                listener.close()
            except OSError:
                pass


def run_tcp_server(config, stop_event=None):
    """Convenience entry point used by the team's run_server.py."""
    server = TCPServer(config, stop_event=stop_event)
    server.serve_forever()
    return server
