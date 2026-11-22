# Webcam TRNG File Encryption — Linux

A Python physics-project prototype that derives **AES-256 keys and encryption nonces from webcam pixel measurements**. A Logitech C170 camera is placed in a dark box to capture small changes in sensor output. The program hashes grayscale measurements with SHA-256 and uses AES-256-GCM to encrypt and decrypt files.

> [!IMPORTANT]
> **Experimental prototype:** Webcam measurements have not been independently tested or certified as a cryptographic entropy source. SHA-256 mixes the measurements but does not create entropy. Do not rely on this project to protect important or sensitive files.

## Requirements

- Linux with a graphical desktop and a working Logitech Webcam C170.
- Camera device: **`/dev/video2`**, accessed through OpenCV's **V4L2** backend. This path is intentionally fixed in `trng.py`.
- Python 3 and a working `pip` installation.
- Python packages in `requirements.txt`:
  - `opencv-python>=4.8` — camera access, frame capture, grayscale conversion, and preview window.
  - `cryptography>=41` — authenticated AES-256-GCM encryption and decryption.
- Built-in Python modules (no separate installation): `hashlib`, `time`, `os`, `datetime`, `pathlib`, and `ast`.

## Installation and launch

From a terminal in the extracted project directory:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

If your installation uses `python3` rather than `python`, replace the commands accordingly. A virtual environment avoids modifying distribution-managed Python packages.

**Start the program from the project directory.** `main.py` creates and uses `input/`, `output/`, and `key/` relative to the current working directory, not relative to the script's location.

## Project layout

```text
webcam_trng_linux/
├── main.py             # Menu, file selection, key management, session counters
├── trng.py             # Camera capture, SHA-256 extraction, key generation
├── encrypt.py          # AES-256-GCM and decrypted-text preview extensions
├── requirements.txt    # Third-party Python dependencies
├── README.md
├── input/              # Source files and generated .enc files
├── output/             # Successfully decrypted files
└── key/                # Active dated binary key file
```

The three folders are created automatically if absent. Place the files you want to encrypt directly inside `input/`; subfolders are not searched. The menu lists eligible files by number, so you do not need to type filenames.

## Menu

```text
=== Webcam TRNG File Encryption ===

1. Encrypt file
2. Decrypt file
3. New key                  (Key: Missing)
4. Exit
-------------------------------------------
Created: —
Directories: input/ | output/ | key/
```

When a key exists, the menu shows `Key: Present`, its filename, and its creation date taken from the filename. **No key is created automatically on first run.** Choose `3. New key` when ready.

After each operation, press Enter to clear the terminal and return to the menu. Option `4` clears the terminal and displays session statistics.

## Workflow

### 1. Generate a key

Choose **3. New key**. The program opens `/dev/video2`, stabilizes for **5 seconds**, and then collects grayscale frames for **10 seconds** (15 seconds of nominal capture time in total, excluding camera opening and cleanup). `trng.py` processes the frames into a SHA-256 digest and converts its 256-bit value to a **32-byte key**. It is written as raw binary to `key/key_DDMMYYYY`, for example `key/key_22112026`.

The key is restricted to owner read/write permissions (`0600`) on Linux. Creating a new key immediately replaces the active one, deletes other matching dated key files in `key/`, and asks for **no confirmation**. Creating another key on the same day overwrites the same filename. **Keep a separate secure copy of any old key needed to decrypt older files.** The date in the filename is a label, not a unique cryptographic key identifier.

### 2. Encrypt a file

Choose **1. Encrypt file**, then select a numbered plaintext file from `input/`. The program requires an existing key. It starts a **new** webcam capture: **3 seconds** for stabilization and **3 seconds** of collection (6 seconds total, excluding opening and cleanup).

The SHA-256 result provides the first **12 bytes (96 bits)** of a nonce. The program encrypts the file with **AES-256-GCM** and saves `input/original.ext.enc`. If that destination exists, it reports that the file is already encrypted rather than overwriting it. A new capture is performed for each successful encryption attempt that reaches nonce generation.

### 3. Decrypt a file

Choose **2. Decrypt file** and select a numbered `.enc` file from `input/`. The program uses the saved key and nonce; **it does not open the webcam for decryption**. It removes the final `.enc` extension and writes the result to `output/original.ext`.

If the destination already exists, the program prints **Already done** and does not overwrite it. If the key is wrong or the encrypted data has been altered, AES-GCM authentication fails and no decrypted output is written.

After successful decryption, recognized text files can be displayed directly in the terminal. The prompt appears only when the restored extension is in the global `READABLE_EXTENSIONS` set in `encrypt.py`. Examples include `.txt`, `.md`, `.csv`, `.tsv`, `.json`, `.yaml`, `.xml`, `.html`, `.css`, `.js`, `.py`, `.c`, `.cpp`, `.sh`, `.sql`, `.log`, `.ini`, and `.toml`. The preview decodes as UTF-8, replacing invalid characters; it does not render PDFs, images, or binary formats.

### 4. Exit and view session statistics

Choose **4. Exit**. The program clears the screen and prints the counts for **keys generated**, **nonces generated**, **encryptions performed**, and **decryptions performed**. Counters exist only in `main.py` memory and **reset to zero each time the program starts**. Encryption/decryption counts increase on success; the nonce count increases after nonce generation, even if a later encryption step fails.

## Modules and data flow

| Module | Main responsibilities |
|---|---|
| `main.py` | Menu, numbered file selection, folder creation, dated-key loading/saving, and session counts |
| `trng.py` | `canalyse()` yields grayscale frame bytes; `trng()` hashes them into a 256-bit integer; `keygen()` converts that integer into a 32-byte key |
| `encrypt.py` | `encrypt_file()` and `decrypt_file()` perform authenticated AES-256-GCM operations; `READABLE_EXTENSIONS` determines text-preview eligibility |

The camera processes **every pixel in every captured frame**. OpenCV converts each full frame to grayscale, and `gray.tobytes()` supplies its pixel intensities. SHA-256 is updated **one frame at a time**, so the program does not need to retain the complete recording in memory. No special pixel coordinates or regions are configured.

The `.enc` file is a UTF-8 text representation of a two-element Python list:

```python
["nonce_hex", "ciphertext_and_authentication_tag_hex"]
```

The nonce and ciphertext are separate elements, not concatenated binary fields. Decryption parses this format with **`ast.literal_eval()`**, not unsafe `eval()`. AES-GCM stores its authentication tag with the ciphertext. **Older `.enc` files from the previous binary nonce-prefix format are not compatible with this version.**

## Notes and limitations

- This is a **physics demonstration of sensor-derived randomness**, not a validated TRNG or certified cryptographic key generator. Longer sampling does not establish a known number of entropy bits.
- AES-GCM requires a **unique nonce for each encryption under the same key**. This prototype does not formally establish nonce uniqueness; hash output alone cannot guarantee it.
- Losing or replacing the key means previous encrypted files cannot be decrypted without a saved copy of the original key.
- OpenCV requires graphical-window support for the webcam preview. Camera windows are released and closed after capture, including on errors.
- If `/dev/video2` is unavailable or inaccessible, capture fails. Check the device and permissions, but keep the configured webcam name unchanged for this Linux setup.
- This is directory-based file organization, **not Docker or Podman containerization**.
