"""
hashing.py
SHA-256 hashing for evidence integrity — the "tamper-proof seal".

Rule for the whole team: hash evidence bytes BEFORE upload, and store
that hash in EvidenceImage.file_hash (or Report.evidence_hash). Anyone
can later re-hash a downloaded file and compare to prove it wasn't
altered.
"""

import hashlib
from pathlib import Path
from typing import Union


def hash_bytes(data: bytes) -> str:
    """Return the SHA-256 hex digest of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def hash_file(path: Union[str, Path]) -> str:
    """
    Return the SHA-256 hex digest of a file on disk, reading it in
    chunks so large images/reports don't get loaded fully into memory.
    """
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def verify_bytes(data: bytes, expected_hash: str) -> bool:
    """Recompute the hash of `data` and compare against a stored hash."""
    return hash_bytes(data) == expected_hash


if __name__ == "__main__":
    # quick manual check: python hashing.py
    sample = b"hello metroscan"
    digest = hash_bytes(sample)
    print(f"hash: {digest}")
    print(f"verifies: {verify_bytes(sample, digest)}")
