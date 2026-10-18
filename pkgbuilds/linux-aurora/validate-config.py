#!/usr/bin/env python3
"""Reject requested capabilities that Kconfig silently dropped."""
from pathlib import Path
import sys


def values(path):
    result = {}
    for line in Path(path).read_text().splitlines():
        if line.startswith('CONFIG_'):
            key, value = line.split('=', 1)
            result[key] = value
        elif line.startswith('# CONFIG_') and line.endswith(' is not set'):
            result[line.split()[1]] = 'n'
    return result


def validate(fragment, resolved):
    requested, actual = values(fragment), values(resolved)
    missing = [f'{name}: wanted {value}, got {actual.get(name, "absent")}'
               for name, value in requested.items() if actual.get(name) != value]
    if missing:
        raise ValueError('Kernel capabilities disabled by Kconfig:\n' + '\n'.join(missing))


def preserve_builtins(baseline, resolved):
    """Compare configs normalized by the same Kconfig and toolchain."""
    before, after = values(baseline), values(resolved)
    lost = [f'{name}: built in before fragments, got {after.get(name, "absent")}'
            for name, value in before.items() if value == 'y' and after.get(name) != 'y']
    if lost:
        raise ValueError('Shared built-in capabilities downgraded:\n' + '\n'.join(lost))


if __name__ == '__main__':
    try:
        if sys.argv[1:2] == ['--preserve-builtins']:
            preserve_builtins(*sys.argv[2:])
        else:
            validate(*sys.argv[1:])
    except (ValueError, OSError) as error:
        sys.exit(str(error))
