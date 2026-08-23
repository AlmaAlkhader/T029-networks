"""I keep the command and hostname checks for the client in this file."""

from __future__ import annotations

from core.protocol import ALLOWED_COMMANDS


# This is the command menu we're using:
# 1 PING     -> PING     (needs a hostname)
# 2 TRACERT  -> TRACERT  (needs a hostname)
# 3 NSLOOKUP -> NSLOOKUP (needs a hostname)
# 4 IPCONFIG -> IPCONFIG (doesn't need a parameter)
# 5 ROUTE    -> ROUTE    (doesn't need a parameter)
# 6 ARP      -> ARP      (doesn't need a parameter)
# 7 NETSTAT  -> NETSTAT  (doesn't need a parameter)
# 8 EXIT     -> EXIT     (doesn't need a parameter)
_HOSTNAME_COMMANDS = frozenset({"PING", "TRACERT", "NSLOOKUP"})

# I list the characters myself so Python's Unicode letter checks don't
# accidentally allow characters outside the original A-Z and 0-9 rules.
_HOSTNAME_CHARACTERS = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-"
)


def _is_valid_hostname(hostname: str) -> bool:
    """I check the hostname one label at a time instead of using a regex."""
    if not hostname or len(hostname) > 253:
        return False

    # A hostname can have one final dot, so I remove it before checking labels.
    if hostname.endswith("."):
        hostname = hostname[:-1]

    if not hostname:
        return False

    labels = hostname.split(".")

    for label in labels:
        if not label or len(label) > 63:
            return False

        if label.startswith("-") or label.endswith("-"):
            return False

        if any(character not in _HOSTNAME_CHARACTERS for character in label):
            return False

    return True


def validate_command(command: str, parameter: str) -> tuple[bool, str]:
    """I check the command and make sure it has a safe hostname when needed."""
    if command not in ALLOWED_COMMANDS:
        return False, f"Unknown command: {command!r}"

    if command in _HOSTNAME_COMMANDS:
        if not isinstance(parameter, str) or not parameter:
            return False, f"{command} requires a hostname parameter"
        if not _is_valid_hostname(parameter):
            return False, "Invalid hostname: use only letters, digits, dots, and hyphens"

    return True, ""
