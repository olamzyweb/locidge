from __future__ import annotations

import argparse
import base64
import os
import socket
import sys
import threading
import time
import webbrowser
from datetime import datetime
from io import BytesIO
from pathlib import Path
from urllib.parse import quote

import qrcode
from flask import Flask, jsonify, render_template, request, send_from_directory
from werkzeug.utils import secure_filename


if getattr(sys, "frozen", False):
    APP_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    DATA_DIR = Path(sys.executable).resolve().parent
else:
    APP_DIR = Path(__file__).resolve().parent
    DATA_DIR = APP_DIR

TEMPLATES_DIR = APP_DIR / "templates"
UPLOAD_FOLDER = DATA_DIR / "uploads"
HOST_DEFAULT = "0.0.0.0"
PORT_DEFAULT = 5000
HOST = HOST_DEFAULT
PORT = PORT_DEFAULT
RETENTION_MINUTES = 30
CLEANUP_INTERVAL_SECONDS = 5 * 60
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"}


app = Flask(__name__, template_folder=str(TEMPLATES_DIR))
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
ensure_upload_dir_ran = False


def has_console_output() -> bool:
    stream = getattr(sys, "stdout", None)
    return stream is not None and hasattr(stream, "write")


def safe_print(*args, **kwargs) -> None:
    if has_console_output():
        print(*args, **kwargs)


def ensure_upload_dir() -> None:
    global ensure_upload_dir_ran
    if not ensure_upload_dir_ran:
        UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        ensure_upload_dir_ran = True


def log_transfer(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    safe_print(f"[{timestamp}] {message}")


def get_local_ip() -> str:
    """Detect the active LAN IP without requiring internet access."""
    ip_address = "127.0.0.1"
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("10.255.255.255", 1))
        ip_address = sock.getsockname()[0]
    except OSError:
        try:
            ip_address = socket.gethostbyname(socket.gethostname())
        except OSError:
            ip_address = "127.0.0.1"
    finally:
        sock.close()
    return ip_address


def generate_qr_data_uri(url: str) -> str:
    qr_image = qrcode.make(url)
    buffer = BytesIO()
    qr_image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def print_ascii_qr(url: str) -> None:
    if not has_console_output():
        return
    qr = qrcode.QRCode(border=1)
    qr.add_data(url)
    qr.make(fit=True)
    qr.print_ascii(out=sys.stdout, invert=True)


def format_size(size_in_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_in_bytes)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size_in_bytes} B"


