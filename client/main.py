from __future__ import annotations

import argparse
import sys
import threading
import time
from typing import Any
from urllib.parse import quote


def _check_deps() -> None:
    missing: list[str] = []
    for name in ("httpx", "pyperclip"):
        try:
            __import__(name)
        except ImportError:
            missing.append(name)
    if missing:
        print(
            "缺少依赖: "
            + ", ".join(missing)
            + f"\n请用当前这个 Python 安装后重试:\n  {sys.executable} -m pip install -e .",
            file=sys.stderr,
        )
        raise SystemExit(1)


_check_deps()

import httpx

from client.plugins import ENABLED

POLL_INTERVAL = 1.0
HTTP_ATTEMPTS = 3
RETRYABLE_STATUS = frozenset({502, 503, 504})
TYPE_LABEL = {"chat": "chat", "clipboard": "clip"}


def _new_client() -> httpx.Client:
    return httpx.Client(
        timeout=httpx.Timeout(8.0, connect=5.0),
        trust_env=False,
        limits=httpx.Limits(max_keepalive_connections=0, max_connections=8),
        headers={"Connection": "close"},
    )


class Bus:
    def __init__(self, relay: str, room: str, name: str) -> None:
        self.relay = relay.rstrip("/")
        self.room = room
        self.name = name
        self._lock = threading.Lock()
        self._http_lock = threading.Lock()
        self._client = _new_client()
        self._local_clip: str | None = None
        self._last_fetch_error: str | None = None
        self.plugins: list[Any] = []

    def mark_local_clip(self, text: str) -> None:
        with self._lock:
            self._local_clip = text

    def is_local_clip(self, text: str) -> bool:
        with self._lock:
            return self._local_clip is not None and text == self._local_clip

    def send(self, msg_type: str, text: str) -> bool:
        try:
            self._request(
                "POST",
                self._messages_url(),
                json={"sender": self.name, "text": text, "type": msg_type},
            )
        except httpx.HTTPError as exc:
            self.log(f"发送失败: {_short_http_error(exc)}")
            return False
        return True

    def fetch_after(self, after: int) -> list[dict[str, Any]]:
        try:
            response = self._request(
                "GET",
                self._messages_url(),
                params={"after": after},
            )
        except httpx.HTTPError as exc:
            error = _short_http_error(exc)
            if error != self._last_fetch_error:
                self.log(f"拉取失败: {error}")
                self._last_fetch_error = error
            return []
        if self._last_fetch_error is not None:
            self.log("中继已恢复")
            self._last_fetch_error = None
        payload = response.json()
        messages = payload.get("messages", [])
        if not isinstance(messages, list):
            return []
        return messages

    def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        last_exc: httpx.HTTPError | None = None
        for attempt in range(HTTP_ATTEMPTS):
            try:
                with self._http_lock:
                    try:
                        response = self._client.request(method, url, **kwargs)
                    except httpx.RequestError:
                        self._reset_client()
                        raise
                    if response.status_code in RETRYABLE_STATUS:
                        self._reset_client()
                    response.raise_for_status()
                    return response
            except httpx.HTTPError as exc:
                last_exc = exc
                if not _is_retryable(exc) or attempt == HTTP_ATTEMPTS - 1:
                    break
                time.sleep(0.4 * (attempt + 1))
        assert last_exc is not None
        raise last_exc

    def _reset_client(self) -> None:
        old = self._client
        self._client = _new_client()
        try:
            old.close()
        except Exception:
            pass

    def log(self, text: str) -> None:
        with self._lock:
            print(text, file=sys.stderr, flush=True)

    def display(self, msg: dict[str, Any]) -> None:
        label = TYPE_LABEL.get(str(msg.get("type")), str(msg.get("type")))
        sender = msg.get("sender", "?")
        text = str(msg.get("text", ""))
        prefix = f"[{label}] {sender}: "
        with self._lock:
            if "\n" in text:
                print(prefix.rstrip(), flush=True)
                for line in text.splitlines():
                    print(f"  {line}", flush=True)
            else:
                print(f"{prefix}{text}", flush=True)

    def _messages_url(self) -> str:
        room = quote(self.room, safe="")
        return f"{self.relay}/api/rooms/{room}/messages"


def _poll_loop(bus: Bus) -> None:
    after = 0
    while True:
        try:
            messages = bus.fetch_after(after)
            for msg in messages:
                after = max(after, int(msg.get("id", after)))
                if msg.get("sender") == bus.name:
                    continue
                bus.display(msg)
                for plugin in bus.plugins:
                    plugin.on_message(msg)
            time.sleep(POLL_INTERVAL if not messages else 0.05)
        except Exception as exc:
            bus.log(f"拉取异常: {exc}")
            time.sleep(POLL_INTERVAL)


def _is_retryable(exc: httpx.HTTPError) -> bool:
    if isinstance(exc, httpx.RequestError):
        return True
    response = getattr(exc, "response", None)
    return response is not None and response.status_code in RETRYABLE_STATUS


def _short_http_error(exc: httpx.HTTPError) -> str:
    response = getattr(exc, "response", None)
    if response is not None:
        return f"{response.status_code} {response.request.url}"
    return str(exc)


def main() -> None:
    parser = argparse.ArgumentParser(description="终端聊天与剪贴板发送")
    parser.add_argument("--cheat", required=True, help="中继地址，例如 http://127.0.0.1:8000")
    parser.add_argument("--room", required=True, help="房间口令")
    parser.add_argument("--name", required=True, help="显示名")
    args = parser.parse_args()

    bus = Bus(args.cheat, args.room, args.name)
    for plugin_cls in ENABLED:
        plugin = plugin_cls()
        plugin.start(bus)
        bus.plugins.append(plugin)

    threading.Thread(target=_poll_loop, args=(bus,), daemon=True).start()
    print(
        f"已连接 {bus.relay} 房间 {bus.room}。输入文字回车发送；"
        "复制文本会自动发给对方。Ctrl+C 退出。",
        flush=True,
    )

    while True:
        try:
            line = input()
        except (EOFError, KeyboardInterrupt):
            print(flush=True)
            break
        text = line.strip()
        if not text:
            continue
        if bus.send("chat", text):
            bus.display({"type": "chat", "sender": bus.name, "text": text})


if __name__ == "__main__":
    main()
