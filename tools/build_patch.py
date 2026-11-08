# -*- coding: utf-8 -*-
"""
Atmosphere LayeredFS Patch Builder for Village in the Shade (ほの暮しの庭 / 静谧田园)
TitleID: 01001BA027DD8000 (v393216 / Display Version 1.2.0)

Usage:
  python D:/Village-SC/tools/build_patch.py [--allow-partial]

Reads all JSON batches in D:/Village-SC/workspace/batches/, applies translated `sc` strings
to Slot 4 (Traditional Chinese slot) of the 37 localized /data/database/*.dat files,
rebuilds the binary .dat files with dynamically recalculated string pool offsets,
verifies binary round-trip integrity, and outputs the ready-to-use Atmosphere patch to:
  D:/Village-SC/output/atmosphere/contents/01001BA027DD8000/romfs/data/database/*.dat
"""

import os
import sys
import json
import struct
import shutil
from dat_tool import LOCALIZED_37_FILES, parse_dat_bytes, rebuild_dat_bytes

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROMFS_DB_DIR = os.environ.get("VILLAGE_ROMFS_DB_DIR", os.path.join(REPO_ROOT, "unpacked", "romfs", "data", "database"))
BATCHES_DIR = os.environ.get("VILLAGE_BATCHES_DIR", os.path.join(REPO_ROOT, "workspace", "batches"))
OUTPUT_DB_DIR = os.environ.get("VILLAGE_OUTPUT_DB_DIR", os.path.join(REPO_ROOT, "output", "atmosphere", "contents", "01001BA027DD8000", "romfs", "data", "database"))


