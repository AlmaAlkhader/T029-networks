"""Start the TCP server and separate-process HTTP server together."""

import multiprocessing

from config.config_manager import load_config
from server import logger
from server.tcp_server import TCPServer
from web.http_server import run_http_server


def main():
    config = load_config()
    logger.init(config["log_file"])
    print("Logger initialized.")
    print("Statistics initialized.")

    tcp_server = TCPServer(config)
    tcp_server.open(announce=True)

    http_stop = multiprocessing.Event()
    http_ready = multiprocessing.Event()
    http_process = multiprocessing.Process(
        target=run_http_server,
        args=(config, http_stop, http_ready),
        name="HTTP-Server",
    )
    http_process.start()
    if not http_ready.wait(timeout=5):
        tcp_server.shutdown()
        http_process.terminate()
        http_process.join()
        raise RuntimeError("HTTP server did not start")

    print("HTTP Server started on port " + str(config["http_port"]) + ".")
    try:
        tcp_server.serve_forever(announce_waiting=True)
    finally:
        http_stop.set()
        http_process.join(timeout=2)
        if http_process.is_alive():
            http_process.terminate()
            http_process.join()


if __name__ == "__main__":
    main()
