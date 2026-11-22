"""AES-256-GCM file encryption with a separate nonce and ciphertext list."""

from ast import literal_eval

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


READABLE_EXTENSIONS = {
    ".txt", ".md", ".csv", ".tsv", ".json", ".jsonl", ".yaml", ".yml",
    ".xml", ".html", ".htm", ".css", ".js", ".jsx", ".ts", ".tsx",
    ".py", ".c", ".h", ".cpp", ".hpp", ".java", ".rs", ".go",
    ".sh", ".bash", ".zsh", ".toml", ".ini", ".cfg", ".conf",
    ".log", ".sql", ".svg", ".tex", ".rst", ".properties",
    ".ipynb", ".bat", ".ps1", ".diff", ".patch",
}


def encrypt_file(source, target, key, nonce):
    """Write [nonce_hex, ciphertext_and_tag_hex] to a .enc text file."""
    plaintext = source.read_bytes()
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, None)
    target.write_text(repr([nonce.hex(), ciphertext.hex()]), encoding="utf-8")


def decrypt_file(source, target, key):
    """Safely parse the two-element list and restore the verified plaintext."""
    values = literal_eval(source.read_text(encoding="utf-8"))
    if (not isinstance(values, list) or len(values) != 2
            or not all(isinstance(value, str) for value in values)):
        raise ValueError("Expected [nonce_hex, ciphertext_hex] in the .enc file.")

    nonce, ciphertext = (bytes.fromhex(value) for value in values)
    if len(nonce) != 12:
        raise ValueError("Invalid nonce: expected 12 bytes.")

    try:
        plaintext = AESGCM(key).decrypt(nonce, ciphertext, None)
    except InvalidTag as error:
        raise ValueError("Wrong key or modified encrypted file.") from error
    target.write_bytes(plaintext)
