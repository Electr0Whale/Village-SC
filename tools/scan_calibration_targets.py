# -*- coding: utf-8 -*-
"""
Scan calibration targets across all 289 batches.
Identifies:
1. Pronoun and deity targets (Gods vs Youkai, 祂 vs 它/他, 妳/牠 residue).
2. Traditional 著 aspect particle residue (著 -> 着).
3. Speaker persona targets (今野, 六角, 帷, 木珠, 主, 琪娜娜).
"""

import os
import sys
import json
import re

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORKSPACE_DIR = os.environ.get("VILLAGE_WORKSPACE_DIR", os.path.join(REPO_ROOT, "workspace"))
BATCHES_DIR = os.path.join(WORKSPACE_DIR, "batches")

GOD_KEYWORDS = ["神", "ヌシ", "主様", "古神", "イザナギ", "イザナミ", "龍", "荒神", "氏神", "御神体"]
YOUKAI_KEYWORDS = ["妖怪", "妖", "鬼", "変化", "物の怪", "化け物", "怪物", "物の気", "異形"]

def scan_all():
    batch_files = sorted(fn for fn in os.listdir(BATCHES_DIR) if fn.endswith(".json"))

    god_candidates = []
    youkai_candidates = []
    zhu_residues = []
    forbidden_pronouns = []

    rokkaku_candidates = []
    konno_candidates = []
    tobari_candidates = []
    kodama_candidates = []
    nushi_candidates = []

    for bfn in batch_files:
        bpath = os.path.join(BATCHES_DIR, bfn)
        with open(bpath, "r", encoding="utf-8") as f:
            batch = json.load(f)

        for rec in batch.get("records", []):
            rec_id = rec.get("rec_id", "")
            fn = rec.get("file", "")
            for ln in rec.get("lines", []):
                ja = ln.get("ja", "")
                tc = ln.get("tc", "")
                sc = ln.get("sc", "")
                spk = ln.get("spk", "")

                loc = (bfn, fn, rec_id, spk, ja, tc, sc)

                # Forbidden pronouns
                if "妳" in sc or "牠" in sc:
                    forbidden_pronouns.append(loc)

                # 著 residue
                if "著" in sc and "著名" not in sc and "原著" not in sc and "名著" not in sc:
                    zhu_residues.append(loc)

                # God candidates: TC had 祂, or JA mentions god/nushi, or SC refers to God
                if "祂" in tc or any(k in ja for k in ["神様", "イザナギ", "主様", "ヅ主"]):
                    god_candidates.append(loc)

                # Speaker tics
                if "六角" in spk and ("っス" in ja):
                    rokkaku_candidates.append(loc)
                elif "今野" in spk and any(k in ja for k in ["まァす", "ねェ", "ですヨ", "ますヨ", "かァ", "おやァ"]):
                    konno_candidates.append(loc)
                elif "帷" in spk and ("ないでくれる" in ja or "アンタ" in ja):
                    tobari_candidates.append(loc)
                elif "木珠" in spk and ("、" in ja or "……" in ja):
                    kodama_candidates.append(loc)
                elif "主" in spk:
                    nushi_candidates.append(loc)

    print("=== Target Scan Summary ===")
    print(f"Forbidden pronouns (妳/牠) in SC: {len(forbidden_pronouns)}")
    print(f"Aspect particle '著' residues: {len(zhu_residues)}")
    print(f"Deity/God calibration candidates: {len(god_candidates)}")
    print(f"Rokkaku (っス) tic candidates: {len(rokkaku_candidates)}")
    print(f"Konno (prolonged sarcastic) candidates: {len(konno_candidates)}")
    print(f"Tobari (cold/tsundere) candidates: {len(tobari_candidates)}")
    print(f"Kodama (stutter/broken) candidates: {len(kodama_candidates)}")
    print(f"Nushi (divine speech) candidates: {len(nushi_candidates)}")

    return {
        "forbidden_pronouns": forbidden_pronouns,
        "zhu_residues": zhu_residues,
        "god_candidates": god_candidates,
        "rokkaku_candidates": rokkaku_candidates,
        "konno_candidates": konno_candidates,
        "tobari_candidates": tobari_candidates,
        "kodama_candidates": kodama_candidates,
        "nushi_candidates": nushi_candidates,
    }

if __name__ == "__main__":
    scan_all()
