# -*- coding: utf-8 -*-
"""
Extract all 37 localized database files from D:/Village-SC/unpacked/romfs/data/database/
into context-preserving, record-grouped JSON translation batches in D:/Village-SC/workspace/batches/.
Includes automatic speaker attribution (`spk`) for every dialogue line in `talk.dat`.
"""

import os
import struct
import json
from collections import OrderedDict
from dat_tool import LOCALIZED_37_FILES, parse_dat_bytes

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROMFS_DB_DIR = os.environ.get("VILLAGE_ROMFS_DB_DIR", os.path.join(REPO_ROOT, "unpacked", "romfs", "data", "database"))
WORKSPACE_DIR = os.environ.get("VILLAGE_WORKSPACE_DIR", os.path.join(REPO_ROOT, "workspace"))
BATCHES_DIR = os.path.join(WORKSPACE_DIR, "batches")
MAX_LINES_PER_BATCH = 200

# Speaker ID mapping from talkNameplate.dat
SPEAKER_LABELS = {
    0: "主角心声/旁白/选项",
    10: "帷 (トバリ)",
    11: "木助 (キスケ)",
    12: "四郎治 (シロージ)",
    13: "林 (リン)",
    14: "驹子 (コマコ)",
    15: "茶梅 (サザンカ)",
    16: "六角 (ロッカク)",
    17: "今野 (コンノ)",
    18: "名护 (ナゴ)",
    19: "洋 (ヨウ)",
    20: "裕太 (ユータ)",
    21: "堇怜 (スミレ)",
    22: "莲实 (ハスミ)",
    23: "琪娜娜 (チナナ)",
    24: "木珠 (コダマ)",
    25: "母亲 (＊)",
    26: "红衣商人 (？？？)",
    27: "蓝衣商人 (？？？)",
    28: "？？？ (未知角色)",
    29: "评鉴会职员 (品評会職員)",
    31: "洋的母亲 (？？？)",
    32: "洋的父亲 (？？？)",
    33: "年轻时的六角 (？？？)",
    34: "欧万 (オワン/鹦鹉)",
    35: "主 (ヅ主/神明)",
    36: "<player> (主角)",
    37: "？？？ (未知角色2)",
}

FILE_GROUPS = [
    ("sys_ui", [
        "action.dat", "cmd.dat", "framework_cmd.dat", "framework_string.dat",
        "framework_vkey.dat", "framework_vkeyCategory.dat", "vkey.dat",
        "gameEffect.dat", "gameSetting.dat", "string.dat", "logText.dat", "updateText.dat"
    ]),
    ("world_meta", [
        "character.dat", "talkNameplate.dat", "facility.dat", "facilityRelease.dat",
        "construction.dat", "bundle.dat", "bundleGroup.dat", "skillTree.dat",
        "trophy.dat", "whistle.dat", "bgm.dat"
    ]),
    ("flora_fauna", [
        "crops.dat", "livestock.dat", "creature.dat", "itemType.dat", "intangeble.dat"
    ]),
    ("quest_tips", [
        "quest.dat", "tips.dat"
    ]),
    ("lore_letters", [
        "letter.dat", "lostBook.dat", "reminiscence.dat"
    ]),
    ("credits", [
        "credit.dat", "framework_credit.dat"
    ]),
    ("item", ["item.dat"]),
    ("talk", ["talk.dat"]),
]


def get_talk_slot_speakers(records, ml_slots):
    """Map (rec_idx, f_idx) -> speaker label string for talk.dat."""
    slots_by_rec = {}
    for s in ml_slots:
        slots_by_rec.setdefault(s[0], []).append(s)

    slot_spk_map = {}
    for r, rec_slots in slots_by_rec.items():
        rec = records[r]
        rec_id = rec_slots[0][2]
        boxes = [[rec_slots[0]]]
        for s in rec_slots[1:]:
            if s[4][0] - boxes[-1][-1][4][0] == 64:
                boxes[-1].append(s)
            else:
                boxes.append([s])

        last_valid_spk = 0
        for box in boxes:
            first_off = box[0][4][0]
            spk_id = struct.unpack_from("<I", rec, first_off - 44)[0] if first_off >= 44 else 0
            if spk_id == 69 and "HUNTER" in rec_id:
                spk_id = 14
            elif spk_id not in SPEAKER_LABELS:
                spk_id = 0
            spk_label = SPEAKER_LABELS[spk_id]
            for s in box:
                slot_spk_map[(r, s[1])] = spk_label
    return slot_spk_map


