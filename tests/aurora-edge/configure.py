#!/usr/bin/env python3
"""Resolve and validate the packaged Aurora config without compiling a kernel."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys


def check(kernel, package, baseline, output):
    output.mkdir(parents=True, exist_ok=False)
    builds = []
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
        inputs = ['config', 'common.config', 'neo.config', 'validate-config.py', 'configure.sh']
        report['inputs'] = {
            name: hashlib.sha256((package / name).read_bytes()).hexdigest()
            for name in inputs}
        report['baseline_inputs'] = {
            name: hashlib.sha256((baseline / name).read_bytes()).hexdigest()
            for name in inputs if name != 'configure.sh'}
        report['comparison'] = 'Base and candidate package configs resolved with the same kernel and toolchain'
        report['toolchain_scope'] = 'Configuration approximation; the full package build remains authoritative'
        original = (package / 'config').read_text()
        (output / 'original.config').write_text(original)
        with (output / 'configure.log').open('w') as log:
            def run(args):
                log.write('$ ' + ' '.join(map(str, args)) + '\n')
                log.flush()
                subprocess.run(list(map(str, args)), cwd=kernel,
                               stdout=log, stderr=subprocess.STDOUT, check=True)

            def resolve(config_dir, name):
                build = output / ('build-' + name)
                build.mkdir()
                builds.append(build)
                # prepare() supplies the production _make; this hosted check
                # uses its documented approximate toolchain with the same steps.
                command = '''set -euo pipefail
_make() { make ARCH=arm64 LLVM="${LLVM:-1}" BINDGEN="${BINDGEN:-bindgen}" LOCALVERSION= "$@"; }
source "$1/configure.sh"
configure_kernel "$2" "$3" "$4"
'''
                snapshot = 'requested.config' if name == 'resolved' else 'baseline-requested.config'
                try:
                    run(['bash', '-c', command, 'aurora-config', package,
                         config_dir, build, output / snapshot])
                finally:
                    if (build / '.config').exists():
                        shutil.copyfile(build / '.config', output / (name + '.config'))
                return (output / (name + '.config')).read_text()

            previous = resolve(baseline, 'baseline')
            resolved = resolve(package, 'resolved')
            (output / 'config.diff').write_text(''.join(difflib.unified_diff(
                previous.splitlines(keepends=True), resolved.splitlines(keepends=True),
                fromfile='base/resolved.config', tofile='candidate/resolved.config')))
            (output / 'raw-config.diff').write_text(''.join(difflib.unified_diff(
                original.splitlines(keepends=True), resolved.splitlines(keepends=True),
                fromfile='packaged/config', tofile='resolved.config')))
        report['status'] = 'passed'
    finally:
        (output / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
        # Keep evidence, not regenerable host tools and Kbuild intermediates.
        for build in builds:
            shutil.rmtree(build)
    print(f'Configuration validated; evidence: {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kernel', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True,
                        help='Base branch package directory, resolved with the candidate kernel and tools')
    parser.add_argument('--package', type=Path,
                        default=Path(__file__).resolve().parents[2] / 'pkgbuilds/linux-aurora')
    args = parser.parse_args()
    try:
        check(args.kernel.resolve(), args.package.resolve(), args.baseline.resolve(), args.output.resolve())
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
