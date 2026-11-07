# -*- coding: utf-8 -*-
"""
Village in the Shade (ほの暮しの庭 / 靜謐田園) Switch UI Texture Patch Builder
TitleID: 01001BA027DD8000 (v393216 / 1.2.0)

Reconstructs resident_lang_tc.fad inside fairy_1_00.dat:
- Full fix for P0-1: comp_sz = 20 + len(lz4_payload), matching Switch LZ4_decompress_safe convention
- Full fix for P0-2: upgrades descriptor q6 to 0x07 (BC3) and sets ints[5] = 0x800006
- Full fix for P0-3: dynamic Tegra Swizzle block height mode extraction (mode = ints[14] & 0xFF)
- Supports --mode all (Route B, 66 textures) and --mode safe (Route A, 5 native 0x07 textures)
"""

import os
import sys
import struct
import ctypes
import hashlib
import argparse
import pyswizzle

# Setup paths
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PC_FAIRY = os.environ.get("VILLAGE_PC_FAIRY", r"D:\GameLibrary\Village in the Shade\data\fairy_1_00.dat")
SW_FAIRY = os.environ.get("VILLAGE_SW_FAIRY", os.path.join(REPO_ROOT, "unpacked", "romfs", "data", "fairy_1_00.dat"))
LZ4_DLL_PATH = os.environ.get("VILLAGE_LZ4_DLL", r"D:\GameLibrary\Village in the Shade\lz4.dll")
OUTPUT_DIR = os.environ.get("VILLAGE_OUTPUT_DIR", os.path.join(REPO_ROOT, "output", "atmosphere", "contents", "01001BA027DD8000", "romfs", "data"))
OUTPUT_FAIRY = os.path.join(OUTPUT_DIR, "fairy_1_00.dat")

# Load lz4.dll
lz4_dll = ctypes.CDLL(LZ4_DLL_PATH)

LZ4_compress_default = lz4_dll.LZ4_compress_default
LZ4_compress_default.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
LZ4_compress_default.restype = ctypes.c_int

LZ4_compressBound = lz4_dll.LZ4_compressBound
LZ4_compressBound.argtypes = [ctypes.c_int]
LZ4_compressBound.restype = ctypes.c_int

LZ4_decompress_safe = lz4_dll.LZ4_decompress_safe
LZ4_decompress_safe.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
LZ4_decompress_safe.restype = ctypes.c_int


def decompress_ykcmp_u1_4(data: bytes, decomp_sz: int) -> bytes:
    out = bytearray(decomp_sz)
    out_pos = 0
    in_pos = 0
    in_len = len(data)

    while in_pos < in_len and out_pos < decomp_sz:
        b0 = data[in_pos]
        in_pos += 1

        if (b0 & 0x80) == 0:
            length = b0
            if length == 0:
                continue
            out[out_pos : out_pos + length] = data[in_pos : in_pos + length]
            in_pos += length
            out_pos += length
        elif (b0 & 0x40) == 0:
            length = ((b0 >> 4) & 3) + 1
            dist = (b0 & 0x0F) + 1
            src_pos = out_pos - dist
            for _ in range(length):
                out[out_pos] = out[src_pos]
                out_pos += 1
                src_pos += 1
        else:
            if (b0 & 0x20) == 0:
                b1 = data[in_pos]
                in_pos += 1
                length = (b0 & 0x1F) + 2
                dist = b1 + 1
                src_pos = out_pos - dist
                for _ in range(length):
                    out[out_pos] = out[src_pos]
                    out_pos += 1
                    src_pos += 1
            else:
                b1 = data[in_pos]
                b2 = data[in_pos + 1]
                in_pos += 2
                length = (((b0 & 0x1F) << 4) | (b1 >> 4)) + 3
                dist = (((b1 & 0x0F) << 8) | b2) + 1
                src_pos = out_pos - dist
                for _ in range(length):
                    out[out_pos] = out[src_pos]
                    out_pos += 1
                    src_pos += 1

    return bytes(out[:out_pos])


