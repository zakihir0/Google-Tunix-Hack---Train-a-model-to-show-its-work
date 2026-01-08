#!/usr/bin/env python3
"""
Sanitize Jupyter notebooks to fix rendering/nbformat validation issues.

Behavior:
 - For each .ipynb found under --path:
   1) Validate as-is. If valid, skip.
   2) Remove metadata.widgets and cell.metadata.widgets and some Colab refs, then validate.
   3) If still invalid, remove widget-view outputs and validate.
   4) If still invalid, clear all cell outputs and execution_count, remove attachments, then validate.
   5) Write changes if made and report status.

Usage (locally):
  python scripts/sanitize_notebooks.py --path . --pattern '**/*.ipynb' --dry-run

Run in Actions: workflow will call this script and commit/push changes.

"""
import argparse
import nbformat
import shutil
import sys
import traceback
from pathlib import Path
from nbformat import validate, ValidationError

def backup(path: Path):
    bak = path.with_suffix(path.suffix + '.bak')
    try:
        shutil.copy2(path, bak)
        print(f"[BACKUP] {path} -> {bak}")
    except Exception as e:
        print(f"[WARN] backup failed for {path}: {e}")

def find_widgets_locations(nb):
    locs = []
    if 'widgets' in getattr(nb, 'metadata', {}):
        locs.append(('notebook', None, nb.metadata['widgets']))
    for i, cell in enumerate(nb.cells):
        md = cell.get('metadata', {})
        if 'widgets' in md:
            locs.append(('cell', i, md['widgets']))
    return locs

def try_validate(nb):
    try:
        validate(nb)
        return True, ""
    except ValidationError as ve:
        return False, str(ve)
    except Exception as e:
        return False, f"{e}\n{traceback.format_exc()}"

def remove_widget_metadata(nb):
    changed = False
    if 'widgets' in getattr(nb, 'metadata', {}):
        nb.metadata.pop('widgets', None)
        changed = True
    # remove common colab widget refs that may exist
    if 'colab' in getattr(nb, 'metadata', {}):
        colab = nb.metadata.get('colab')
        if isinstance(colab, dict) and 'referenced_widgets' in colab:
            colab.pop('referenced_widgets', None)
            nb.metadata['colab'] = colab
            changed = True
    for i, cell in enumerate(nb.cells):
        md = cell.get('metadata', {})
        if 'widgets' in md:
            md.pop('widgets', None)
            cell['metadata'] = md
            changed = True
        # remove cell-level colab referenced_widgets if present
        if 'colab' in md:
            cm = md.get('colab')
            if isinstance(cm, dict) and 'referenced_widgets' in cm:
                cm.pop('referenced_widgets', None)
                md['colab'] = cm
                cell['metadata'] = md
                changed = True
    return changed

def remove_widget_view_outputs(nb):
    """
    Remove outputs that have application/vnd.jupyter.widget-view+json
    or other widget mime types. Return True if anything changed.
    """
    changed = False
    for cell in nb.cells:
        outs = cell.get('outputs', [])
        new_outs = []
        for out in outs:
            data = out.get('data') if isinstance(out, dict) else None
            if data and any(k.startswith('application/vnd.jupyter.widget') for k in data.keys()):
                changed = True
                continue
            new_outs.append(out)
        if len(new_outs) != len(outs):
            cell['outputs'] = new_outs
    return changed

def clear_all_outputs(nb):
    changed = False
    for cell in nb.cells:
        if cell.get('outputs'):
            cell['outputs'] = []
            changed = True
        if 'execution_count' in cell and cell['execution_count'] is not None:
            cell['execution_count'] = None
            changed = True
        # remove attachments (can be binary blobs causing render issues)
        if 'attachments' in cell.get('metadata', {}):
            md = cell['metadata']
            if 'attachments' in md:
                md.pop('attachments', None)
                cell['metadata'] = md
                changed = True
    # also remove top-level attachments if any (rare)
    if 'attachments' in getattr(nb, 'metadata', {}):
        nb.metadata.pop('attachments', None)
        changed = True
    return changed

