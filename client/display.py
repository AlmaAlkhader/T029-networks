"""Terminal formatting for diagnostic responses."""


BORDER = "========================================="


def display_response(response):
    """Print one normal command response in the execution-scenario format."""
    command = str(response.get("command", ""))
    parameter = str(response.get("parameter", ""))
    command_line = command + ((" " + parameter) if parameter else "")
    status = str(response.get("status", "Failed"))
    execution_time = response.get("execution_time", 0.0)
    try:
        formatted_time = f"{float(execution_time):.2f}"
    except (TypeError, ValueError):
        formatted_time = "0.00"

    print(BORDER)
    print("Command : " + command_line)
    print("Status : " + status)
    print("Time : " + formatted_time + " seconds")
    print()

    output = response.get("output", "")
    if status == "Failed":
        error = response.get("error") or "The command failed."
        print("Error: " + str(error))
        if output:
            print(str(output))
    elif output:
        print(str(output))

    print(BORDER)


def display_server_message(message):
    """Print a welcome or server-level error without normal-response fields."""
    text = message.get("error") or message.get("message") or "Server message"
    print(BORDER)
    print("Server: " + str(text))
    print(BORDER)
