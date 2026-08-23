"""Start the TCP server and the HTTP server (as a thread) together."""

import threading

from config.config_manager import load_config
from server import logger, statistics
from server.tcp_server import TCPServer
from web.http_server import run_http_server


def main():
    config = load_config()

    logger.init(config["log_file"])
    statistics.rebuild_from_log(config["log_file"])
    print("Logger initialized.")
    print("Statistics initialized.")

    tcp_server = TCPServer(config)
    tcp_server.open(announce=True)

    http_stop = threading.Event()
    http_ready = threading.Event()
    http_thread = threading.Thread(
        target=run_http_server,
        args=(config, http_stop, http_ready),
        name="HTTP-Server",
        daemon=True,
    )
    http_thread.start()

    if not http_ready.wait(timeout=5):
        tcp_server.shutdown()
        http_stop.set()
        raise RuntimeError("HTTP server did not start")

    print("HTTP Server started on port " + str(config["http_port"]) + ".")
    try:
        tcp_server.serve_forever(announce_waiting=True)
    finally:
        http_stop.set()
        http_thread.join(timeout=2)


if __name__ == "__main__":
    main()
