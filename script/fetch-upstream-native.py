#!/usr/bin/env python3
"""Reuse the unchanged JNI libraries from the exact upstream source revision.

Delete app/prebuilt and run make release to compile these libraries from the
pinned, recursively checked-out submodules instead.
"""
from pathlib import Path
import hashlib
import io
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ASSETS = {
    'arm64-v8a': 'c727d509cbae8ba6a6b3616f57ea299d46bb13072812342811d03aea0bc3cb98',
    'armeabi-v7a': '3fb58040fe7bc985d7241270196aa4de4c619481925f90cc449b2724d8101e57',
}
for abi, expected in ASSETS.items():
    name = f'com.osfans.trime-v3.3.12-0-ge09ac711-{abi}-release.apk'
    url = f'https://github.com/osfans/trime/releases/download/v3.3.12/{name}'
    with urllib.request.urlopen(url, timeout=120) as response:
        data = response.read()
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected:
        raise SystemExit(f'Upstream APK checksum mismatch for {abi}')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        members = [x for x in archive.namelist() if x.startswith(f'lib/{abi}/') and x.endswith('.so')]
        if not members:
            raise SystemExit(f'No native libraries in verified {abi} APK')
        for member in members:
            destination = ROOT / 'app/prebuilt' / abi / Path(member).name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(archive.read(member))
    print(f'Verified {abi}: {len(members)} native libraries from upstream Trime 3.3.12')
