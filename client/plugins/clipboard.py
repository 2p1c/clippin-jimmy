from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING, Any

import pyperclip

if TYPE_CHECKING:
    from client.main import Bus

POLL_INTERVAL = 0.3
MAX_LEN = 20000
_CLIPBOARD_LOCK = threading.Lock()


class ClipboardPlugin:
    name = "clipboard"

    def start(self, bus: Bus) -> None:
        thread = threading.Thread(target=self._loop, args=(bus,), daemon=True)
        thread.start()

    def on_message(self, msg: dict[str, Any]) -> None:
        return None

    def _loop(self, bus: Bus) -> None:
        last = read_clipboard()
        while True:
            time.sleep(POLL_INTERVAL)
            current = read_clipboard()
            if current is None or current == last:
                continue
            last = current
            text = current.strip()
            if not text:
                continue
            if bus.is_local_clip(text) or bus.is_local_clip(current):
                continue
            if len(text) > MAX_LEN:
                bus.log("剪贴板内容过长，已跳过")
                continue
            if bus.send("clipboard", text):
                bus.display({"type": "clipboard", "sender": bus.name, "text": text})


def write_clipboard(text: str) -> bool:
    try:
        with _CLIPBOARD_LOCK:
            pyperclip.copy(text)
    except Exception:
        return False
    return True


def read_clipboard() -> str | None:
    try:
        with _CLIPBOARD_LOCK:
            value = pyperclip.paste()
    except Exception:
        return None
    if not isinstance(value, str):
        return None
    return value