def is_previewable_image(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTENSIONS


def build_file_info(path: Path) -> dict[str, object]:
    stat = path.stat()
    return {
        "name": path.name,
        "size": stat.st_size,
        "url_name": quote(path.name),
        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
        "preview_url": f"/file/{quote(path.name)}",
        "is_previewable": is_previewable_image(path),
        "extension": path.suffix.lower().lstrip(".") or "file",
    }


def cleanup_expired_files() -> int:
    ensure_upload_dir()
    removed_count = 0
    now = time.time()
    retention_seconds = RETENTION_MINUTES * 60

    for path in UPLOAD_FOLDER.iterdir():
        if not path.is_file():
            continue

        try:
            age_seconds = now - path.stat().st_mtime
        except OSError as exc:
            log_transfer(f"CLEANUP skipped {path.name}: {exc}")
            continue

        if age_seconds < retention_seconds:
            continue

        try:
            size_human = format_size(path.stat().st_size)
            path.unlink()
            removed_count += 1
            log_transfer(
                f"CLEANUP removed {path.name} ({size_human}) after {RETENTION_MINUTES} minutes"
            )
        except OSError as exc:
            log_transfer(f"CLEANUP failed for {path.name}: {exc}")

    return removed_count


def start_cleanup_worker() -> threading.Thread:
    def cleanup_loop() -> None:
        while True:
            time.sleep(CLEANUP_INTERVAL_SECONDS)
            cleanup_expired_files()

    worker = threading.Thread(target=cleanup_loop, daemon=True, name="cleanup-worker")
    worker.start()
    return worker


def get_shared_files() -> list[dict[str, object]]:
    ensure_upload_dir()
    files = []
    for path in sorted(UPLOAD_FOLDER.iterdir(), key=lambda item: item.name.lower()):
        if path.is_file():
            files.append(build_file_info(path))
    return files


def print_terminal_banner(local_url: str, lan_url: str) -> None:
    if not has_console_output():
        return
    divider = "=" * 72
    safe_print(divider)
    safe_print("Locidge")
    safe_print(divider)
    safe_print(f"Laptop page    : {local_url}")
    safe_print(f"Mobile page    : {lan_url}")
    safe_print(f"Upload folder  : {UPLOAD_FOLDER}")
    safe_print(f"Auto-delete    : Files older than {RETENTION_MINUTES} minutes")
    safe_print("")
    safe_print("Scan the QR code below from the browser page or open the LAN URL directly.")
    safe_print("")
    print_ascii_qr(lan_url)
    safe_print("")
    safe_print("Keep this window open while transferring files.")
    safe_print(divider)


def maybe_open_browser() -> None:
    try:
        webbrowser.open(f"http://localhost:{PORT}", new=1)
    except Exception as exc:  # pragma: no cover
        log_transfer(f"Could not auto-open browser: {exc}")


def parse_runtime_settings() -> tuple[str, int]:
    parser = argparse.ArgumentParser(description="Start the Locidge transfer server")
    parser.add_argument(
        "--host",
        default=os.getenv("LOCIDGE_HOST", HOST_DEFAULT),
        help=f"Host/IP to bind (default: LOCIDGE_HOST or {HOST_DEFAULT})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("LOCIDGE_PORT", str(PORT_DEFAULT))),
        help=f"Port to bind (default: LOCIDGE_PORT or {PORT_DEFAULT})",
    )
    args = parser.parse_args()

    if not (1 <= args.port <= 65535):
        parser.error("--port must be between 1 and 65535")

    return args.host, args.port


@app.route("/")
def index():
    local_ip = get_local_ip()
    lan_url = f"http://{local_ip}:{PORT}"
    files = get_shared_files()
    return render_template(
        "index.html",
        local_url=f"http://localhost:{PORT}",
        lan_url=lan_url,
        qr_code=generate_qr_data_uri(lan_url),
        files=files,
        file_count=len(files),
        uploads_path=str(UPLOAD_FOLDER),
        format_size=format_size,
    )


@app.route("/api/files")
def api_files():
    files = get_shared_files()
    return jsonify(
        {
            "files": [
                {
                    **file_info,
                    "size_human": format_size(int(file_info["size"])),
                }
                for file_info in files
            ]
        }
    )


@app.route("/upload", methods=["POST"])
def upload_file():
    ensure_upload_dir()
    incoming_files = request.files.getlist("files")
    if not incoming_files or all(file.filename == "" for file in incoming_files):
        return jsonify({"ok": False, "error": "No files selected."}), 400

    saved_files = []
    for file_storage in incoming_files:
        if not file_storage or file_storage.filename == "":
            continue

        filename = secure_filename(file_storage.filename)
        if not filename:
            continue

        destination = UPLOAD_FOLDER / filename
        if destination.exists():
            stem = destination.stem
            suffix = destination.suffix
            counter = 1
            while destination.exists():
                destination = UPLOAD_FOLDER / f"{stem}-{counter}{suffix}"
                counter += 1

        file_storage.save(destination)
        file_stat = destination.stat()
        remote_addr = request.headers.get("X-Forwarded-For", request.remote_addr)
        log_transfer(
            f"UPLOAD from {remote_addr or 'unknown'} -> {destination.name} ({format_size(file_stat.st_size)})"
        )
        saved_file = build_file_info(destination)
        saved_file["size_human"] = format_size(file_stat.st_size)
        saved_files.append(saved_file)

    if not saved_files:
        return jsonify({"ok": False, "error": "No valid files were uploaded."}), 400

    return jsonify({"ok": True, "files": saved_files})


@app.route("/file/<path:filename>")
def serve_file_inline(filename: str):
    ensure_upload_dir()
    safe_name = Path(filename).name
    return send_from_directory(app.config["UPLOAD_FOLDER"], safe_name, as_attachment=False)


@app.route("/download/<path:filename>")
def download_file(filename: str):
    ensure_upload_dir()
    safe_name = Path(filename).name
    file_path = UPLOAD_FOLDER / safe_name
    if file_path.exists() and file_path.is_file():
        remote_addr = request.headers.get("X-Forwarded-For", request.remote_addr)
        log_transfer(
            f"DOWNLOAD to {remote_addr or 'unknown'} <- {safe_name} ({format_size(file_path.stat().st_size)})"
        )
    return send_from_directory(app.config["UPLOAD_FOLDER"], safe_name, as_attachment=True)


def main() -> None:
    global HOST, PORT
    HOST, PORT = parse_runtime_settings()

    ensure_upload_dir()
    cleanup_expired_files()
    start_cleanup_worker()

    local_ip = get_local_ip()
    local_url = f"http://localhost:{PORT}"
    lan_url = f"http://{local_ip}:{PORT}"

    print_terminal_banner(local_url, lan_url)
    threading.Timer(1.0, maybe_open_browser).start()

    try:
        app.run(host=HOST, port=PORT, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\nShutting down.")
        sys.exit(0)


if __name__ == "__main__":
    main()
