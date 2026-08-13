"""Plattformübergreifender Starter für die gepackte Mini-SIEM-Anwendung.

Der Launcher startet FastAPI ausschliesslich auf dem lokalen Rechner und öffnet
die Weboberfläche, sobald der Health-Check des Servers erreichbar ist.
"""

import argparse
import multiprocessing
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from collections.abc import Sequence

import uvicorn

from main import app


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
STARTUP_TIMEOUT_SECONDS = 15.0


def build_argument_parser() -> argparse.ArgumentParser:
    """Erstellt die Kommandozeilenoptionen des Launchers."""

    parser = argparse.ArgumentParser(
        description="Startet SSH Sentinel als lokale Webanwendung.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Lokaler HTTP-Port (Standard: {DEFAULT_PORT}).",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Browser nach dem Start nicht automatisch öffnen.",
    )
    return parser


def port_is_available(host: str, port: int) -> bool:
    """Prüft, ob der gewünschte lokale TCP-Port gebunden werden kann."""

    if not 1 <= port <= 65535:
        return False

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((host, port))
    except OSError:
        return False
    return True


def wait_for_server_and_open(url: str, timeout: float = STARTUP_TIMEOUT_SECONDS) -> None:
    """Wartet auf den Health-Check und öffnet anschliessend die Startseite."""

    health_url = f"{url}/api/health"
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(health_url, timeout=0.5) as response:
                if response.status == 200:
                    webbrowser.open(url)
                    return
        except (OSError, urllib.error.URLError):
            time.sleep(0.2)

    print(
        f"Hinweis: Der Browser konnte nicht automatisch geöffnet werden. Öffne {url} manuell.",
        file=sys.stderr,
    )


def run(argv: Sequence[str] | None = None) -> int:
    """Validiert die Optionen und startet den lokalen Uvicorn-Server."""

    args = build_argument_parser().parse_args(argv)
    if not 1 <= args.port <= 65535:
        print("Fehler: Der Port muss zwischen 1 und 65535 liegen.", file=sys.stderr)
        return 2

    if not port_is_available(DEFAULT_HOST, args.port):
        alternative_port = args.port + 1 if args.port < 65535 else DEFAULT_PORT
        print(
            f"Fehler: Port {args.port} ist bereits belegt. "
            f"Starte die App zum Beispiel mit --port {alternative_port}.",
            file=sys.stderr,
        )
        return 1

    url = f"http://{DEFAULT_HOST}:{args.port}"
    if not args.no_browser:
        threading.Thread(
            target=wait_for_server_and_open,
            args=(url,),
            daemon=True,
            name="browser-opener",
        ).start()

    print(f"SSH Sentinel läuft unter {url}")
    print("Zum Beenden Ctrl+C drücken oder dieses Fenster schliessen.")

    # Explizite Implementierungen vermeiden dynamische Auto-Auswahl und machen
    # den PyInstaller-Build auf Linux und Windows reproduzierbarer.
    uvicorn.run(
        app,
        host=DEFAULT_HOST,
        port=args.port,
        loop="asyncio",
        http="h11",
        # Die App definiert keine Startup-/Shutdown-Hooks. Ohne Lifespan bleibt
        # auch das Beenden des gepackten Programms per Ctrl+C frei von Warnungen.
        lifespan="off",
        reload=False,
        workers=1,
    )
    return 0


if __name__ == "__main__":
    # Unter Windows benötigt ein eingefrorenes Programm diesen Aufruf für Module,
    # die intern Multiprocessing-Unterstützung verwenden könnten.
    multiprocessing.freeze_support()
    raise SystemExit(run())
