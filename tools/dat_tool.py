# -*- coding: utf-8 -*-
"""
Village in the Shade (ほの暮しの庭 / 靜謐田園) Database (.dat) Core Library
TitleID: 01001BA027DD8000 (v393216 / 1.2.0)

Provides 100% lossless parsing, 7-slot MultiLangString extraction, and
dynamic-offset string pool rebuilding for all 189 /data/database/*.dat files.
"""

import os
import struct
import hashlib

# The 37 human-readable localized database files in /data/database/
LOCALIZED_37_FILES = [
    "action.dat",
    "bgm.dat",
    "bundle.dat",
    "bundleGroup.dat",
    "character.dat",
    "cmd.dat",
    "construction.dat",
    "creature.dat",
    "credit.dat",
    "crops.dat",
    "facility.dat",
    "facilityRelease.dat",
    "framework_cmd.dat",
    "framework_credit.dat",
    "framework_string.dat",
    "framework_vkey.dat",
    "framework_vkeyCategory.dat",
    "gameEffect.dat",
    "gameSetting.dat",
    "intangeble.dat",
    "item.dat",
    "itemType.dat",
    "letter.dat",
    "livestock.dat",
    "logText.dat",
    "lostBook.dat",
    "quest.dat",
    "reminiscence.dat",
    "skillTree.dat",
    "string.dat",
    "talk.dat",
    "talkNameplate.dat",
    "tips.dat",
    "trophy.dat",
    "updateText.dat",
    "vkey.dat",
    "whistle.dat",
]


def get_pool_entries(spool: bytes):
    """Return ordered list of (byte_offset, byte_length) for every null-terminated string in spool."""
    entries = []
    pos = 0
    n = len(spool)
    while pos < n:
        end = spool.find(b"\x00", pos)
        if end == -1:
            break
        entries.append((pos, end - pos))
        pos = end + 1
    return entries


def parse_dat_bytes(data: bytes):
    """
    Parse a .dat binary file into its structural components:
      - cnt: record count
      - rsize: total record payload size
      - records: list of bytearray for each record's payload
      - rec_chains: list (per record) of [(off_in_rec, old_o, old_l, pool_idx), ...]
      - pool_strings: list of decoded UTF-8 strings in string pool order
      - multilang_slots: list of (rec_idx, field_idx, rec_id_str, tuple_of_7_pidx, tuple_of_7_off)
    """
    cnt, rsize, ssize = struct.unpack_from("<III", data, 0)
    str_base = 12 + cnt * 4 + rsize
    if str_base + ssize != len(data):
        raise ValueError(f"Header size mismatch: {str_base} + {ssize} != {len(data)}")

    spool = data[str_base:]
    pool_entries = get_pool_entries(spool)
    pool_map = {o: idx for idx, (o, l) in enumerate(pool_entries)}
    pool_set = set(pool_entries)
    pool_strings = [spool[o : o + l].decode("utf-8") for o, l in pool_entries]

    records = []
    rec_chains = []
    claimed_pidx = set()
    pos = 12

    for r in range(cnt):
        rlen = struct.unpack_from("<I", data, pos)[0]
        rec = bytearray(data[pos + 4 : pos + 4 + rlen])
        pos += 4 + rlen
        records.append(rec)
        if not pool_entries:
            rec_chains.append([])
            continue

        cands = []
        for off in range(0, rlen - 7, 4):
            o, l = struct.unpack_from("<II", rec, off)
            if (o, l) in pool_set and pool_map[o] not in claimed_pidx:
                cands.append((off, o, l, pool_map[o]))

        by_pidx = {}
        for off, o, l, pidx in cands:
            by_pidx.setdefault(pidx, []).append((off, o, l))

        best_chain = []
        visited = set()
        for pidx in sorted(by_pidx.keys()):
            if pidx in visited:
                continue
            chain = []
            curr_pidx = pidx
            last_off = -8
            while curr_pidx in by_pidx:
                valid_offs = [item for item in by_pidx[curr_pidx] if item[0] >= last_off + 8]
                if not valid_offs:
                    break
                chosen = valid_offs[0]
                chain.append((chosen[0], chosen[1], chosen[2], curr_pidx))
                visited.add(curr_pidx)
                last_off = chosen[0]
                curr_pidx += 1
            if len(chain) > len(best_chain):
                best_chain = chain

        rec_chains.append(best_chain)
        for _, _, _, pidx in best_chain:
            claimed_pidx.add(pidx)

    if len(claimed_pidx) != len(pool_entries):
        raise ValueError(f"String pool bijection failed: claimed {len(claimed_pidx)} / {len(pool_entries)}")

    multilang_slots = []
    for r, chain in enumerate(rec_chains):
        if not chain:
            continue
        first_str = pool_strings[chain[0][3]]
        rec_id = (
            first_str
            if (first_str and all(0x20 <= ord(c) < 0x7F for c in first_str))
            else f"REC_{r:04d}"
        )
        runs = [[chain[0]]]
        for item in chain[1:]:
            if item[0] == runs[-1][-1][0] + 8 and item[3] == runs[-1][-1][3] + 1:
                runs[-1].append(item)
            else:
                runs.append([item])

        f_idx = 0
        for run in runs:
            if len(run) >= 7:
                rem = len(run) % 7
                if rem in (0, 1, 2):
                    for k in range(rem, len(run), 7):
                        grp = run[k : k + 7]
                        if grp[2][2] == 0 and grp[3][2] == 0 and grp[6][2] == 0:
                            pidxs = tuple(x[3] for x in grp)
                            offs = tuple(x[0] for x in grp)
                            multilang_slots.append((r, f_idx, rec_id, pidxs, offs))
                            f_idx += 1

    return cnt, rsize, records, rec_chains, pool_strings, multilang_slots


def rebuild_dat_bytes(cnt: int, rsize: int, records: list, rec_chains: list, pool_strings: list) -> bytes:
    """
    Rebuild a .dat binary file from its parsed components and potentially modified pool_strings.
    Dynamically recalculates all (offset, length) pairs in every record and updates the 12-byte header.
    """
    encoded = [s.encode("utf-8") for s in pool_strings]
    new_offsets = []
    new_lengths = []
    curr_off = 0
    for b in encoded:
        new_offsets.append(curr_off)
        new_lengths.append(len(b))
        curr_off += len(b) + 1
    new_spool = b"\x00".join(encoded) + (b"\x00" if encoded else b"")
    assert len(new_spool) == curr_off

    out_parts = [struct.pack("<III", cnt, rsize, len(new_spool))]
    for r, rec in enumerate(records):
        rec_copy = bytearray(rec)
        for off_in_rec, old_o, old_l, pidx in rec_chains[r]:
            struct.pack_into("<II", rec_copy, off_in_rec, new_offsets[pidx], new_lengths[pidx])
        out_parts.append(struct.pack("<I", len(rec_copy)))
        out_parts.append(bytes(rec_copy))
    out_parts.append(new_spool)
    return b"".join(out_parts)
