"""Validation rules for client network commands."""

from __future__ import annotations

import re

from core.protocol import ALLOWED_COMMANDS


# Command-keyword table:
# 1 PING     -> PING     (hostname required)
# 2 TRACERT  -> TRACERT  (hostname required)
# 3 NSLOOKUP -> NSLOOKUP (hostname required)
# 4 IPCONFIG -> IPCONFIG (no parameter)
# 5 ROUTE    -> ROUTE    (no parameter)
# 6 ARP      -> ARP      (no parameter)
# 7 NETSTAT  -> NETSTAT  (no parameter)
# 8 EXIT     -> EXIT     (no parameter)
_HOSTNAME_COMMANDS = frozenset({"PING", "TRACERT", "NSLOOKUP"})
_HOSTNAME_PATTERN = re.compile(
    r"^(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)(?:\.(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?))*\.?$"
)


def validate_command(command: str, parameter: str) -> tuple[bool, str]:
    """Validate a command keyword and any required hostname parameter.

    Parameters supplied to commands that do not need one are intentionally
    ignored. Hostnames permit only letters, digits, dots, and hyphens, with a
    maximum total length of 253 and maximum label length of 63 characters.
    """

    if command not in ALLOWED_COMMANDS:
        return False, f"Unknown command: {command!r}"

    if command in _HOSTNAME_COMMANDS:
        if not isinstance(parameter, str) or not parameter:
            return False, f"{command} requires a hostname parameter"
        if not _HOSTNAME_PATTERN.fullmatch(parameter):
            return False, "Invalid hostname: use only letters, digits, dots, and hyphens"

    return True, ""
