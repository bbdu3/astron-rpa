#!/usr/bin/env python3
"""Launch the astron-rpa Engine scheduler and its managed services."""

import argparse
import os
import signal
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ENGINE_DIR = SCRIPT_DIR.parent
REPO_ROOT = ENGINE_DIR.parent
RESOURCES_DIR = REPO_ROOT / "resources"
DEFAULT_CONF = RESOURCES_DIR / "conf.yaml"

RUN_MODES = {
    "dev": "Start the scheduler and all services managed by it.",
    "rpa-dev": "Alias for dev.",
    "scheduler": "Alias for dev.",
}


def resolve_conf(path: str) -> Path:
    conf = Path(path).expanduser().resolve()
    if not conf.is_file():
        raise FileNotFoundError(f"Configuration file does not exist: {conf}")
    return conf


def build_scheduler_cmd(conf: Path) -> list[str]:
    return [sys.executable, "-m", "astronverse.scheduler", "--conf", str(conf)]


def stop_engine_processes() -> None:
    """Reuse the scheduler's Windows-aware process cleanup implementation."""
    from astronverse.scheduler.core.setup.setup import Process

    Process.kill_all_zombie()


def start_scheduler(command: list[str]) -> subprocess.Popen:
    """Start the scheduler in a process group that can be stopped as a unit."""
    popen_kwargs = {"cwd": ENGINE_DIR}
    if sys.platform == "win32":
        # Keep Ctrl+C in this launcher. The scheduler receives an explicit tree
        # termination below, instead of leaving shell-spawned services behind.
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        popen_kwargs["start_new_session"] = True
    return subprocess.Popen(command, **popen_kwargs)


def stop_scheduler(process: subprocess.Popen) -> None:
    """Terminate the scheduler and every process it started."""
    if sys.platform == "win32":
        # Popen.terminate() only terminates the scheduler executable on Windows;
        # taskkill /T is needed for services started through cmd.exe as well.
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        except ProcessLookupError:
            pass

    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            process.kill()
        process.wait()


def run_scheduler(conf: Path) -> int:
    command = build_scheduler_cmd(conf)
    sys.stdout.write(f"[dev] Starting scheduler: {' '.join(command)}\n")

    process = start_scheduler(command)
    try:
        return process.wait()
    except KeyboardInterrupt:
        sys.stdout.write("\n[dev] Stopping scheduler...\n")
        return 0
    finally:
        if process.poll() is None:
            stop_scheduler(process)
        stop_engine_processes()


def build_parser() -> argparse.ArgumentParser:
    modes = ", ".join(RUN_MODES)
    parser = argparse.ArgumentParser(
        prog="uv run scripts/start.py",
        description="AstronRPA Engine launcher for the scheduler-managed architecture.",
        epilog=(
            f"modes: {modes}\n"
            "examples:\n"
            "  uv run scripts/start.py dev\n"
            "  uv run scripts/start.py dev --conf ../resources/conf.local.yaml\n"
            "  uv run scripts/start.py stop"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("mode", choices=[*RUN_MODES, "stop"], help="run mode or stop")
    parser.add_argument(
        "--conf",
        type=Path,
        default=DEFAULT_CONF,
        help=f"scheduler configuration file (default: {DEFAULT_CONF})",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.mode == "stop":
        stop_engine_processes()
        sys.stdout.write("[dev] Engine processes stopped.\n")
        return 0

    try:
        conf = resolve_conf(str(args.conf))
    except FileNotFoundError as exc:
        sys.stderr.write(f"[dev] {exc}\n")
        return 1

    return run_scheduler(conf)


if __name__ == "__main__":
    raise SystemExit(main())
