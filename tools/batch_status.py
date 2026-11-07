# -*- coding: utf-8 -*-
"""
Progress & Batch Status CLI for Gemini 3.8 Flash High.

Usage:
  python D:/Village-SC/tools/batch_status.py          # Show overall progress and next 5 pending batches
  python D:/Village-SC/tools/batch_status.py --next   # Print only the next pending batch path
"""

import os
import sys
import json
from validate_batch import validate_single_batch, load_font_cps

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BATCHES_DIR = os.environ.get("VILLAGE_BATCHES_DIR", os.path.join(REPO_ROOT, "workspace", "batches"))


def main():
    font_cps = load_font_cps()
    batch_files = sorted(fn for fn in os.listdir(BATCHES_DIR) if fn.endswith(".json"))

    done_batches = []
    pending_batches = []
    error_batches = []

    for bfn in batch_files:
        bpath = os.path.join(BATCHES_DIR, bfn)
        with open(bpath, "r", encoding="utf-8") as f:
            batch = json.load(f)
        lines = [ln for rec in batch.get("records", []) for ln in rec.get("lines", [])]
        filled = sum(1 for ln in lines if ln.get("sc", "") != "")
        if filled == 0:
            pending_batches.append((bfn, 0, len(lines)))
        elif filled < len(lines):
            error_batches.append((bfn, f"Partially filled ({filled}/{len(lines)})"))
        else:
            errs, _ = validate_single_batch(bpath, font_cps)
            if errs:
                error_batches.append((bfn, f"{len(errs)} validation error(s): {errs[0]}"))
            else:
                done_batches.append(bfn)

    if "--next" in sys.argv[1:]:
        if error_batches:
            print(os.path.join(BATCHES_DIR, error_batches[0][0]))
        elif pending_batches:
            print(os.path.join(BATCHES_DIR, pending_batches[0][0]))
        else:
            print("ALL_DONE")
        return

    print(f"=== Village-SC Translation Progress ===")
    print(f"  Completed & Validated : {len(done_batches):3d} / {len(batch_files)}")
    print(f"  With Validation Errors: {len(error_batches):3d} / {len(batch_files)}")
    print(f"  Pending (Untranslated): {len(pending_batches):3d} / {len(batch_files)}")

    if error_batches:
        print("\n[!] Batches needing fixes first:")
        for bfn, msg in error_batches[:5]:
            print(f"  - {bfn}: {msg}")

    if pending_batches:
        print("\nNext 5 pending batches to process:")
        for bfn, _, total in pending_batches[:5]:
            print(f"  - D:\\Village-SC\\workspace\\batches\\{bfn} ({total} lines)")


if __name__ == "__main__":
    main()