def extract_all_batches():
    os.makedirs(BATCHES_DIR, exist_ok=True)
    manifest = {
        "title_id": "01001BA027DD8000",
        "version": "1.2.0 (v393216)",
        "total_files": len(LOCALIZED_37_FILES),
        "total_records": 0,
        "total_lines": 0,
        "batches": [],
    }

    batch_global_idx = 1

    for group_name, file_list in FILE_GROUPS:
        group_records = []
        for fn in file_list:
            fpath = os.path.join(ROMFS_DB_DIR, fn)
            data = open(fpath, "rb").read()
            cnt, rsize, records, rec_chains, pool_strings, ml_slots = parse_dat_bytes(data)

            slot_spk_map = get_talk_slot_speakers(records, ml_slots) if fn == "talk.dat" else {}

            by_rec = OrderedDict()
            for r, f_idx, rec_id, pidxs, offs in ml_slots:
                ja = pool_strings[pidxs[0]]
                tc = pool_strings[pidxs[4]]
                if not tc:
                    continue
                if r not in by_rec:
                    by_rec[r] = {
                        "file": fn,
                        "rec_idx": r,
                        "rec_id": rec_id,
                        "lines": [],
                    }
                line_obj = {
                    "f_idx": f_idx,
                    "pidx_tc": pidxs[4],
                }
                if fn == "talk.dat":
                    line_obj["spk"] = slot_spk_map.get((r, f_idx), "主角心声/旁白/选项")
                line_obj["ja"] = ja
                line_obj["tc"] = tc
                line_obj["sc"] = ""
                by_rec[r]["lines"].append(line_obj)
            for rec_obj in by_rec.values():
                group_records.append(rec_obj)

        cur_batch_recs = []
        cur_batch_lines = 0

        def flush_batch(recs, line_cnt):
            nonlocal batch_global_idx
            if not recs:
                return
            batch_id = f"batch_{batch_global_idx:03d}_{group_name}"
            batch_filename = f"{batch_id}.json"
            batch_path = os.path.join(BATCHES_DIR, batch_filename)
            files_in_batch = sorted(list({r["file"] for r in recs}))
            batch_obj = {
                "batch_id": batch_id,
                "group": group_name,
                "files": files_in_batch,
                "record_count": len(recs),
                "line_count": line_cnt,
                "records": recs,
            }
            with open(batch_path, "w", encoding="utf-8") as f:
                json.dump(batch_obj, f, ensure_ascii=False, indent=2)

            manifest["batches"].append({
                "batch_id": batch_id,
                "filename": batch_filename,
                "group": group_name,
                "files": files_in_batch,
                "record_count": len(recs),
                "line_count": line_cnt,
            })
            manifest["total_records"] += len(recs)
            manifest["total_lines"] += line_cnt
            batch_global_idx += 1

        for rec_obj in group_records:
            n_lines = len(rec_obj["lines"])
            if cur_batch_recs and (cur_batch_lines + n_lines > MAX_LINES_PER_BATCH):
                flush_batch(cur_batch_recs, cur_batch_lines)
                cur_batch_recs = []
                cur_batch_lines = 0
            cur_batch_recs.append(rec_obj)
            cur_batch_lines += n_lines

        flush_batch(cur_batch_recs, cur_batch_lines)

    manifest_path = os.path.join(WORKSPACE_DIR, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(
        f"Extracted {len(manifest['batches'])} batches covering "
        f"{manifest['total_records']} records and {manifest['total_lines']} localized lines (with speaker attribution)."
    )


if __name__ == "__main__":
    extract_all_batches()
