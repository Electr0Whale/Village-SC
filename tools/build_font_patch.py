# -*- coding: utf-8 -*-
"""
Rebuild misc_1_00.dat (FAFULLFS archive) with LXGW WenKai (霞鹜文楷等宽) v1.530.

Supports:
  python tools/build_font_patch.py              # Default: Medium (500), matching PC version bold aesthetic & 720p legibility
  python tools/build_font_patch.py --weight regular  # Regular (400), for lighter stroke aesthetic
"""

import os
import io
import struct
import zipfile
import shutil
import argparse
from fontTools.ttLib import TTFont

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORKSPACE_DIR = os.environ.get("VILLAGE_WORKSPACE_DIR", os.path.join(REPO_ROOT, "workspace"))
ZIP_PATH = os.environ.get("LXGW_ZIP_PATH", r"D:\Download\lxgw-wenkai-v1.530.zip")
ORIG_MISC = os.environ.get("VILLAGE_MISC_SRC", os.path.join(REPO_ROOT, "unpacked", "romfs", "data", "misc_1_00.dat"))
OUT_MISC = os.environ.get("VILLAGE_MISC_DST", os.path.join(REPO_ROOT, "output", "atmosphere", "contents", "01001BA027DD8000", "romfs", "data", "misc_1_00.dat"))
EDEN_MISC = r"C:\Users\Admin\AppData\Roaming\eden\load\01001BA027DD8000\Village_SC_Translation\romfs\data\misc_1_00.dat"

def prepare_lxgw_font(raw_bytes, target_name="ResourceHan", style="Regular"):
    f = TTFont(io.BytesIO(raw_bytes))
    
    # Update name table for game compatibility
    for r in f['name'].names:
        enc = r.getEncoding()
        if target_name == "ResourceHan":
            if r.nameID == 1:
                r.string = "Resource Han Rounded TC".encode(enc)
            elif r.nameID == 2:
                r.string = "Regular".encode(enc)
            elif r.nameID == 4:
                r.string = f"Resource Han Rounded TC {style}".encode(enc)
            elif r.nameID == 6:
                r.string = f"Resource-Han-Rounded-TC-{style}".encode(enc)
        elif target_name == "LXGW":
            if r.nameID == 1:
                r.string = "LXGW WenKai Mono TC".encode(enc)
            elif r.nameID == 2:
                r.string = "Bold".encode(enc)
            elif r.nameID == 4:
                r.string = "LXGW WenKai Mono TC Bold".encode(enc)
            elif r.nameID == 6:
                r.string = "LXGWWenKaiMonoTC-Bold".encode(enc)
                
    out_buf = io.BytesIO()
    f.save(out_buf)
    return out_buf.getvalue()

