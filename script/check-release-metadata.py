#!/usr/bin/env python3
"""Validate release identity and the narrow voice-IME visibility declaration."""
import argparse
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = 'io.github.skyxiangtian13152.skywuji'
SIGNER_SHA256 = 'a1b0fc701a23aa028167d9e0fd4de87ca0a848ae46edfa3b6a6ca11d36af688a'
ANDROID = '{http://schemas.android.com/apk/res/android}'
VOICE_ACTION = 'android.view.InputMethod'
ALL_PACKAGES = 'android.permission.QUERY_ALL_PACKAGES'


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def source_metadata():
    gradle = (ROOT / 'app/build.gradle.kts').read_text(encoding='utf-8')
    package = re.search(r'^\s*applicationId = "([^"]+)"', gradle, re.M).group(1)
    version = re.search(r'^\s*versionName = "([^"]+)"', gradle, re.M).group(1)
    code = re.search(r'^\s*versionCode = (\d+)\s*$', gradle, re.M).group(1)
    require(package == PACKAGE, 'Unexpected source application ID')
    require(re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.-]+)?', version),
            'Version must be safe for release filenames and build environment')
    manifest = ET.parse(ROOT / 'app/src/main/AndroidManifest.xml').getroot()
    require(any(action.get(ANDROID + 'name') == VOICE_ACTION
                for action in manifest.findall('./queries/intent/action')),
            'Source manifest must declare queries/intent/action for voice IMEs')
    require(not any(p.get(ANDROID + 'name') == ALL_PACKAGES
                    for p in manifest.findall('./uses-permission')),
            'Use the narrow input-method query, not QUERY_ALL_PACKAGES')
    return version, code


def has_voice_query(xmltree):
    """Inspect element ancestry so a service intent-filter cannot pass this check."""
    ancestors = []
    for line in xmltree.splitlines():
        element = re.match(r'^(\s*)E: ([^ ]+)', line)
        if element:
            indent = len(element.group(1))
            while ancestors and ancestors[-1][0] >= indent:
                ancestors.pop()
            ancestors.append((indent, element.group(2)))
        elif [name for _, name in ancestors] == ['manifest', 'queries', 'intent', 'action']:
            if re.search(r'A: android:name\([^)]*\)="android\.view\.InputMethod"', line):
                return True
    return False


def validate_apk(apk, version, code, aapt, apksigner):
    badging = subprocess.check_output([aapt, 'dump', 'badging', str(apk)], text=True, encoding='utf-8')
    package_line = re.search(r'^package: (.+)$', badging, re.M)
    require(package_line is not None, 'APK has no package metadata')
    fields = dict(re.findall(r"([A-Za-z]+)='([^']*)'", package_line.group(1)))
    require(fields.get('name') == PACKAGE, 'APK package does not match source')
    require(fields.get('versionName') == version, 'APK version name does not match source')
    require(fields.get('versionCode') == code, 'APK version code does not match source')
    tree = subprocess.check_output([aapt, 'dump', 'xmltree', str(apk), 'AndroidManifest.xml'], text=True, encoding='utf-8')
    require(has_voice_query(tree), 'APK is missing the input-method visibility query')
    require(ALL_PACKAGES not in tree, 'APK unexpectedly requests QUERY_ALL_PACKAGES')
    signature = subprocess.check_output([apksigner, 'verify', '--verbose', '--print-certs', str(apk)], text=True, encoding='utf-8')
    signers = re.findall(r'^Signer #\d+ certificate SHA-256 digest: ([a-fA-F0-9]+)$', signature, re.M)
    require([s.lower() for s in signers] == [SIGNER_SHA256], 'APK does not use the existing project signer')
    print(f'APK verified: {apk.name}')
    print(f'Signer SHA-256: {SIGNER_SHA256}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('apk', nargs='?', type=Path)
    parser.add_argument('--aapt', default='aapt')
    parser.add_argument('--apksigner', default='apksigner')
    parser.add_argument('--github-env', type=Path)
    args = parser.parse_args()
    version, code = source_metadata()
    if args.apk:
        validate_apk(args.apk, version, code, args.aapt, args.apksigner)
    if args.github_env:
        with args.github_env.open('a', encoding='utf-8') as output:
            output.write(f'BUILD_VERSION_NAME={version}\n')
    print(f'Package: {PACKAGE}; version: {version}; code: {code}')
    print('Input-method visibility query verified; QUERY_ALL_PACKAGES absent.')


if __name__ == '__main__':
    main()