def get_file_from_fafullfs(dat_path, target_rel):
    with open(dat_path, "rb") as f:
        hdr = f.read(0x40)
        count = struct.unpack_from("<I", hdr, 8)[0]
        str_off, str_size, toc_off = struct.unpack_from("<QQQ", hdr, 0x10)
        f.seek(str_off)
        spool = f.read(str_size)
        f.seek(toc_off)
        toc = f.read(count * 48)
        for i in range(count):
            name_hash, s_off, flags, f_size, f_off, ts = struct.unpack_from("<QQQQQQ", toc, i * 48)
            end = spool.find(b"\x00", s_off)
            rel_path = spool[s_off:end].decode("utf-8", errors="ignore")
            if target_rel in rel_path:
                f.seek(f_off)
                return f.read(f_size)
    return None


def parse_all_tex_entries(fad_data):
    entries = []
    pos = 0
    while True:
        pos = fad_data.find(b"NMPLTEX1", pos)
        if pos == -1:
            break
        ints = struct.unpack_from("<32I", fad_data, pos)
        entries.append({
            "pos": pos,
            "w": ints[6],
            "h": ints[7],
            "fmt": ints[8],
            "decomp_sz": ints[11],
            "comp_sz": ints[12],
            "data_off": ints[13],
            "ints5": ints[5],
            "ints14": ints[14],
            "ints15": ints[15],
        })
        pos += 8
    return entries


def get_tga_names(data):
    end_tga = data.find(b"NMPLTEX1")
    chunk = data[end_tga - 0x10000 : end_tga]
    tgas = [s.decode("shift_jis", errors="ignore") for s in chunk.split(b"\x00") if s.endswith(b".tga")]
    return tgas


def sw_to_pc(sw_idx):
    if sw_idx < 106:
        return sw_idx
    elif sw_idx == 106:
        return 109
    elif sw_idx == 107:
        return 108
    elif sw_idx == 108:
        return 110
    elif sw_idx == 109:
        return 111
    else:
        return sw_idx + 2


