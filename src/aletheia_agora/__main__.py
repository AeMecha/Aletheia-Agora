"""Start a single-user server and open its browser interface."""
import argparse
import os
import threading
import webbrowser
from pathlib import Path

import uvicorn
from .server import create_app


def main():
    parser = argparse.ArgumentParser(description="Aletheia Agora: your archive in a browser")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--home", type=Path)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    if args.host not in ("127.0.0.1", "localhost", "::1") and not os.environ.get("ALETHEIA_ACCESS_TOKEN"):
        parser.error("Set ALETHEIA_ACCESS_TOKEN before binding a non-loopback interface.")
    app = create_app(args.home)
    host = "127.0.0.1" if args.host in ("0.0.0.0", "::") else args.host
    if ":" in host:
        host = "[" + host + "]"
    url = f"http://{host}:{args.port}/#token={app.state.access_token}"
    print("Aletheia Agora browser address (keep the access token private):\n" + url)
    if not args.no_browser:
        timer = threading.Timer(1.0, webbrowser.open, args=(url,))
        timer.daemon = True
        timer.start()
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
