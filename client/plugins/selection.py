from __future__ import annotations

import atexit
import json
import queue
import shutil
import subprocess
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any

from client.plugins.clipboard import write_clipboard

if TYPE_CHECKING:
    from client.main import Bus

HELPER_DIR = Path(__file__).resolve().parent / "selection_hook"
LISTENER = HELPER_DIR / "listener.js"
MAX_LEN = 20000


class SelectionPlugin:
    name = "selection"

    def __init__(self) -> None:
        self._proc: subprocess.Popen[str] | None = None

    def start(self, bus: Bus) -> None:
        atexit.register(self._stop)
        thread = threading.Thread(target=self._loop, args=(bus,), daemon=True)
        thread.start()

    def on_message(self, msg: dict[str, Any]) -> None:
        return None

    def _loop(self, bus: Bus) -> None:
        proc = _spawn_listener(bus)
        if proc is None or proc.stdout is None:
            return
        self._proc = proc
        events: queue.Queue[str | None] = queue.Queue()

        def _read_stdout() -> None:
            try:
                for raw in proc.stdout:
                    events.put(raw)
            finally:
                events.put(None)

        threading.Thread(target=_read_stdout, daemon=True).start()
        last = ""
        try:
            while True:
                raw = events.get()
                if raw is None:
                    break
                event = _parse_event(raw)
                if event is None:
                    continue
                kind = event.get("type")
                if kind == "error":
                    message = str(event.get("message", "")).strip()
                    if message:
                        bus.log(message)
                    continue
                if kind != "selection":
                    continue
                text = str(event.get("text", "")).strip()
                if not text or text == last or len(text) > MAX_LEN:
                    continue
                last = text
                try:
                    bus.mark_local_clip(text)
                    write_clipboard(text)
                    if bus.send("clipboard", text):
                        bus.display({"type": "clipboard", "sender": bus.name, "text": text})
                except Exception as exc:
                    bus.log(f"划词发送失败: {exc}")
        finally:
            self._stop()

    def _stop(self) -> None:
        proc = self._proc
        self._proc = None
        if proc is None or proc.poll() is not None:
            return
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()


def _spawn_listener(bus: Bus) -> subprocess.Popen[str] | None:
    node = shutil.which("node")
    if node is None:
        bus.log("划词功能需要 Node.js，安装后重启客户端即可。")
        return None
    if not LISTENER.is_file():
        bus.log("找不到划词监听脚本，已跳过。")
        return None
    if not _ensure_native_module(bus):
        return None
    try:
        return subprocess.Popen(
            [node, str(LISTENER)],
            cwd=HELPER_DIR,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
            start_new_session=True,
        )
    except OSError as exc:
        bus.log(f"划词监听启动失败: {exc}")
        return None


def _ensure_native_module(bus: Bus) -> bool:
    module_dir = HELPER_DIR / "node_modules" / "selection-hook"
    if module_dir.is_dir():
        return True
    npm = shutil.which("npm")
    if npm is None:
        bus.log("划词功能需要 npm，安装 Node.js 后重启客户端即可。")
        return False
    try:
        result = subprocess.run(
            [npm, "install", "--omit=dev"],
            cwd=HELPER_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        bus.log(f"划词依赖安装失败: {exc}")
        return False
    if result.returncode != 0 or not module_dir.is_dir():
        bus.log("划词依赖 selection-hook 安装失败。")
        return False
    return True


def _parse_event(raw: str) -> dict[str, Any] | None:
    line = raw.strip()
    if not line:
        return None
    try:
        payload = json.loads(line)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload
