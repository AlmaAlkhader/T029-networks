"""Start the interactive Network Diagnostic System client."""

from client import menu, tcp_client
from config.config_manager import load_config


def main():
    config = load_config()
    host = config["server_host"]
    if host == "0.0.0.0":
        host = "127.0.0.1"
    try:
        sock = tcp_client.connect_to_server(host, config["tcp_port"])
    except ConnectionRefusedError as error:
        print(str(error))
        return
    menu.run(sock)


if __name__ == "__main__":
    main()
