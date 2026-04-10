# Locidge

Locidge lets you send files between your laptop and any device on the same local WiFi network, especially an iPhone, without using the internet, cables, or installing an app on the receiving device.

It runs as a lightweight Flask server on your laptop, generates a QR code for quick access, and serves a mobile-friendly page where other devices can upload files to the laptop or download files the laptop is sharing.

## Why this app exists

- Fast local transfer over WiFi
- No cloud storage or third-party services
- No app install required on the phone
- Works well for photos, videos, zip files, PDFs, and other large files
- One command to start: `python server.py`

## Requirements

- Python 3.8 or newer
- `pip`
- A laptop and phone connected to the same WiFi network or hotspot

## Project structure

```text
wifi-transfer/
+-- server.py
+-- templates/
¦   +-- index.html
+-- uploads/
+-- requirements.txt
+-- README.md
```

## Installation

1. Open a terminal in the `wifi-transfer` folder.
2. Install the required Python packages:

```bash
pip install -r requirements.txt
```

## How to run

Start the app with:

```bash
python server.py
```

When the script starts it will:

- detect your laptop's local IP address
- start a local Flask server on port `5000`
- print the local and LAN URLs in the terminal
- auto-open `http://localhost:5000` in your default browser
- show a QR code on the page for easy scanning

## How to use it from iPhone

1. Make sure your iPhone and laptop are on the same WiFi network.
2. Run `python server.py` on the laptop.
3. On the laptop browser page, scan the QR code with the iPhone camera.
4. Tap the link prompt on the iPhone.
5. The mobile page will open.
6. Use the upload section to send files to the laptop.
7. Use the shared files section to download files from the laptop.

## How uploads work

- Files uploaded from the phone are saved into the `uploads/` folder on the laptop.
- Files in `uploads/` are automatically deleted after 30 minutes to help prevent storage buildup.
- The mobile page shows an upload progress bar while the transfer is running.
- The terminal shows a transfer log for uploads, downloads, and cleanup events.

## How to share files from laptop to iPhone

Place any file you want to share into the `uploads/` folder. Keep in mind that files in this folder are automatically deleted after 30 minutes:

```text
wifi-transfer/uploads/
```

Once the file is there, it should appear on the phone automatically within a few seconds. You can still refresh manually if needed.

## Windows and macOS notes

- The app is designed to work on both Windows and macOS.
- On both systems, run it from a terminal with Python installed.
- If port `5000` is already in use, stop the conflicting app or change the port in `server.py`.

## Troubleshooting

### Phone cannot connect

- Confirm both devices are on the same network.
- Make sure the laptop is not connected to one WiFi and the phone to another.
- If using a hotspot, connect the phone to the laptop's hotspot and retry.

### Wrong IP address appears

- If your laptop has multiple network adapters, Python may detect the wrong one.
- Check the LAN URL printed in the terminal.
- If needed, temporarily disable unused adapters such as VPNs or virtual adapters and restart the app.

### Firewall blocks access

- On Windows, allow Python through Windows Defender Firewall when prompted.
- On macOS, allow incoming connections for Python if the system asks.
- If the phone cannot load the page but `localhost:5000` works on the laptop, the firewall is the first thing to check.

### QR code scans but page does not open

- Verify the QR code points to the same LAN URL shown in the terminal.
- Make sure the laptop is still running the server.
- Try typing the LAN URL manually into Safari on the iPhone.

### Large file upload seems slow

- Local transfer speed depends on the WiFi signal and router quality.
- Keep both devices near the router or hotspot source.
- Avoid switching apps or locking the phone during large uploads.

## Windows executable and installer

You can build Locidge as a standalone Windows executable and then wrap it in a normal Windows installer.

### Build the `.exe` with PyInstaller

1. Install PyInstaller:

```bash
pip install pyinstaller
```

2. From the `wifi-transfer` folder, run the included build script:

```bash
packaging\build_windows.bat
```

This creates:

```text
wifi-transfer\dist\Locidge.exe
```

Notes:

- The build uses `--windowed`, so the app launches without a visible console window.
- The included icon file `packaging\locidge.ico` is embedded into the Windows executable.
- The executable creates and uses an `uploads` folder next to the `.exe` at runtime.
- If you prefer running PyInstaller manually, the build script shows the exact command being used.

### Create a Windows installer with Inno Setup

1. Install Inno Setup.
2. Build the executable first so `dist\Locidge.exe` exists.
3. Open this script in Inno Setup:

```text
wifi-transfer\packaging\Locidge.iss
```

4. In Inno Setup, click **Build**.

This creates an installer named:

```text
wifi-transfer\packaging\Locidge-Installer.exe
```

The installer:

- installs Locidge into `Program Files`
- creates an `uploads` folder inside the install directory
- uses the included Locidge icon for the installer and shortcuts
- adds a Start Menu shortcut
- can optionally add a desktop shortcut
- can launch Locidge after installation

## Security note

This tool is designed for trusted local networks. Anyone on the same WiFi who has the QR code or LAN link can access the page and transfer files while the server is running. Files in `uploads/` are also subject to the automatic 30-minute cleanup policy.

