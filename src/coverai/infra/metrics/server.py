from prometheus_client import start_http_server

_started_ports: set[int] = set()


def start_metrics_server(port: int) -> None:
    """Запускает metrics server."""
    if port in _started_ports:
        return

    start_http_server(port)
    _started_ports.add(port)
