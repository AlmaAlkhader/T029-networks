"""Fresh JSONL search with dependency-free query-string parsing."""

import html

from web import pages


def _decode_component(value):
    value = value.replace("+", " ")
    result = bytearray()
    index = 0
    while index < len(value):
        if value[index] == "%" and index + 2 < len(value):
            try:
                result.append(int(value[index + 1:index + 3], 16))
                index += 3
                continue
            except ValueError:
                pass
        result.extend(value[index].encode("utf-8"))
        index += 1
    return result.decode("utf-8", errors="replace")


def parse_query(query_string):
    filters = {"type": "", "hostname": "", "ip": ""}
    for pair in query_string.split("&"):
        if not pair:
            continue
        key, separator, value = pair.partition("=")
        key = _decode_component(key)
        if separator and key in filters:
            filters[key] = _decode_component(value)
    return filters


def _matches(entry, filters):
    mappings = {
        "type": str(entry.get("command", "")),
        "hostname": str(entry.get("parameter", "")),
        "ip": str(entry.get("client_ip", "")),
    }
    return all(
        not value or value.casefold() in mappings[key].casefold()
        for key, value in filters.items()
    )


def search_page(config, query_string):
    filters = parse_query(query_string)
    entries = pages.read_log_entries(config["log_file"])
    matches = [entry for entry in entries if _matches(entry, filters)]
    form = """<h1>Search</h1><form method="GET" action="/search">
<label>Command <input name="type" value="{type}"></label>
<label>Hostname <input name="hostname" value="{hostname}"></label>
<label>Client IP <input name="ip" value="{ip}"></label>
<button type="submit">Search</button></form>""".format(
        type=html.escape(filters["type"], quote=True),
        hostname=html.escape(filters["hostname"], quote=True),
        ip=html.escape(filters["ip"], quote=True),
    )
    has_filters = any(filters.values())
    if has_filters and not matches:
        results = '<p class="message">No matching results found.</p>'
    else:
        results = pages.entries_table(list(reversed(matches)))
    return pages.page("Search", form + results)
