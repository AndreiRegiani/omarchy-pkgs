#!/usr/bin/env python3
"""Resolve and validate the packaged Aurora config without compiling a kernel."""
import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


def check(kernel, package, output):
    output.mkdir(parents=True, exist_ok=False)
    build = output / 'build'
    build.mkdir()
    report = {'status': 'failed'}
    try:
        match = re.search(r'^_commit=([0-9a-f]{40})$',
                          (package / 'PKGBUILD').read_text(), re.MULTILINE)
        if not match:
            raise ValueError('PKGBUILD must pin a full kernel commit')
        actual = subprocess.check_output(
            ['git', '-C', str(kernel), 'rev-parse', 'HEAD'], text=True).strip()
        report['source_commit'] = actual
        if actual != match[1]:
            raise ValueError(f'Kernel checkout {actual} differs from pin {match[1]}')
        inputs = ['config', 'common.config', 'neo.config', 'validate-config.py']
        report['inputs'] = {
            name: hashlib.sha256((package / name).read_bytes()).hexdigest()
            for name in inputs}
        original = (package / 'config').read_text()
        (output / 'original.config').write_text(original)
        shutil.copyfile(package / 'config', build / '.config')
        with (output / 'configure.log').open('w') as log:
            def run(args):
                log.write('$ ' + ' '.join(map(str, args)) + '\n')
                log.flush()
                subprocess.run(list(map(str, args)), cwd=kernel,
                               stdout=log, stderr=subprocess.STDOUT, check=True)

            run([kernel / 'scripts/kconfig/merge_config.sh', '-m', '-O', build,
                 build / '.config', package / 'common.config', package / 'neo.config'])
            run([kernel / 'scripts/config', '--file', build / '.config',
                 '--disable', 'LOCALVERSION_AUTO'])
            shutil.copyfile(build / '.config', output / 'requested.config')
            run(['make', 'O=' + str(build), 'ARCH=arm64',
                 'LLVM=' + os.environ.get('LLVM', '1'),
                 'BINDGEN=' + os.environ.get('BINDGEN', 'bindgen'),
                 'LOCALVERSION=', 'olddefconfig'])
            shutil.copyfile(build / '.config', output / 'resolved.config')
            resolved = (output / 'resolved.config').read_text()
            (output / 'config.diff').write_text(''.join(difflib.unified_diff(
                original.splitlines(keepends=True), resolved.splitlines(keepends=True),
                fromfile='packaged/config', tofile='resolved.config')))
            for fragment in ('common.config', 'neo.config'):
                run([sys.executable, package / 'validate-config.py',
                     package / fragment, output / 'resolved.config'])
            if 'CONFIG_RUST=y' not in resolved.splitlines():
                raise ValueError('Rust drivers were disabled by Kconfig/toolchain checks')
        report['status'] = 'passed'
    finally:
        (output / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
        # Keep evidence, not regenerable host tools and Kbuild intermediates.
        shutil.rmtree(build)
    print(f'Configuration validated; evidence: {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kernel', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--package', type=Path,
                        default=Path(__file__).resolve().parents[2] / 'pkgbuilds/linux-aurora')
    args = parser.parse_args()
    try:
        check(args.kernel.resolve(), args.package.resolve(), args.output.resolve())
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
