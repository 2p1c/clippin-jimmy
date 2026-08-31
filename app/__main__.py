import argparse
import sys

def _check_deps() -> None:
    missing: list[str] = []
    for name in ("uvicorn", "fastapi"):
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


def main() -> None:
    _check_deps()
    import uvicorn

    parser = argparse.ArgumentParser(description="HTTP 消息中继")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=False,
        timeout_keep_alive=75,
        timeout_graceful_shutdown=3,
    )


if __name__ == "__main__":
    main()
