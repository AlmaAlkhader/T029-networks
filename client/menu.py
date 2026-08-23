"""Interactive terminal menu for the TCP client."""

from core.validation import validate_command

from client import display, tcp_client


MENU_HEADER = """=========================================
 Network Diagnostic System
=========================================
1. Ping Host
2. Trace Route
3. DNS Lookup
4. IP Configuration
5. Routing Table
6. ARP Table
7. Active TCP Connections
8. Exit"""

COMMANDS = {
    1: "PING",
    2: "TRACERT",
    3: "NSLOOKUP",
    4: "IPCONFIG",
    5: "ROUTE",
    6: "ARP",
    7: "NETSTAT",
    8: "EXIT",
}


def _read_selection():
    while True:
        print(MENU_HEADER)
        raw_selection = input("Select:").strip()
        try:
            selection = int(raw_selection)
        except ValueError:
            print("Invalid selection. Enter a number from 1 to 8.")
            continue
        if selection not in COMMANDS:
            print("Invalid selection. Enter a number from 1 to 8.")
            continue
        return selection


def run(sock):
    """Run the menu until EXIT, server rejection, disconnect, or Ctrl+C."""
    try:
        first_message = tcp_client.receive_welcome(sock)
        if first_message.get("type") == "error":
            display.display_server_message(first_message)
            return
        print(str(first_message.get("message", "Connected.")))

        while True:
            selection = _read_selection()
            command = COMMANDS[selection]
            parameter = ""
            if selection in (1, 2, 3):
                parameter = input("Enter hostname:").strip()

            is_valid, validation_error = validate_command(command, parameter)
            if not is_valid:
                print(validation_error)
                continue

            tcp_client.send_request(sock, command, parameter)
            response = tcp_client.receive_response(sock)
            if response.get("type") == "error":
                display.display_server_message(response)
                return
            if response.get("type") == "welcome":
                display.display_server_message(response)
                continue

            display.display_response(response)
            if command == "EXIT":
                return
            input("Press ENTER to continue...")
    except KeyboardInterrupt:
        print("\nClient closed.")
    except (ConnectionError, OSError) as error:
        print("Connection closed: " + str(error))
    finally:
        try:
            sock.close()
        except OSError:
            pass
