#!/usr/bin/env python3
import argparse
import nbformat
import sys
from pathlib import Path

def process_notebook(path: Path, mode: str):
    try:
        nb = nbformat.read(path, as_version=nbformat.NO_CONVERT)
    except Exception as e:
        print(f"ERROR reading {path}: {e}")
        return False, False

    changed = False
    had_widgets = False

    # notebook-level widgets
    if 'widgets' in getattr(nb, 'metadata', {}):
        had_widgets = True
        if mode == 'add_state':
            if 'state' not in nb.metadata['widgets']:
                nb.metadata['widgets']['state'] = {}
                changed = True
        elif mode == 'remove':
            nb.metadata.pop('widgets', None)
            changed = True

    # cell-level widgets
    for i, cell in enumerate(nb.cells):
        md = cell.get('metadata', {})
        if 'widgets' in md:
            had_widgets = True
            if mode == 'add_state':
                if 'state' not in md['widgets']:
                    md['widgets']['state'] = {}
                    cell['metadata'] = md
                    changed = True
                    print(f"Added widgets.state to {path} cell {i}")
            elif mode == 'remove':
                md.pop('widgets', None)
                cell['metadata'] = md
                changed = True
                print(f"Removed widgets from {path} cell {i}")

    if changed:
        try:
            nbformat.write(nb, str(path))
            print(f"Updated {path}")
        except Exception as e:
            print(f"ERROR writing {path}: {e}")
            return had_widgets, False

    return had_widgets, changed

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--path', default='.', help='リポジトリルートまたはディレクトリ')
    p.add_argument('--mode', choices=['add_state','remove','list'], default='add_state',
                   help='add_state: widgets.state を追加 (既定)。remove: widgets を削除。list: 該当ファイル列挙のみ')
    p.add_argument('--pattern', default='**/*.ipynb', help='ノートブックファイル検索パターン')
    args = p.parse_args()

    base = Path(args.path).resolve()
    files = list(base.glob(args.pattern))
    if not files:
        print("No .ipynb files found")
        return 0

    any_widgets = False
    any_changed = False
    for f in files:
        had_widgets, changed = process_notebook(f, args.mode)
        any_widgets = any_widgets or had_widgets
        any_changed = any_changed or changed

    print("Summary: found widgets in any file:", any_widgets)
    print("Summary: any files changed:", any_changed)

    # Exit code 0 always so Actions won't fail unless script errors.
    return 0

if __name__ == '__main__':
    sys.exit(main())
