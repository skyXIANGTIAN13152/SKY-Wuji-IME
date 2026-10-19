#!/usr/bin/env python3
"""Compile and run the pure JVM upgrade-policy check using Gradle's bundled Kotlin compiler."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--gradle-lib', type=Path, help='Gradle distribution lib/ directory')
args = parser.parse_args()
gradle_lib = args.gradle_lib
if gradle_lib is None:
    gradle_cache = Path(os.environ.get('GRADLE_USER_HOME', Path.home() / '.gradle'))
    compilers = sorted((gradle_cache / 'wrapper/dists').glob('**/lib/kotlin-compiler-embeddable-*.jar'))
    if not compilers:
        raise SystemExit('Run ./gradlew --version first, or specify --gradle-lib')
    gradle_lib = compilers[-1].parent
stdlib = next(gradle_lib.glob('kotlin-stdlib-*.jar'))
java_home = os.environ.get('JAVA_HOME')
java = str(Path(java_home) / 'bin/java') if java_home else 'java'
work = ROOT / 'build/user-data-upgrade-check'
work.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory(dir=work) as temporary:
    classes = Path(temporary) / 'classes'
    subprocess.run([
        java, '-cp', str(gradle_lib / '*'), 'org.jetbrains.kotlin.cli.jvm.K2JVMCompiler',
        '-no-stdlib', '-no-reflect', '-jvm-target', '11', '-classpath', str(stdlib), '-d', str(classes),
        str(ROOT / 'app/src/main/java/com/osfans/trime/data/base/BundledUserDataPolicy.kt'),
        str(ROOT / 'script/UserDataUpgradeCheck.kt'),
    ], check=True)
    subprocess.run([
        java, '-cp', os.pathsep.join([str(classes), str(stdlib)]),
        'UserDataUpgradeCheckKt', temporary,
    ], check=True)
