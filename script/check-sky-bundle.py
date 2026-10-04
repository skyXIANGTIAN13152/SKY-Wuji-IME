#!/usr/bin/env python3
"""Check release payload completeness and exclusion of personal device data."""
from pathlib import Path
import hashlib
import json
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RIME = ROOT / 'app/src/main/assets/rime'
manifest = json.loads((ROOT / 'docs/BUNDLED_FILES.json').read_text(encoding='utf-8'))
expected = manifest['files']
actual = {str(p.relative_to(RIME)).replace('\\', '/'): p for p in RIME.rglob('*') if p.is_file()}
assert set(actual) == set(expected), 'Unexpected or missing bundled file'
for name, path in actual.items():
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected[name], name
    assert not any(x in name.lower() for x in ['.userdb', 'installation.yaml', 'user.yaml', 'sync/', '.p12', '.keystore']), name

patch = (RIME / 'tongwenfeng.trime.custom.yaml').read_text(encoding='utf-8')
assert 'label: 请先安装并启用“说点啥”' in patch
assert 'label: 当前使用本地语音模型' not in patch
assert 'preset_keys/hide_key_symbol: null' in patch
assert 'preset_keys/hide_key_hint: null' in patch
assert 'select: sky_help_home' in patch
for image in set(re.findall(r'cherry-v5/[a-zA-Z0-9_.-]+\.png', patch)):
    assert (RIME / 'backgrounds' / image).is_file(), image
assert hashlib.sha256((RIME / 'fonts/sky-preview-microphone-v6.ttf').read_bytes()).hexdigest() == 'c7bfa207b21ab1a3e67f820abd898ecf884e12d25f026c44603cf18984219082'
assert (RIME / 'custom_phrase.txt').read_text(encoding='utf-8').startswith('# User-defined phrases.')
assert 'schema: rime_ice' in (RIME / 'default.custom.yaml').read_text(encoding='utf-8')

for apk in map(Path, sys.argv[1:]):
    with zipfile.ZipFile(apk) as archive:
        names = archive.namelist()
        checksums = json.loads(archive.read('assets/checksums.json'))['files']
        for name, digest in expected.items():
            key = f'rime/{name}'
            assert hashlib.sha256(archive.read(f'assets/{key}')).hexdigest() == digest, name
            assert checksums[key] == digest, f'Asset sync omission: {key}'
        for abi in ['arm64-v8a', 'armeabi-v7a']:
            assert any(name.startswith(f'lib/{abi}/') and name.endswith('.so') for name in names), abi
    print(f'APK payload and automatic asset-sync manifest verified: {apk.name}')
print(f'Validated {len(expected)} bundled files; no personal device data in the payload.')
