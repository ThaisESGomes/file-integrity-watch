"""Offline SHA-256 file integrity checker."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile


def digest(path):
    fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
    with os.fdopen(fd, 'rb') as source:
        before = os.fstat(source.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise ValueError('File is not regular')
        value = hashlib.sha256()
        for block in iter(lambda: source.read(1024 * 1024), b''):
            value.update(block)
        after = os.fstat(source.fileno())
    if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
        raise ValueError(f'File changed during scan: {path}')
    return {'sha256': value.hexdigest(), 'size': after.st_size}


def scan(root, excluded=()):
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError('Target must be a directory')
    excluded = {Path(p).absolute() for p in excluded}
    files, skipped = {}, []
    def walk(directory):
        with os.scandir(directory) as entries:
            for entry in sorted(entries, key=lambda e: e.name):
                path = Path(entry.path)
                name = path.relative_to(root).as_posix()
                if path.absolute() in excluded:
                    continue
                if entry.is_symlink():
                    skipped.append({'path': name, 'reason': 'symbolic_link'})
                elif entry.is_dir(follow_symlinks=False):
                    walk(path)
                elif entry.is_file(follow_symlinks=False):
                    files[name] = digest(path)
                else:
                    skipped.append({'path': name, 'reason': 'special_file'})
    walk(root)
    return {'version': 1, 'algorithm': 'sha256', 'root': str(root), 'files': files, 'skipped': skipped}


def validate(value):
    if not isinstance(value, dict) or value.get('version') != 1 or value.get('algorithm') != 'sha256':
        raise ValueError('Unsupported manifest')
    if not isinstance(value.get('root'), str) or not isinstance(value.get('files'), dict) or not isinstance(value.get('skipped'), list):
        raise ValueError('Malformed manifest')
    for name, item in value['files'].items():
        if not isinstance(name, str) or name.startswith('/') or '\\' in name or any(p in ('', '.', '..') for p in name.split('/')):
            raise ValueError('Invalid path')
        if not isinstance(item, dict) or type(item.get('size')) is not int or item['size'] < 0:
            raise ValueError('Invalid metadata')
        checksum = item.get('sha256')
        if not isinstance(checksum, str) or len(checksum) != 64 or any(c not in '0123456789abcdef' for c in checksum):
            raise ValueError('Invalid checksum')
    return value


def compare(old, new):
    validate(old)
    validate(new)
    a, b = old['files'], new['files']
    result = {'added': sorted(b.keys()-a.keys()), 'removed': sorted(a.keys()-b.keys()),
              'modified': sorted(p for p in a.keys() & b.keys() if a[p] != b[p]), 'skipped': new['skipped']}
    result['summary'] = {key: len(result[key]) for key in ('added', 'removed', 'modified')}
    return result


def save(path, value):
    path = Path(path)
    fd, temp = tempfile.mkstemp(prefix='.integrity-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as target:
            json.dump(value, target, indent=2, ensure_ascii=False)
            target.write('\n')
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ('baseline', 'check'):
        part = sub.add_parser(command)
        part.add_argument('directory', type=Path)
        part.add_argument('--manifest', type=Path, required=True)
        if command == 'baseline':
            part.add_argument('--force', action='store_true')
        else:
            part.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    try:
        if args.directory.is_symlink():
            raise ValueError('Root cannot be a symlink')
        excluded = [args.manifest]
        if args.command == 'baseline':
            if args.manifest.exists() and not args.force:
                raise ValueError('Manifest exists; use --force to approve a new baseline')
            value = scan(args.directory, excluded)
            save(args.manifest, value)
            print(f"Baseline saved: {len(value['files'])} files; {len(value['skipped'])} skipped")
            return 0
        if args.output:
            if args.output.resolve() == args.manifest.resolve():
                raise ValueError('Report must not overwrite baseline')
            excluded.append(args.output)
        old = validate(json.loads(args.manifest.read_text(encoding='utf-8')))
        if str(args.directory.resolve(strict=True)) != old['root']:
            raise ValueError('Directory differs from baseline root')
        report = compare(old, scan(args.directory, excluded))
        if args.output:
            save(args.output, report)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1 if any(report['summary'].values()) else 0
    except (OSError, ValueError, RecursionError) as error:
        parser.exit(2, f'Error: {error}\n')

if __name__ == '__main__':
    raise SystemExit(main())