def build_atmosphere_patch(allow_partial: bool = False):
    os.makedirs(OUTPUT_DB_DIR, exist_ok=True)

    # Collect translations by (file, pidx_tc) -> sc
    translations_by_file = {fn: {} for fn in LOCALIZED_37_FILES}
    total_lines = 0
    translated_lines = 0
    missing_batches = []

    batch_files = sorted(fn for fn in os.listdir(BATCHES_DIR) if fn.endswith(".json"))
    for bfn in batch_files:
        bpath = os.path.join(BATCHES_DIR, bfn)
        with open(bpath, "r", encoding="utf-8") as f:
            batch = json.load(f)
        batch_missing = 0
        for rec in batch.get("records", []):
            fn = rec["file"]
            for ln in rec["lines"]:
                total_lines += 1
                pidx_tc = ln["pidx_tc"]
                sc = ln.get("sc", "")
                if sc:
                    translations_by_file[fn][pidx_tc] = sc
                    translated_lines += 1
                else:
                    batch_missing += 1
                    if allow_partial:
                        translations_by_file[fn][pidx_tc] = ln["tc"]
        if batch_missing > 0:
            missing_batches.append((bfn, batch_missing))

    print(f"Loaded {len(batch_files)} batch files: {translated_lines}/{total_lines} lines translated.")
    if missing_batches and not allow_partial:
        print(f"ERROR: {len(missing_batches)} batch(es) still have untranslated lines (use --allow-partial to fallback to ZH-TW):")
        for bfn, cnt in missing_batches[:15]:
            print(f"  - {bfn}: {cnt} untranslated lines")
        sys.exit(1)

    total_written_bytes = 0
    for fn in LOCALIZED_37_FILES:
        orig_path = os.path.join(ROMFS_DB_DIR, fn)
        orig_bytes = open(orig_path, "rb").read()
        cnt, rsize, records, rec_chains, pool_strings, ml_slots = parse_dat_bytes(orig_bytes)

        file_trans = translations_by_file.get(fn, {})
        mod_strings = list(pool_strings)
        replaced_cnt = 0
        for pidx_tc, sc_val in file_trans.items():
            mod_strings[pidx_tc] = sc_val
            replaced_cnt += 1

        new_bytes = rebuild_dat_bytes(cnt, rsize, records, rec_chains, mod_strings)

        # Round-trip structural verification on rebuilt binary
        cnt2, rsize2, _, _, pool_strings2, _ = parse_dat_bytes(new_bytes)
        assert cnt2 == cnt and rsize2 == rsize and pool_strings2 == mod_strings, f"Round-trip verification failed on {fn}!"

        out_path = os.path.join(OUTPUT_DB_DIR, fn)
        with open(out_path, "wb") as out_f:
            out_f.write(new_bytes)
        total_written_bytes += len(new_bytes)
        print(f"  [OK] {fn:28s}: {replaced_cnt:6d} strings updated | {len(orig_bytes):9d} B -> {len(new_bytes):9d} B")

    # Build texture routing patches for official SC graphics
    tex_remaps = {
        "texture.dat": {
            "data/texture/fairy_ui_0070/ui_0070_buttonicon_text_TC.nltx": "data/texture/fairy_ui_0070/ui_0070_buttonicon_text_sc.nltx",
            "data/texture/minimap_01_spr_TC.nltx": "data/texture/minimap_01_spr_sc.nltx",
            "data/texture/minimap_01_sum_TC.nltx": "data/texture/minimap_01_sum_sc.nltx",
            "data/texture/minimap_01_aut_TC.nltx": "data/texture/minimap_01_aut_sc.nltx",
            "data/texture/minimap_01_win_TC.nltx": "data/texture/minimap_01_win_sc.nltx",
            "data/texture/minimap_11_spr_TC.nltx": "data/texture/minimap_11_spr_sc.nltx",
            "data/texture/fairy_ui_5080/ui_5080_02_TC.nltx": "data/texture/fairy_ui_5080/ui_5080_02_sc.nltx",
        },
        "framework_texture.dat": {
            "data/texture/number_framework_TC.nltx": "data/texture/number_framework_sc.nltx",
        }
    }
    for tfn, remap in tex_remaps.items():
        tpath = os.path.join(ROMFS_DB_DIR, tfn)
        tbytes = open(tpath, "rb").read()
        cnt, rsize, records, rec_chains, pool_strings, ml_slots = parse_dat_bytes(tbytes)
        rep_c = 0
        for r, f_idx, rec_id, pidxs, offs in ml_slots:
            tc_pidx = pidxs[4]
            old_val = pool_strings[tc_pidx]
            if old_val in remap:
                pool_strings[tc_pidx] = remap[old_val]
                rep_c += 1
        new_tbytes = rebuild_dat_bytes(cnt, rsize, records, rec_chains, pool_strings)
        with open(os.path.join(OUTPUT_DB_DIR, tfn), "wb") as out_f:
            out_f.write(new_tbytes)
        total_written_bytes += len(new_tbytes)
        print(f"  [OK] {tfn:28s}: {rep_c:6d} texture routes updated | {len(tbytes):9d} B -> {len(new_tbytes):9d} B")

    # Build extra databases (multiLineText lore noticeboards and player character customization)
    extra_databases = {
        "multiLineText.dat": {
            (0, 0): "其一，晚十一点后禁止外出",
            (0, 1): "其二，当为村落齐心协力",
            (0, 2): "其三，切勿接近陌生人",
            (0, 3): "其四，切勿刺探他人秘密",
            (0, 4): "其五，绝不可离开村落",
            (0, 5): "其六，切勿回应山中呼唤",
            (0, 6): "其七，切勿寻觅遗失之物",
            (0, 7): "其八，欲有所求必付相应代价",
            (1, 0): "谨听：背弃戒律者，难逃神明耳目。",
            (1, 1): "梦魇之中，恐伤己身。",
            (1, 2): "故建此辰鼓楼，",
            (1, 3): "以报清晨破晓之警醒。",
            (2, 0): "……",
            (2, 1): "第七十四代柱　树木",
            (2, 2): "第七十五代柱　树木森子",
            (2, 3): "第七十六代柱　树木兼森",
            (2, 4): "第七十七代柱　树木林乃进",
            (2, 5): "第七十八代柱　树木森枝",
            (2, 6): "第七十九代柱　——",
            (2, 7): "                                          树木木珠",
            (2, 8): "第八十代柱　——",
            (3, 0): "……",
            (3, 1): "树木林　血液 300ml",
            (3, 2): "树木林　血液 200ml",
            (3, 3): "树木林　血液 300ml",
            (3, 4): "树木林　血液 500ml",
            (3, 5): "树木林　血液 300ml",
            (3, 6): "树木林　血液 200ml",
            (3, 7): "树木林　血液 300ml",
        },
        "playerFrontHairStyle.dat": {
            "PLAYER_FRONT_HAIR_STYLE_ID_1": "普通",
            "PLAYER_FRONT_HAIR_STYLE_ID_2": "齐刘海",
            "PLAYER_FRONT_HAIR_STYLE_ID_3": "短发",
            "PLAYER_FRONT_HAIR_STYLE_ID_4": "斜分刘海",
            "PLAYER_FRONT_HAIR_STYLE_ID_5": "单侧刘海",
            "PLAYER_FRONT_HAIR_STYLE_ID_6": "交错刘海",
            "PLAYER_FRONT_HAIR_STYLE_ID_7": "中分",
            "PLAYER_FRONT_HAIR_STYLE_ID_8": "微翘中分",
            "PLAYER_FRONT_HAIR_STYLE_ID_9": "厚重刘海",
            "PLAYER_FRONT_HAIR_STYLE_ID_10": "大背头",
            "PLAYER_FRONT_HAIR_STYLE_ID_11": "卷发中分",
            "PLAYER_FRONT_HAIR_STYLE_ID_12": "平整中分",
            "PLAYER_FRONT_HAIR_STYLE_ID_13": "三七分",
            "PLAYER_FRONT_HAIR_STYLE_ID_14": "眉上刘海",
            "PLAYER_FRONT_HAIR_STYLE_ID_15": "带鬓角三七分",
            "PLAYER_FRONT_HAIR_STYLE_ID_16": "侧边麻花辫",
            "PLAYER_FRONT_HAIR_STYLE_ID_17": "蓬松卷发",
            "PLAYER_FRONT_HAIR_STYLE_ID_18": "碎齐刘海",
            "PLAYER_FRONT_HAIR_STYLE_ID_19": "大波浪",
        },
        "playerBackHairStyle.dat": {
            "PLAYER_BACK_HAIR_STYLE_ID_1": "双叶",
            "PLAYER_BACK_HAIR_STYLE_ID_2": "呆毛",
            "PLAYER_BACK_HAIR_STYLE_ID_3": "双马尾",
            "PLAYER_BACK_HAIR_STYLE_ID_4": "低马尾",
            "PLAYER_BACK_HAIR_STYLE_ID_5": "马尾",
            "PLAYER_BACK_HAIR_STYLE_ID_6": "小啾啾",
            "PLAYER_BACK_HAIR_STYLE_ID_7": "丸子头",
            "PLAYER_BACK_HAIR_STYLE_ID_8": "双角发髻",
            "PLAYER_BACK_HAIR_STYLE_ID_9": "长发",
            "PLAYER_BACK_HAIR_STYLE_ID_12": "半双马尾",
            "PLAYER_BACK_HAIR_STYLE_ID_13": "狼尾发型",
            "PLAYER_BACK_HAIR_STYLE_ID_14": "侧马尾",
            "PLAYER_BACK_HAIR_STYLE_ID_15": "超短发",
            "PLAYER_BACK_HAIR_STYLE_ID_16": "微卷短发",
            "PLAYER_BACK_HAIR_STYLE_ID_17": "侧边丸子头",
            "PLAYER_BACK_HAIR_STYLE_ID_18": "单麻花辫",
            "PLAYER_BACK_HAIR_STYLE_ID_19": "双麻花辫",
            "PLAYER_BACK_HAIR_STYLE_ID_20": "双丸子头",
            "PLAYER_BACK_HAIR_STYLE_ID_21": "大小姐双卷发",
            "PLAYER_BACK_HAIR_STYLE_ID_24": "长卷发",
            "PLAYER_BACK_HAIR_STYLE_ID_25": "爆炸头",
            "PLAYER_BACK_HAIR_STYLE_ID_26": "齐刘海长发",
            "PLAYER_BACK_HAIR_STYLE_ID_27": "波波头",
            "PLAYER_BACK_HAIR_STYLE_ID_28": "微卷波波头",
            "PLAYER_BACK_HAIR_STYLE_ID_29": "武士高马尾",
        },
        "playerCrothing.dat": {
            "PLAYER_CROTHING_ID_1": "默认服饰",
            "PLAYER_CROTHING_ID_2": "牛仔装",
            "PLAYER_CROTHING_ID_3": "半身裙",
            "PLAYER_CROTHING_ID_4": "牛角扣大衣",
            "PLAYER_CROTHING_ID_5": "针织背心",
            "PLAYER_CROTHING_ID_6": "睡衣",
            "PLAYER_CROTHING_ID_8": "雨衣",
            "PLAYER_CROTHING_ID_9": "连衣裙",
            "PLAYER_CROTHING_ID_10": "西装",
            "PLAYER_CROTHING_ID_11": "正装礼服",
            "PLAYER_CROTHING_ID_12": "甚平",
            "PLAYER_CROTHING_ID_13": "侦探风衣",
        },
        "playerHeadAccessory.dat": {
            "PLAYER_HEAD_ACCESSORY_ID_1": "无",
            "PLAYER_HEAD_ACCESSORY_ID_01": "草帽",
            "PLAYER_HEAD_ACCESSORY_ID_02": "贝雷帽",
            "PLAYER_HEAD_ACCESSORY_ID_03": "牛仔帽",
            "PLAYER_HEAD_ACCESSORY_ID_04": "侦探帽",
            "PLAYER_HEAD_ACCESSORY_ID_05": "睡帽",
            "PLAYER_HEAD_ACCESSORY_ID_06": "春季花环",
            "PLAYER_HEAD_ACCESSORY_ID_07": "夏季花环",
            "PLAYER_HEAD_ACCESSORY_ID_08": "秋季花环",
            "PLAYER_HEAD_ACCESSORY_ID_09": "冬季花环",
            "PLAYER_HEAD_ACCESSORY_ID_10": "魔法师帽",
            "PLAYER_HEAD_ACCESSORY_ID_11": "鸭舌帽",
            "PLAYER_HEAD_ACCESSORY_ID_12": "斗笠",
            "PLAYER_HEAD_ACCESSORY_ID_30": "狐狸面具",
            "PLAYER_HEAD_ACCESSORY_ID_31": "般若面具",
            "PLAYER_HEAD_ACCESSORY_ID_32": "阿龟面具",
            "PLAYER_HEAD_ACCESSORY_ID_37": "天狗面具",
            "PLAYER_HEAD_ACCESSORY_ID_34": "音符发夹",
            "PLAYER_HEAD_ACCESSORY_ID_35": "蝴蝶发饰",
            "PLAYER_HEAD_ACCESSORY_ID_36": "花朵发饰",
            "PLAYER_HEAD_ACCESSORY_ID_50": "蝴蝶结",
            "PLAYER_HEAD_ACCESSORY_ID_52": "小铃铛",
            "PLAYER_HEAD_ACCESSORY_ID_53": "毛球发饰",
            "PLAYER_HEAD_ACCESSORY_ID_60": "兔耳发箍",
            "PLAYER_HEAD_ACCESSORY_ID_62": "洛丽塔发带",
            "PLAYER_HEAD_ACCESSORY_ID_63": "耳机",
            "PLAYER_HEAD_ACCESSORY_ID_70": "眼罩",
            "PLAYER_HEAD_ACCESSORY_ID_71": "护目镜",
            "PLAYER_HEAD_ACCESSORY_ID_72": "眼镜",
            "PLAYER_HEAD_ACCESSORY_ID_73": "太阳镜",
            "PLAYER_HEAD_ACCESSORY_ID_74": "单片眼镜",
        },
        "playerNeckAccessory.dat": {
            "PLAYER_NECK_ACCESSORY_ID_1": "无颈饰",
            "PLAYER_NECK_ACCESSORY_ID_2": "丝巾",
            "PLAYER_NECK_ACCESSORY_ID_3": "围巾",
            "PLAYER_NECK_ACCESSORY_ID_4": "毛绒围脖",
        },
        "playerBackAccessory.dat": {
            "PLAYER_BACK_ACCESSORY_ID_1": "无背包",
        }
    }

    for efn, trans_map in extra_databases.items():
        epath = os.path.join(ROMFS_DB_DIR, efn)
        ebytes = open(epath, "rb").read()
        cnt, rsize, records, rec_chains, pool_strings, ml_slots = parse_dat_bytes(ebytes)
        rep_c = 0
        for slot in ml_slots:
            rec_idx, field_idx, rec_id, pidxs, _ = slot
            if efn == "multiLineText.dat":
                key = (rec_idx, field_idx)
                if key in trans_map:
                    sc_text = trans_map[key]
                    pool_strings[pidxs[4]] = sc_text
                    rep_c += 1
            else:
                if rec_id in trans_map:
                    sc_text = trans_map[rec_id]
                    pool_strings[pidxs[4]] = sc_text
                    rep_c += 1
        new_ebytes = rebuild_dat_bytes(cnt, rsize, records, rec_chains, pool_strings)
        with open(os.path.join(OUTPUT_DB_DIR, efn), "wb") as out_f:
            out_f.write(new_ebytes)
        total_written_bytes += len(new_ebytes)
        print(f"  [OK] {efn:28s}: {rep_c:6d} custom strings updated | {len(ebytes):9d} B -> {len(new_ebytes):9d} B")

    # Build 1.2x handheld large font profile with engine-level vertical offset calibration
    font_src = os.path.join(ROMFS_DB_DIR, "font.dat")
    font_dst = os.path.join(OUTPUT_DB_DIR, "font.dat")
    with open(font_src, "rb") as f:
        fdata = bytearray(f.read())
    fcnt, frsize, fssize = struct.unpack_from("<III", fdata, 0)
    fpos = 12
    # Profile: 1.2x Japanese Base Sizes + Calibrated offsetY
    # Rec 0 (BIG):        46x46 px, offY = 3 (upshift 2px relative to vanilla 5)
    # Rec 1 (GAME):       38x38 px, offY = 0 (upshift 2px relative to vanilla 2)
    # Rec 2 (SMALL):      29x29 px, offY = 1 (upshift 4px relative to vanilla TC 5, aligned with official SC 1)
    # Rec 3 (SMALL_TEXT): 29x29 px, offY = 1 (upshift 4px relative to vanilla TC 5, aligned with official SC 1)
    # Rec 4 (TALK):       38x38 px, offY = 0 (vanilla 0)
    font_configs = {
        0: (46, 46, 3),  # FONT_ID_GAME_BIG: 38 * 1.2 = 45.6 -> 46
        1: (38, 38, 0),  # FONT_ID_GAME: 32 * 1.2 = 38.4 -> 38
        2: (29, 29, 1),  # FONT_ID_GAME_SMALL: 24 * 1.2 = 28.8 -> 29
        3: (29, 29, 1),  # FONT_ID_GAME_SMALL_TEXT: 24 * 1.2 = 28.8 -> 29
        4: (38, 38, 0),  # FONT_ID_GAME_TALK: 32 * 1.2 = 38.4 -> 38
    }
    for r in range(fcnt):
        frlen = struct.unpack_from("<I", fdata, fpos)[0]
        frec_start = fpos + 4
        fw, fh, off_y = font_configs[r]
        for lang, l_off in [("TC", 0x228), ("SC", 0x330)]:
            fchunk = frec_start + l_off
            struct.pack_into("<ii", fdata, fchunk + 16, fw, fh)
            struct.pack_into("<i", fdata, fchunk + 60, off_y)
        fpos += 4 + frlen
    with open(font_dst, "wb") as f:
        f.write(fdata)
    total_written_bytes += len(fdata)
    total_files_built = len(LOCALIZED_37_FILES) + len(tex_remaps) + len(extra_databases) + 1
    print(f"  [OK] {'font.dat':28s}: Handheld 1.2x Large Font profile compiled (46/38/29px, calibrated offsetY) | {len(fdata)} B")

    # Sync to Eden mod folder if present
    eden_db_dir = r"C:\Users\Admin\AppData\Roaming\eden\load\01001BA027DD8000\Village_SC_Translation\romfs\data\database"
    if os.path.exists(eden_db_dir):
        for fname in os.listdir(OUTPUT_DB_DIR):
            if fname.endswith(".dat"):
                shutil.copy2(os.path.join(OUTPUT_DB_DIR, fname), os.path.join(eden_db_dir, fname))
        print(f"  [OK] Successfully synced {total_files_built} database files to Eden mod folder.")

    print(
        f"\nSuccessfully built Atmosphere LayeredFS patch!\n"
        f"  Output directory: {OUTPUT_DB_DIR}\n"
        f"  Files compiled  : {total_files_built} .dat files ({total_written_bytes / (1024*1024):.2f} MB)"
    )


if __name__ == "__main__":
    allow_partial = "--allow-partial" in sys.argv[1:]
    build_atmosphere_patch(allow_partial=allow_partial)
