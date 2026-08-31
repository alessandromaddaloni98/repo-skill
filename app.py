"""Startup entrypoint: python app.py"""
import os
import socket

from app import create_app

app = create_app()


def _lan_ip() -> str:
    """IP of the interface used for the local network (to print the URL for phones)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))   # no real traffic, only used to pick the interface
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


if __name__ == "__main__":
    # 0.0.0.0 = reachable from other devices on the same network (phone, other computers).
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8515"))
    if host == "0.0.0.0":
        print(f" * From this machine: http://127.0.0.1:{port}")
        print(f" * From phone/LAN:    http://{_lan_ip()}:{port}")
    app.run(host=host, port=port, debug=True)