def sanitize(path: Path, dry_run=False):
    try:
        nb = nbformat.read(path, as_version=nbformat.NO_CONVERT)
    except Exception as e:
        print(f"[ERROR] cannot read {path}: {e}")
        return {'path': str(path), 'error': True, 'msg': str(e)}

    result = {'path': str(path), 'changed': False, 'valid_before': None, 'valid_after': None, 'actions': []}
    valid, msg = try_validate(nb)
    result['valid_before'] = valid
    if valid:
        print(f"[OK] {path} is already valid")
        result['valid_after'] = True
        return result

    result['actions'].append(('validation_failed', msg))
    print(f"[INFO] {path} failed validate: {msg[:300]}")

    # make backup
    backup(path)

    # Step 1: remove widget metadata (and colab referenced_widgets)
    if remove_widget_metadata(nb):
        result['actions'].append(('removed_widget_metadata', True))
        print(f"[INFO] removed widget metadata in {path}")

    # validate
    valid, msg = try_validate(nb)
    if valid:
        result['changed'] = True
        result['valid_after'] = True
        result['actions'].append(('validated_after_remove_widgets', True))
        if not dry_run:
            nbformat.write(nb, str(path))
        return result
    else:
        result['actions'].append(('validate_after_remove_widgets', msg))
        print(f"[INFO] still invalid after removing widget metadata: {msg[:300]}")

    # Step 2: remove widget-view outputs
    if remove_widget_view_outputs(nb):
        result['actions'].append(('removed_widget_view_outputs', True))
        print(f"[INFO] removed widget-view outputs in {path}")

    # validate
    valid, msg = try_validate(nb)
    if valid:
        result['changed'] = True
        result['valid_after'] = True
        result['actions'].append(('validated_after_remove_view_outputs', True))
        if not dry_run:
            nbformat.write(nb, str(path))
        return result
    else:
        result['actions'].append(('validate_after_remove_view_outputs', msg))
        print(f"[INFO] still invalid after removing widget outputs: {msg[:300]}")

    # Step 3: clear all outputs and attachments (aggressive)
    if clear_all_outputs(nb):
        result['actions'].append(('cleared_all_outputs', True))
        print(f"[INFO] cleared all outputs/attachments in {path}")

    # final validation
    valid, msg = try_validate(nb)
    result['valid_after'] = valid
    if valid:
        result['changed'] = True
        result['actions'].append(('validated_after_clearing_outputs', True))
        if not dry_run:
            nbformat.write(nb, str(path))
        print(f"[OK] {path} validated after clearing outputs")
    else:
        result['actions'].append(('still_invalid', msg))
        print(f"[ERROR] {path} still invalid after aggressive cleaning: {msg}")

        # Dump snippets of suspicious metadata for debugging
        locs = find_widgets_locations(nb)
        if locs:
            print("---- widgets metadata dump ----")
            for loc in locs:
                typ, idx, val = loc
                if typ == 'notebook':
                    print("notebook.metadata.widgets =", repr(val)[:1000])
                else:
                    print(f"cell[{idx}].metadata.widgets =", repr(val)[:1000])
            print("---- end dump ----")

        # Also print first 800 chars of entire notebook JSON (for debugging) - careful with size
        try:
            txt = Path(path).read_text(encoding='utf-8', errors='replace')
            print("---- notebook head (first 2000 chars) ----")
            print(txt[:2000])
            print("---- end head ----")
        except Exception as e:
            print(f"[WARN] could not dump notebook text: {e}")

    return result

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--path', default='.', help='root path to search')
    p.add_argument('--pattern', default='**/*.ipynb', help='glob pattern')
    p.add_argument('--dry-run', action='store_true', help='do not write files, only report')
    args = p.parse_args()

    base = Path(args.path).resolve()
    files = sorted(base.glob(args.pattern))
    if not files:
        print("[INFO] no .ipynb files found")
        return 0

    any_invalid = False
    any_changed = False
    for f in files:
        print(f"\n=== Processing {f} ===")
        r = sanitize(f, dry_run=args.dry_run)
        if r.get('error'):
            print(f"[ERROR] {r.get('msg')}")
            any_invalid = True
            continue
        if not r.get('valid_after'):
            any_invalid = True
        if r.get('changed'):
            any_changed = True

    print("\nSummary: any_changed =", any_changed, "any_invalid =", any_invalid)
    # Exit code non-zero if any invalid remain so Actions job shows failure
    return 2 if any_invalid else 0

if __name__ == '__main__':
    sys.exit(main())
