#!/usr/bin/env python
"""Fetch the official Mpipi supporting code from Figshare and verify its MD5."""

from __future__ import annotations

import hashlib
import urllib.request
import zipfile
from pathlib import Path

URL = "https://ndownloader.figshare.com/files/31037434"
EXPECTED_MD5 = "a18b0f5e30f15f8b5daf7b66210b663e"


def md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    destination = Path(__file__).resolve().parents[1] / "third_party" / "downloads" / "mpipi"
    destination.mkdir(parents=True, exist_ok=True)
    archive = destination / "supporting-code.zip"
    if not archive.exists():
        urllib.request.urlretrieve(URL, archive)
    actual = md5(archive)
    if actual != EXPECTED_MD5:
        raise RuntimeError(f"checksum mismatch: expected {EXPECTED_MD5}, got {actual}")
    extract_to = destination / "supporting-code"
    with zipfile.ZipFile(archive) as source:
        source.extractall(extract_to)
    print(f"Verified and extracted Mpipi supporting code to {extract_to}")


if __name__ == "__main__":
    main()