def rebuild_misc_1_00(weight="medium"):
    if not os.path.exists(ZIP_PATH):
        if os.path.exists(OUT_MISC):
            print(f"LXGW font zip not found at {ZIP_PATH}, but existing built font patch found at {OUT_MISC}.")
            if os.path.exists(os.path.dirname(EDEN_MISC)):
                shutil.copy2(OUT_MISC, EDEN_MISC)
                print(f"  Synced existing misc_1_00.dat to Eden: {EDEN_MISC}")
            return
        raise FileNotFoundError(f"Cannot find font archive at {ZIP_PATH}")

    print(f"Loading fonts from {ZIP_PATH} (Selected primary weight: {weight})...")
    with zipfile.ZipFile(ZIP_PATH, 'r') as z:
        raw_reg = z.read("lxgw-wenkai-v1.530/LXGWWenKaiMono-Regular.ttf")
        raw_med = z.read("lxgw-wenkai-v1.530/LXGWWenKaiMono-Medium.ttf")
        
    primary_raw = raw_med if weight == "medium" else raw_reg
    primary_style = "Medium" if weight == "medium" else "Regular"
    
    font_reg_data = prepare_lxgw_font(primary_raw, target_name="ResourceHan", style=primary_style)
    font_med_data = prepare_lxgw_font(raw_med, target_name="ResourceHan", style="Medium")
    font_lxgw_bold_data = prepare_lxgw_font(raw_med, target_name="LXGW", style="Bold")
    
    print(f"  font_reg_data prepared: {len(font_reg_data)/1024/1024:.2f} MB")
    print(f"  font_med_data prepared: {len(font_med_data)/1024/1024:.2f} MB")
    print(f"  font_lxgw_bold_data prepared: {len(font_lxgw_bold_data)/1024/1024:.2f} MB")

    with open(ORIG_MISC, "rb") as f:
        orig_bytes = f.read()

    hdr = orig_bytes[:0x40]
    count, unk = struct.unpack_from("<II", hdr, 8)
    str_off, str_size, toc_off = struct.unpack_from("<QQQ", hdr, 0x10)

    str_pool = orig_bytes[str_off : str_off + str_size]
    toc = orig_bytes[toc_off : toc_off + count * 48]

    entries = []
    for i in range(count):
        name_hash, s_off, flags, f_size, f_off, ts = struct.unpack_from("<QQQQQQ", toc, i * 48)
        end = str_pool.find(b"\x00", s_off)
        rel_path = str_pool[s_off:end].decode("utf-8")
        
        if rel_path == "data/misc/resourcehanroundedtc-regular.ttf":
            data = font_reg_data
            print(f"  Replacing {rel_path}: {f_size} -> {len(data)} bytes")
        elif rel_path == "data/misc/resourcehanroundedtc-medium.ttf":
            data = font_med_data
            print(f"  Replacing {rel_path}: {f_size} -> {len(data)} bytes")
        elif rel_path == "data/misc/lxgwwenkaimonotc-bold.ttf":
            data = font_lxgw_bold_data
            print(f"  Replacing {rel_path}: {f_size} -> {len(data)} bytes")
        else:
            data = orig_bytes[f_off : f_off + f_size]

        entries.append({
            "hash": name_hash,
            "s_off": s_off,
            "flags": flags,
            "size": len(data),
            "orig_offset": f_off,
            "data": data,
            "ts": ts,
            "path": rel_path
        })

    sorted_files = sorted(entries, key=lambda x: x["orig_offset"])

    new_data = bytearray(0x200)
    for ent in sorted_files:
        if len(new_data) % 0x200 != 0:
            new_data.extend(b"\x00" * (0x200 - (len(new_data) % 0x200)))
        ent["new_offset"] = len(new_data)
        new_data.extend(ent["data"])

    if len(new_data) % 0x200 != 0:
        new_data.extend(b"\x00" * (0x200 - (len(new_data) % 0x200)))
    new_toc_off = len(new_data)

    entries.sort(key=lambda x: x["hash"])
    for ent in entries:
        new_data.extend(struct.pack("<QQQQQQ", ent["hash"], ent["s_off"], ent["flags"], len(ent["data"]), ent["new_offset"], ent["ts"]))

    new_str_off = len(new_data)
    new_data.extend(str_pool)

    struct.pack_into("<8sIIQQQ", new_data, 0, b"FAFULLFS", count, unk, new_str_off, len(str_pool), new_toc_off)

    os.makedirs(os.path.dirname(OUT_MISC), exist_ok=True)
    with open(OUT_MISC, "wb") as out_f:
        out_f.write(new_data)
    print(f"Successfully generated {OUT_MISC} ({len(new_data)/1024/1024:.2f} MB)")

    if os.path.exists(os.path.dirname(EDEN_MISC)):
        shutil.copyfile(OUT_MISC, EDEN_MISC)
        print(f"Successfully synced to Eden mod folder: {EDEN_MISC}")

def main():
    parser = argparse.ArgumentParser(description="Rebuild misc_1_00.dat with LXGW WenKai v1.530")
    parser.add_argument("--weight", choices=["medium", "regular"], default="medium",
                        help="Primary text weight: 'medium' (default, matches PC version bold) or 'regular'")
    args = parser.parse_args()
    rebuild_misc_1_00(weight=args.weight)

if __name__ == "__main__":
    main()
