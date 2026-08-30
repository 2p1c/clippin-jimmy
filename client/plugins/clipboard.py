from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING, Any

import pyperclip

if TYPE_CHECKING:
    from client.main import Bus

POLL_INTERVAL = 0.3


class ClipboardPlugin:
    name = "clipboard"

    def start(self, bus: Bus) -> None:
        thread = threading.Thread(target=self._loop, args=(bus,), daemon=True)
        thread.start()

    def on_message(self, msg: dict[str, Any]) -> None:
        return None

    def _loop(self, bus: Bus) -> None:
        last = _read_clipboard()
        while True:
            time.sleep(POLL_INTERVAL)
            current = _read_clipboard()
            if current is None or current == last:
                continue
            last = current
            text = current.strip()
            if not text:
                continue
            if len(text) > 20000:
                bus.log("剪贴板内容过长，已跳过")
                continue
            bus.send("clipboard", text)


def _read_clipboard() -> str | None:
    try:
        value = pyperclip.paste()
    except Exception:
        return None
    if not isinstance(value, str):
        return None
    return value
