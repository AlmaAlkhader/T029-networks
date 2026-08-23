"""Exact HTTP route mapping for the web interface."""

from web import download, pages, search


STATUS_REASONS = {
    200: "OK",
    400: "Bad Request",
    403: "Forbidden",
    404: "Not Found",
}


def error_response(status, message):
    reason = STATUS_REASONS[status]
    return status, "text/html; charset=UTF-8", pages.error_page(status, reason, message), {}


def route(request_target, config):
    path, separator, query = request_target.partition("?")
    if path == "/":
        path = config["default_homepage"]

    if path == "/home":
        return 200, "text/html; charset=UTF-8", pages.home_page(), {}
    if path == "/dashboard":
        return 200, "text/html; charset=UTF-8", pages.dashboard_page(), {}
    if path == "/history":
        return 200, "text/html; charset=UTF-8", pages.history_page(config), {}
    if path == "/statistics":
        return 200, "text/html; charset=UTF-8", pages.statistics_page(), {}
    if path == "/search":
        return 200, "text/html; charset=UTF-8", search.search_page(config, query if separator else ""), {}
    if path == "/download":
        return download.log_download(config)
    return error_response(404, "The requested page does not exist.")
