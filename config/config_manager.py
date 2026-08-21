"""Load and validate the single project configuration file."""

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.json"

REQUIRED_KEYS = (
    "tcp_port",
    "http_port",
    "server_host",
    "log_file",
    "stats_file",
    "max_clients",
    "default_homepage",
    "buffer_size",
    "command_timeout_seconds",
)


def _configuration_error(message):
    """Print one readable error line and stop without a traceback."""
    print("Configuration error: " + message)
    raise SystemExit(1)


def _require_integer(config, key, minimum, maximum=None):
    value = config[key]
    if type(value) is not int:
        _configuration_error("'" + key + "' must be an integer.")
    if value < minimum or (maximum is not None and value > maximum):
        if maximum is None:
            expected = "at least " + str(minimum)
        else:
            expected = "between " + str(minimum) + " and " + str(maximum)
        _configuration_error("'" + key + "' must be " + expected + ".")


def _require_positive_number(config, key):
    value = config[key]
    if type(value) not in (int, float) or value <= 0:
        _configuration_error("'" + key + "' must be a positive number.")


def _resolve_project_path(value, key):
    if not isinstance(value, str) or not value.strip():
        _configuration_error("'" + key + "' must be a non-empty relative path.")

    configured_path = Path(value)
    if configured_path.is_absolute():
        _configuration_error("'" + key + "' must be relative to the project root.")

    resolved_path = (PROJECT_ROOT / configured_path).resolve()
    try:
        resolved_path.relative_to(PROJECT_ROOT)
    except ValueError:
        _configuration_error("'" + key + "' must stay inside the project folder.")
    return str(resolved_path)


def _validate_config(config):
    if not isinstance(config, dict):
        _configuration_error("config.json must contain one JSON object.")

    for key in REQUIRED_KEYS:
        if key not in config:
            _configuration_error("missing required key '" + key + "'.")

    _require_integer(config, "tcp_port", 1, 65535)
    _require_integer(config, "http_port", 1, 65535)
    if config["tcp_port"] == config["http_port"]:
        _configuration_error("'tcp_port' and 'http_port' must be different.")

    if not isinstance(config["server_host"], str) or not config["server_host"].strip():
        _configuration_error("'server_host' must be a non-empty string.")

    _require_integer(config, "max_clients", 1)
    _require_integer(config, "buffer_size", 1)
    _require_positive_number(config, "command_timeout_seconds")

    homepage = config["default_homepage"]
    if not isinstance(homepage, str) or not homepage.startswith("/"):
        _configuration_error("'default_homepage' must start with '/'.")


def load_config(config_path=None):
    """Return a validated config dict with absolute runtime data paths.

    Relative paths are always interpreted from the project root, not from the
    terminal's current working directory. Any configuration problem produces
    one concise error line followed by a clean exit.
    """
    print("Loading configuration...")

    if config_path is None:
        path = DEFAULT_CONFIG_PATH
    else:
        path = Path(config_path)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        path = path.resolve()

    try:
        with path.open("r", encoding="utf-8") as config_file:
            config = json.load(config_file)
    except FileNotFoundError:
        _configuration_error("config.json was not found at " + str(path) + ".")
    except json.JSONDecodeError as error:
        _configuration_error(
            "config.json contains invalid JSON near line "
            + str(error.lineno)
            + ", column "
            + str(error.colno)
            + "."
        )
    except OSError as error:
        _configuration_error("config.json could not be read: " + str(error) + ".")

    _validate_config(config)

    loaded_config = dict(config)
    loaded_config["log_file"] = _resolve_project_path(config["log_file"], "log_file")
    loaded_config["stats_file"] = _resolve_project_path(config["stats_file"], "stats_file")
    return loaded_config
