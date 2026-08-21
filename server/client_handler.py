"""Handle one TCP client inside its own dedicated thread."""

import json
import socket
from datetime import datetime


WELCOME_MESSAGE = {
    "type": "welcome",
    "message": "Connected to Network Diagnostic Server",
}


def _timestamp_now():
    return datetime.now().isoformat(timespec="seconds")


def _failed_response(command, parameter, error_message, timestamp=None):
    return {
        "status": "Failed",
        "command": command,
        "parameter": parameter,
        "output": "",
        "error": error_message,
        "execution_time": 0.0,
        "timestamp": timestamp or _timestamp_now(),
    }


def _normalize_execution_result(result):
    if not isinstance(result, dict):
        raise ValueError("command_executor.execute() must return a dictionary")

    status = result.get("status")
    if status not in ("Success", "Failed"):
        status = "Failed"

    output = result.get("output", "")
    if output is None:
        output = ""
    elif not isinstance(output, str):
        output = str(output)

    execution_time = result.get("execution_time", 0.0)
    if type(execution_time) not in (int, float) or execution_time < 0:
        execution_time = 0.0

    error_message = result.get("error", "")
    if status == "Failed" and not error_message:
        error_message = output or "The command could not be completed."

    return status, output, float(execution_time), str(error_message)


def _load_default_dependencies():
    # Imports are delayed so Mohammad's files can be tested before the other
    # team members finish their modules.
    from core import protocol
    from core import validation
    from server import command_executor
    from server import logger
    from server import statistics

    return protocol, validation, command_executor, logger, statistics


def _record_request(
    logger_module,
    statistics_module,
    client_address,
    command,
    parameter,
    execution_time,
    status,
    timestamp,
):
    entry = {
        "timestamp": timestamp,
        "client_ip": client_address[0],
        "client_port": client_address[1],
        "command": command,
        "parameter": parameter,
        "execution_time": execution_time,
        "status": status,
    }

    try:
        logger_module.log_request(entry)
    except Exception as error:
        print(
            "Logging error for "
            + str(client_address[0])
            + ":"
            + str(client_address[1])
            + ": "
            + str(error)
        )

    try:
        statistics_module.record_request(
            command,
            execution_time,
            status == "Success",
        )
    except Exception as error:
        print("Statistics update error: " + str(error))


def _send_and_record_failure(
    client_socket,
    client_address,
    command,
    parameter,
    error_message,
    protocol_module,
    logger_module,
    statistics_module,
):
    response = _failed_response(command, parameter, error_message)
    try:
        protocol_module.send_message(client_socket, response)
    finally:
        _record_request(
            logger_module,
            statistics_module,
            client_address,
            command,
            parameter,
            0.0,
            "Failed",
            response["timestamp"],
        )


def handle_client(
    client_socket,
    client_address,
    config,
    on_close=None,
    protocol_module=None,
    validation_module=None,
    executor_module=None,
    logger_module=None,
    statistics_module=None,
):
    """Serve exactly one connected client until EXIT or disconnection.

    The optional module arguments are only test hooks. In the complete project,
    tcp_server calls this function with the first four arguments and the real
    modules supplied by Alma and Eman are imported automatically.
    """
    if (
        protocol_module is None
        or validation_module is None
        or executor_module is None
        or logger_module is None
        or statistics_module is None
    ):
        defaults = _load_default_dependencies()
        protocol_module = protocol_module or defaults[0]
        validation_module = validation_module or defaults[1]
        executor_module = executor_module or defaults[2]
        logger_module = logger_module or defaults[3]
        statistics_module = statistics_module or defaults[4]

    client_counted = False

    try:
        statistics_module.client_connected()
        client_counted = True
        protocol_module.send_message(client_socket, WELCOME_MESSAGE)

        while True:
            try:
                request = protocol_module.receive_message(client_socket)
            except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
                _send_and_record_failure(
                    client_socket,
                    client_address,
                    "INVALID",
                    "",
                    "Malformed JSON request.",
                    protocol_module,
                    logger_module,
                    statistics_module,
                )
                continue

            if request is None:
                break

            if not isinstance(request, dict):
                _send_and_record_failure(
                    client_socket,
                    client_address,
                    "INVALID",
                    "",
                    "Request must be a JSON object.",
                    protocol_module,
                    logger_module,
                    statistics_module,
                )
                continue

            command = request.get("command", "")
            parameter = request.get("parameter", "")

            if not isinstance(command, str) or not isinstance(parameter, str):
                _send_and_record_failure(
                    client_socket,
                    client_address,
                    "INVALID" if not isinstance(command, str) else command,
                    "" if not isinstance(parameter, str) else parameter,
                    "Command and parameter must both be strings.",
                    protocol_module,
                    logger_module,
                    statistics_module,
                )
                continue

            is_valid, validation_error = validation_module.validate_command(
                command,
                parameter,
            )
            if not is_valid:
                _send_and_record_failure(
                    client_socket,
                    client_address,
                    command,
                    parameter,
                    validation_error or "Invalid command or parameter.",
                    protocol_module,
                    logger_module,
                    statistics_module,
                )
                continue

            if command == "EXIT":
                protocol_module.send_message(
                    client_socket,
                    {
                        "status": "Success",
                        "command": "EXIT",
                        "parameter": "",
                        "output": "Connection closed.",
                        "execution_time": 0.0,
                        "timestamp": _timestamp_now(),
                    },
                )
                break

            try:
                result = executor_module.execute(command, parameter)
                status, output, execution_time, execution_error = (
                    _normalize_execution_result(result)
                )
            except Exception:
                status = "Failed"
                output = ""
                execution_time = 0.0
                execution_error = "The server could not execute the command."

            timestamp = _timestamp_now()
            response = {
                "status": status,
                "command": command,
                "parameter": parameter,
                "output": output,
                "execution_time": execution_time,
                "timestamp": timestamp,
            }
            if status == "Failed":
                response["error"] = execution_error

            try:
                protocol_module.send_message(client_socket, response)
            finally:
                # A completed command is logged even if its client disconnects
                # before receiving the result.
                _record_request(
                    logger_module,
                    statistics_module,
                    client_address,
                    command,
                    parameter,
                    execution_time,
                    status,
                    timestamp,
                )

    except (ConnectionResetError, BrokenPipeError, socket.timeout, OSError):
        pass
    except Exception as error:
        # No client can terminate the listening server or another client thread.
        print(
            "Client thread error for "
            + str(client_address[0])
            + ":"
            + str(client_address[1])
            + ": "
            + str(error)
        )
    finally:
        try:
            client_socket.close()
        except OSError:
            pass

        if client_counted:
            try:
                statistics_module.client_disconnected()
            except Exception as error:
                print("Statistics disconnect error: " + str(error))

        if on_close is not None:
            try:
                on_close()
            except Exception as error:
                print("Client cleanup error: " + str(error))

        print("Client disconnected:")
        print(str(client_address[0]) + ":" + str(client_address[1]))
