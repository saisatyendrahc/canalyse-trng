"""Menu for webcam-derived AES keys and encrypted files in local folders."""

import os
from datetime import date, datetime
from pathlib import Path

from encrypt import READABLE_EXTENSIONS, decrypt_file, encrypt_file
from trng import canalyse, keygen, trng


ROOT = Path.cwd()
INPUT_DIR = ROOT / "input"
OUTPUT_DIR = ROOT / "output"
KEY_DIR = ROOT / "key"

KEY_STABILIZE, KEY_COLLECT = 5, 10    # Total: 15 seconds
NONCE_STABILIZE, NONCE_COLLECT = 3, 3  # Total: 6 seconds


def active_key():
    """Find the most recently saved key_ DDMMYYYY file, if one exists."""
    keys = [
        path for path in KEY_DIR.glob("key_????????")
        if path.is_file() and not path.is_symlink() and path.name[4:].isdigit()
    ]
    return max(keys, key=lambda path: path.stat().st_mtime_ns, default=None)


def load_key():
    path = active_key()
    if path is None:
        raise FileNotFoundError("Key missing. Select 'New key' first.")
    key = path.read_bytes()
    if len(key) != 32:
        raise ValueError(f"Invalid key file: {path.name} (expected 32 bytes).")
    return key


def new_key():
    """Replace the existing key immediately, without any confirmation prompt."""
    key = keygen(trng(canalyse(KEY_STABILIZE, KEY_COLLECT)))
    path = KEY_DIR / f"key_{date.today():%d%m%Y}"
    path.write_bytes(key)
    # POSIX-only: Windows file permissions are controlled by NTFS ACLs.
    if os.name != "nt":
        path.chmod(0o600)
    for previous in KEY_DIR.glob("key_????????"):
        if previous != path and previous.is_file() and previous.name[4:].isdigit():
            previous.unlink()
    print(f"New AES-256 key saved: key/{path.name}")


def choose_file(encrypted):
    """Show only eligible files directly inside input/ and return the chosen path."""
    files = sorted(
        (path for path in INPUT_DIR.iterdir()
         if path.is_file() and not path.is_symlink()
         and path.name.endswith(".enc") == encrypted),
        key=lambda path: path.name.casefold(),
    )
    if not files:
        print("No encrypted files in input/." if encrypted
              else "No files available to encrypt in input/.")
        return None

    print("\nFiles in input/:")
    for number, path in enumerate(files, start=1):
        print(f"  {number}. {path.name}")
    print("  0. Back")

    try:
        number = int(input("Select file number: ").strip())
    except ValueError:
        print("Invalid selection.")
        return None

    if number == 0:
        return None
    if not 1 <= number <= len(files):
        print("Invalid selection.")
        return None
    return files[number - 1]


def encrypt_option(stats):
    key = load_key()
    source = choose_file(encrypted=False)
    if source is None:
        return

    target = INPUT_DIR / (source.name + ".enc")
    if target.exists() or target.is_symlink():
        print(f"Already encrypted: input/{target.name}")
        return

    nonce = trng(canalyse(NONCE_STABILIZE, NONCE_COLLECT)).to_bytes(32, "big")[:12]
    stats["nonces_generated"] += 1
    encrypt_file(source, target, key, nonce)
    stats["encryptions_performed"] += 1
    print(f"Encrypted: input/{target.name}")
    print(f"Nonce (hex): {nonce.hex()}")


def decrypt_option(stats):
    key = load_key()
    source = choose_file(encrypted=True)
    if source is None:
        return

    target = OUTPUT_DIR / source.name[:-4]  # Remove only the final '.enc'.
    if target.exists() or target.is_symlink():
        print(f"Already done: output/{target.name} exists.")
        return

    decrypt_file(source, target, key)
    stats["decryptions_performed"] += 1
    print(f"Decrypted: output/{target.name}")

    if target.suffix.lower() in READABLE_EXTENSIONS:
        if input("Read decrypted file here? (y/n): ").strip().lower() == "y":
            print(f"\n--- {target.name} ---")
            print(target.read_text(encoding="utf-8", errors="replace"))
            print(f"--- End of {target.name} ---")


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def main():
    stats = {
        "keys_generated": 0,
        "nonces_generated": 0,
        "encryptions_performed": 0,
        "decryptions_performed": 0,
    }
    for directory in (INPUT_DIR, OUTPUT_DIR, KEY_DIR):
        directory.mkdir(exist_ok=True)

    while True:
        clear_screen()
        path = active_key()
        print("=== Webcam TRNG File Encryption ===\n")
        print("1. Encrypt file")
        print("2. Decrypt file")
        print(f"3. New key                  (Key: {'Present' if path else 'Missing'})")
        print("4. Exit")
        print("-" * 43)
        if path:
            print(f"Active key: {path.name}")
            try:
                print(f"Created: {datetime.strptime(path.name[4:], '%d%m%Y'):%d/%m/%Y}")
            except ValueError:
                print("Created: Unknown")
        else:
            print("Created: —")
        print("Directories: input/ | output/ | key/\n")

        choice = input("Enter option: ").strip()
        if choice == "4":
            break

        try:
            if choice == "1":
                encrypt_option(stats)
            elif choice == "2":
                decrypt_option(stats)
            elif choice == "3":
                new_key()
                stats["keys_generated"] += 1
            else:
                print("Invalid option.")
        except Exception as error:
            print(f"Operation failed: {error}")

        input("\nPress Enter to continue...")

    clear_screen()
    print("=== Webcam TRNG File Encryption ===\n")
    print("Session statistics:")
    print(f"Keys generated:        {stats['keys_generated']}")
    print(f"Nonces generated:      {stats['nonces_generated']}")
    print(f"Encryptions performed: {stats['encryptions_performed']}")
    print(f"Decryptions performed: {stats['decryptions_performed']}")
    print("\nSession ended.")


if __name__ == "__main__":
    main()