def build_fairy_patch(mode="all"):
    print(f"=== Building fairy_1_00.dat Patch (Mode: {mode.upper()}) ===")
    print("[1/5] Loading archives...")
    sw_tc_fad = get_file_from_fafullfs(SW_FAIRY, "resident_lang_tc.fad")
    pc_tc_fad = get_file_from_fafullfs(PC_FAIRY, "resident_lang_tc.fad")
    pc_sc_fad = get_file_from_fafullfs(PC_FAIRY, "resident_lang_sc.fad")

    sw_tgas = get_tga_names(sw_tc_fad)
    sw_entries = parse_all_tex_entries(sw_tc_fad)
    pc_tc_entries = parse_all_tex_entries(pc_tc_fad)
    pc_sc_entries = parse_all_tex_entries(pc_sc_fad)

    print(f"Loaded: SW={len(sw_entries)} texs, PC TC={len(pc_tc_entries)} texs, PC SC={len(pc_sc_entries)} texs")

    # Native 0x07 textures (Route A targets)
    SAFE_TARGETS = {153, 154, 155, 156, 209}

    print("[2/5] Preparing replacement textures...")
    replace_map = {}

    for sw_idx in range(len(sw_tgas)):
        if mode == "safe" and sw_idx not in SAFE_TARGETS:
            continue

        pc_idx = sw_to_pc(sw_idx)
        sw_e = sw_entries[sw_idx]
        pc_tc_e = pc_tc_entries[pc_idx]
        pc_sc_e = pc_sc_entries[pc_idx]

        pc_tc_payload = pc_tc_fad[pc_tc_e["pos"] + pc_tc_e["data_off"] : pc_tc_e["pos"] + pc_tc_e["data_off"] + pc_tc_e["comp_sz"] + 20]
        pc_sc_payload = pc_sc_fad[pc_sc_e["pos"] + pc_sc_e["data_off"] : pc_sc_e["pos"] + pc_sc_e["data_off"] + pc_sc_e["comp_sz"] + 20]

        if pc_tc_payload == pc_sc_payload:
            continue

        if sw_e["w"] != pc_sc_e["w"] or sw_e["h"] != pc_sc_e["h"]:
            print(f"  Skipping #{sw_idx} {sw_tgas[sw_idx]}: dim mismatch")
            continue

        w, h = sw_e["w"], sw_e["h"]

        # 2200x1300 and 256x16 are non-POT background art/dividers
        if (w, h) in [(2200, 1300), (256, 16)]:
            print(f"  Skipping non-POT #{sw_idx} {sw_tgas[sw_idx]} ({w}x{h})")
            continue

        # 1. Decompress PC SC BC3
        pc_sc_bc3 = decompress_ykcmp_u1_4(pc_sc_payload[20:], pc_sc_e["decomp_sz"])
        assert len(pc_sc_bc3) == pc_sc_e["decomp_sz"]

        # 2. Dynamic Tegra Swizzle block height mode
        sw_mode = sw_e["ints14"] & 0xFF
        swz = bytes(pyswizzle.nsw_swizzle(pc_sc_bc3, (w, h), (4, 4), 16, sw_mode))
        assert len(swz) == len(pc_sc_bc3)

        # 3. Compress with LZ4 default
        bound = LZ4_compressBound(len(swz))
        comp_buf = ctypes.create_string_buffer(bound)
        comp_raw_sz = LZ4_compress_default(swz, comp_buf, len(swz), bound)
        comp_payload = comp_buf.raw[:comp_raw_sz]

        # 4. Strict verify: decompress with LZ4_decompress_safe matching Switch engine convention
        dec_buf = ctypes.create_string_buffer(len(swz))
        ret = LZ4_decompress_safe(comp_payload, dec_buf, comp_raw_sz, len(swz))
        assert ret == len(swz), f"Decompression failed on #{sw_idx} {sw_tgas[sw_idx]}"
        assert dec_buf.raw == swz

        # 5. Build YKCMP_V1 container
        # CRITICAL P0-1 FIX: comp_sz in Switch YKCMP and NMPLTEX1 ints[12] must include the 20-byte YKCMP header!
        yk_comp_sz = 20 + comp_raw_sz
        yk_decomp_sz = len(swz)
        yk_hdr = struct.pack("<8sIII", b"YKCMP_V1", 9, yk_comp_sz, yk_decomp_sz)
        new_ykcmp_chunk = yk_hdr + comp_payload

        replace_map[sw_idx] = {
            "ykcmp_chunk": new_ykcmp_chunk,
            "yk_comp_sz": yk_comp_sz,
            "decomp_sz": yk_decomp_sz,
            "name": sw_tgas[sw_idx],
            "w": w,
            "h": h,
            "mode": sw_mode,
            "orig_ints14": sw_e["ints14"],
        }

    print(f"Total textures to replace: {len(replace_map)}")

    print("[3/5] Reconstructing resident_lang_tc.fad...")
    FIRST_DESC_POS = 0x33FB60
    table_base = 0xd00
    prefix = bytearray(sw_tc_fad[:FIRST_DESC_POS])

    new_blocks = []
    current_offset = FIRST_DESC_POS
    desc_pos = FIRST_DESC_POS
    new_steps = []

    for i in range(411):
        orig_desc_raw = sw_tc_fad[desc_pos : desc_pos + 64]
        orig_desc_ints = struct.unpack_from("<16I", orig_desc_raw, 0)
        orig_step = orig_desc_ints[2]
        orig_nmpl_sz = orig_desc_ints[8]

        orig_nmpl_pos = desc_pos + 64
        orig_nmpl_hdr = bytearray(sw_tc_fad[orig_nmpl_pos : orig_nmpl_pos + 128])

        # CRITICAL P0-4 FIX: Synchronize Master Texture Table entry offset at 0xd00 + i * 32!
        struct.pack_into("<I", prefix, table_base + i * 32, current_offset)

        if i in replace_map:
            rep = replace_map[i]
            new_comp_sz = rep["yk_comp_sz"]
            new_decomp_sz = rep["decomp_sz"]
            new_ykcmp = rep["ykcmp_chunk"]

            # CRITICAL P0-2 FIX: update NMPLTEX1 header
            # ints[5] = 0x800006 (BC3 format flag)
            # ints[11] = decomp_sz (w * h)
            # ints[12] = yk_comp_sz (20 + lz4_len)
            struct.pack_into("<I", orig_nmpl_hdr, 20, 0x800006)
            struct.pack_into("<I", orig_nmpl_hdr, 44, new_decomp_sz)
            struct.pack_into("<I", orig_nmpl_hdr, 48, new_comp_sz)

            # calculate new nmpl_sz and step
            new_nmpl_sz = 128 + len(new_ykcmp)
            new_step = (64 + new_nmpl_sz + 15) & ~15
            pad_len = new_step - (64 + new_nmpl_sz)

            # CRITICAL P0-2 FIX: update 64-byte descriptor
            # QWORD 1 = new_step
            # QWORD 4 = new_nmpl_sz
            # QWORD 5 = (h << 16) | w
            # QWORD 6 = (((h << 16) | w) << 32) | 0x07050080 (BC3 format flag)
            new_desc_qwords = list(struct.unpack_from("<8Q", orig_desc_raw, 0))
            new_desc_qwords[1] = new_step
            new_desc_qwords[4] = new_nmpl_sz
            new_desc_qwords[5] = (rep["h"] << 16) | rep["w"]
            new_desc_qwords[6] = (((rep["h"] << 16) | rep["w"]) << 32) | 0x07050080
            new_desc_raw = struct.pack("<8Q", *new_desc_qwords)

            block = new_desc_raw + bytes(orig_nmpl_hdr) + new_ykcmp + (b"\x00" * pad_len)
            assert len(block) == new_step
            new_blocks.append(block)
            new_steps.append(new_step)
            current_offset += new_step
        else:
            # Keep original chunk intact
            block = sw_tc_fad[desc_pos : desc_pos + orig_step]
            new_blocks.append(block)
            new_steps.append(orig_step)
            current_offset += orig_step

        desc_pos += orig_step

    # CRITICAL P0-4 FIX: Synchronize Master Texture Table field 6 (step of entry i+1)!
    for i in range(410):
        struct.pack_into("<I", prefix, table_base + i * 32 + 24, new_steps[i + 1])

    new_fad_bytes = bytes(prefix) + b"".join(new_blocks)
    print(f"Reconstructed FAD size: {len(new_fad_bytes)} bytes ({len(new_fad_bytes)/(1024*1024):.2f} MB)")
    print(f"Original      FAD size: {len(sw_tc_fad)} bytes ({len(sw_tc_fad)/(1024*1024):.2f} MB)")

    # Strict Ground-Truth Verification
    print("[4/5] Verifying reconstructed resident_lang_tc.fad against Switch engine conventions...")
    test_desc_pos = FIRST_DESC_POS
    verified_reps = 0
    for i in range(411):
        # Verify Master Table offset points directly to descriptor i
        table_ptr = struct.unpack_from("<I", new_fad_bytes, table_base + i * 32)[0]
        assert table_ptr == test_desc_pos, f"Master table ptr mismatch for #{i}: {hex(table_ptr)} != {hex(test_desc_pos)}"
        if i < 410:
            table_f6 = struct.unpack_from("<I", new_fad_bytes, table_base + i * 32 + 24)[0]
            assert table_f6 == new_steps[i + 1], f"Master table f6 mismatch for #{i}: {hex(table_f6)} != {hex(new_steps[i+1])}"

        desc_q = struct.unpack_from("<8Q", new_fad_bytes, test_desc_pos)
        step = desc_q[1]
        nmpl_sz = desc_q[4]
        nmpl_pos = test_desc_pos + 64
        assert new_fad_bytes[nmpl_pos : nmpl_pos + 8] == b"NMPLTEX1", f"Tex #{i} magic mismatch!"

        nmpl_ints = struct.unpack_from("<32I", new_fad_bytes, nmpl_pos)
        i11 = nmpl_ints[11]
        i12 = nmpl_ints[12]

        assert nmpl_sz == 128 + i12, f"Tex #{i} nmpl_sz mismatch! {nmpl_sz} vs {128 + i12}"

        yk_pos = nmpl_pos + 128
        magic, u1, c_sz, d_sz = struct.unpack_from("<8sIII", new_fad_bytes, yk_pos)
        assert magic == b"YKCMP_V1", f"Tex #{i} YKCMP magic mismatch!"
        assert c_sz == i12, f"Tex #{i} c_sz {c_sz} != ints12 {i12}!"
        assert d_sz == i11, f"Tex #{i} d_sz {d_sz} != ints11 {i11}!"

        if i in replace_map:
            rep = replace_map[i]
            assert c_sz == rep["yk_comp_sz"]
            assert d_sz == rep["decomp_sz"]

            # Emulate game engine call: LZ4_decompress_safe(src+20, comp_sz-20)
            src_payload = new_fad_bytes[yk_pos + 20 : yk_pos + c_sz]
            assert len(src_payload) == c_sz - 20
            out_buf = ctypes.create_string_buffer(d_sz)
            ret = LZ4_decompress_safe(src_payload, out_buf, len(src_payload), d_sz)
            assert ret == d_sz, f"Tex #{i} safe decompress failed: ret={ret} expected={d_sz}"

            # Verify deswizzled data
            deswz = bytes(pyswizzle.nsw_deswizzle(out_buf.raw, (rep["w"], rep["h"]), (4, 4), 16, rep["mode"]))
            verified_reps += 1

        test_desc_pos += step

    print(f"FAD verification 100% SUCCESS! All 411 descriptors valid, {verified_reps} replaced textures verified with LZ4_decompress_safe & deswizzle!")

    print("[5/5] Repacking fairy_1_00.dat...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(SW_FAIRY, "rb") as f_in:
        orig_hdr = f_in.read(0x40)
        count = struct.unpack_from("<I", orig_hdr, 8)[0]
        orig_str_off, orig_str_size, orig_toc_off = struct.unpack_from("<QQQ", orig_hdr, 0x10)
        f_in.seek(orig_str_off)
        spool = f_in.read(orig_str_size)
        f_in.seek(orig_toc_off)
        toc_raw = f_in.read(count * 48)

        toc_entries = []
        for i in range(count):
            name_hash, s_off, flags, f_size, f_off, ts = struct.unpack_from("<QQQQQQ", toc_raw, i * 48)
            toc_entries.append({
                "idx": i,
                "name_hash": name_hash,
                "s_off": s_off,
                "flags": flags,
                "f_size": f_size,
                "f_off": f_off,
                "ts": ts,
            })

        TARGET_START_OFF = 0x3CC0AA00
        f_in.seek(0)
        prefix_data = f_in.read(TARGET_START_OFF)

    with open(OUTPUT_FAIRY, "wb") as f_out:
        # 1. Write prefix data (files 0..7)
        f_out.write(prefix_data)

        # 2. Write new resident_lang_tc.fad at TARGET_START_OFF
        tc_start_off = f_out.tell()
        assert tc_start_off == TARGET_START_OFF
        f_out.write(new_fad_bytes)

        # 3. Pad to 512 bytes (0x200)
        cur_pos = f_out.tell()
        pad_to_512 = (cur_pos + 511) & ~511
        if pad_to_512 > cur_pos:
            f_out.write(b"\x00" * (pad_to_512 - cur_pos))

        # 4. Write TOC
        new_toc_off = f_out.tell()
        new_toc_parts = []
        for e in toc_entries:
            if e["idx"] == 3:  # resident_lang_tc.fad
                new_entry = struct.pack("<QQQQQQ", e["name_hash"], e["s_off"], e["flags"], len(new_fad_bytes), tc_start_off, e["ts"])
            else:
                new_entry = struct.pack("<QQQQQQ", e["name_hash"], e["s_off"], e["flags"], e["f_size"], e["f_off"], e["ts"])
            new_toc_parts.append(new_entry)
        f_out.write(b"".join(new_toc_parts))

        # 5. Write String Pool
        new_str_off = f_out.tell()
        f_out.write(spool)

        total_fairy_sz = f_out.tell()

        # 6. Rewrite 0x40 header
        f_out.seek(0)
        new_hdr = bytearray(orig_hdr)
        struct.pack_into("<QQQ", new_hdr, 0x10, new_str_off, orig_str_size, new_toc_off)
        f_out.write(new_hdr)

    print("\n==========================================")
    print("SUCCESS! Repacked fairy_1_00.dat generated:")
    print(f"  Path: {OUTPUT_FAIRY}")
    print(f"  Size: {total_fairy_sz} bytes ({total_fairy_sz / (1024*1024*1024):.3f} GB)")
    print(f"  Replaced textures: {len(replace_map)} (Mode: {mode.upper()})")
    print("==========================================")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Village in the Shade Switch UI Texture Patch Builder")
    parser.add_argument("--mode", choices=["all", "safe"], default="all",
                        help="'all' (Route B: 66 textures upgraded to BC3) or 'safe' (Route A: 5 native 0x07 textures)")
    args = parser.parse_args()
    build_fairy_patch(mode=args.mode)
