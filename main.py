"""Lanceur local de la plateforme INRH.

Usage:
    python main.py
    python main.py --open-browser
"""

from __future__ import annotations

import argparse
import os
import signal
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
DJANGO_DIR = ROOT_DIR / "web_platform"
children: list[subprocess.Popen] = []


def get_project_python() -> str:
    """Utilise automatiquement le Python du projet lorsqu'il existe."""
    virtualenv_python = ROOT_DIR / ".venv" / "bin" / "python"
    if virtualenv_python.is_file():
        return str(virtualenv_python)
    return sys.executable


def run_command(command: list[str], *, cwd: Path = ROOT_DIR) -> None:
    print(f"[main] $ {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def start_process(command: list[str], *, cwd: Path = ROOT_DIR) -> subprocess.Popen:
    print(f"[main] Démarrage : {' '.join(command)}", flush=True)
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env={**os.environ, "PYTHONPATH": str(ROOT_DIR)},
    )
    children.append(process)
    return process


def stop_processes() -> None:
    for process in reversed(children):
        if process.poll() is None:
            process.terminate()

    deadline = time.monotonic() + 10
    for process in reversed(children):
        if process.poll() is None:
            remaining = max(0, deadline - time.monotonic())
            try:
                process.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def stop_all(*_args) -> None:
    print("\n[main] Arrêt des processus...", flush=True)
    stop_processes()
    print("[main] Services Docker conservés actifs.", flush=True)
    raise SystemExit(0)


def check_children() -> None:
    for process in children:
        return_code = process.poll()
        if return_code is not None:
            raise RuntimeError(
                f"Un processus de la plateforme s'est arrêté avec le code {return_code}."
            )


def ensure_port_available(port: int) -> None:
    """Refuse an occupied dashboard port before starting the worker."""
    if not 1 <= port <= 65535:
        raise ValueError(f"Le port doit être compris entre 1 et 65535 : {port}.")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind(("127.0.0.1", port))
        except OSError as error:
            raise RuntimeError(
                f"Le port {port} est déjà utilisé. "
                f"Arrêtez le processus existant ou relancez avec --port "
                f"<port-libre> (exemple : --port 8001)."
            ) from error


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Démarre Docker, Celery et le dashboard Django."
    )
    parser.add_argument(
        "--open-browser",
        action="store_true",
        help="Ouvre le dashboard dans le navigateur par défaut.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port HTTP du dashboard Django (défaut : 8000).",
    )
    args = parser.parse_args()
    django_url = f"http://127.0.0.1:{args.port}/"
    python = get_project_python()

    signal.signal(signal.SIGINT, stop_all)
    signal.signal(signal.SIGTERM, stop_all)

    try:
        ensure_port_available(args.port)
        run_command(["docker", "compose", "up", "-d", "--wait"])
        print("[main] PostgreSQL, Redis et MinIO sont prêts.", flush=True)

        start_process(
            [
                python,
                "-m",
                "celery",
                "-A",
                "data_pipeline.celery_app",
                "worker",
                "--loglevel=info",
                "--pool=solo",
            ]
        )
        start_process(
            [python, "manage.py", "runserver", f"127.0.0.1:{args.port}"],
            cwd=DJANGO_DIR,
        )

        print(f"[main] Dashboard disponible sur {django_url}", flush=True)
        if args.open_browser:
            webbrowser.open(django_url)

        while True:
            check_children()
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        stop_processes()
        raise
    except RuntimeError as error:
        stop_processes()
        print(f"[main] Erreur : {error}", file=sys.stderr, flush=True)
        raise SystemExit(1) from error
    except Exception:
        stop_processes()
        raise


if __name__ == "__main__":
    main()
