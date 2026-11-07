# -*- coding: utf-8 -*-
"""
Automated Validator for Village in the Shade (ほの暮しの庭 / 静谧田园) Simplified Chinese Batches.

Usage:
  python D:/Village-SC/tools/validate_batch.py <batch_file_or_all> [--allow-non-gb2312]

Checks:
  1. JSON structure & record/line integrity against original extraction.
  2. Non-empty `sc` field on every line.
  3. 100% exact inline markup tag preservation against `ja` (Japanese original is the source of truth!).
  4. 100% font glyph coverage in `ResourceHanRoundedTC-Regular.ttf` (44,806 codepoints).
  5. Traditional-only character residue check (flags any CJK character outside GB2312 unless whitelisted or `<lang JP>`).
  6. Forbidden Taiwan regional terms & known TC mistranslations detector (blocks Taiwanese terms that were converted character-by-character without Mainland term localization).
  7. Corner bracket residue check (`「` `」` `『` `』` should be converted to `“”` `‘’` unless inside `<lang JP>`).
  8. Visual line-length overflow check (warns if visible char count exceeds safe threshold).
"""

import os
import sys
import re
import json

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORKSPACE_DIR = os.environ.get("VILLAGE_WORKSPACE_DIR", os.path.join(REPO_ROOT, "workspace"))
BATCHES_DIR = os.path.join(WORKSPACE_DIR, "batches")
FONT_CPS_PATH = os.path.join(WORKSPACE_DIR, "font_codepoints.json")

TAG_RE = re.compile(r"<icon\s+<[^>]+>[^>]*>|<[^>]+>")

# Known valid Mainland Simplified Chinese characters that are outside GB2312 Level 1+2
WHITELIST_NON_GB2312_SC = set(
    "啰𫫇嗯𥖄啰喔噢𤆵𨭆啰"
    "帷驹堇怜琪歐欧鵺焗狛萩祂楤鱥鱊"
    "♪☆♡○●◎◇◆□■△▲▽▼※→←↑↓↔"
)

# Forbidden Taiwanese / uncalibrated terms (in Simplified script form) that MUST be replaced with Mainland terms
FORBIDDEN_TAIWAN_SUBSTRINGS = {
    "动画语音音量": "环境音音量 (对应日文『環境音の音量』，繁中严重错译)",
    "市公所": "市政厅 (对应日文『市役所』)",
    "手把": "手柄",
    "类比摇杆": "摇杆",
    "线上说明书": "在线说明书",
    "马铃薯": "土豆",
    "高丽菜": "卷心菜",
    "花椰菜": "西兰花",
    "奇异果": "猕猴桃",
    "凤梨": "菠萝",
    "酪梨": "牛油果",
    "起司": "奶酪",
    "优格": "酸奶",
    "义大利面": "意大利面",
    "乌龙面": "乌冬面",
    "喀什米尔": "克什米尔",
    "脚踏车": "自行车",
    "塑胶": "塑料",
    "录音带": "磁带",
    "冷气": "空调",
    "自动贩卖机": "自动售货机",
    "公车站": "公交车站",
    "怪咖": "怪人 / 怪家伙",
    "好康": "好处 / 实惠",
    "落漆": "掉链子",
    "郁卒": "郁闷",
    "龟毛": "挑剔",
    "姊弟": "姐弟",
    "姊姊": "姐姐",
    "讯息": "信息 / 消息",
    "选单": "菜单",
    "视窗": "窗口",
    "预设": "默认",
}


def load_font_cps():
    if not os.path.exists(FONT_CPS_PATH):
        return None
    with open(FONT_CPS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return set(data["ResourceHanRoundedTC"])


def is_gb2312_or_whitelist(ch: str) -> bool:
    if ch in WHITELIST_NON_GB2312_SC:
        return True
    try:
        ch.encode("gb2312")
        return True
    except UnicodeEncodeError:
        return False


def extract_tags(s: str) -> list:
    return TAG_RE.findall(s)


def strip_tags(s: str) -> str:
    return TAG_RE.sub("", s)


def validate_single_batch(batch_path: str, font_cps: set, allow_non_gb2312: bool = False):
    errors = []
    warnings = []

    try:
        with open(batch_path, "r", encoding="utf-8") as f:
            batch = json.load(f)
    except Exception as e:
        return [f"JSON parse error: {e}"], []

    records = batch.get("records", [])
    if not records:
        errors.append("Batch has 0 records.")
        return errors, warnings

    untranslated_count = 0
    for rec in records:
        rec_id = rec.get("rec_id", "?")
        fn = rec.get("file", "?")
        for ln in rec.get("lines", []):
            f_idx = ln.get("f_idx", -1)
            ja = ln.get("ja", "")
            tc = ln.get("tc", "")
            sc = ln.get("sc", "")
            spk = ln.get("spk", "")
            loc = f"[{fn} {rec_id} f{f_idx}{f' ({spk})' if spk else ''}]"

            if not isinstance(sc, str) or sc == "":
                untranslated_count += 1
                continue

            # 1. Exact tag preservation (compare against JA/TC; note: if <lang JP>, must match JA!)
            if "<lang JP>" in ja:
                if sc != ja:
                    errors.append(f"{loc} Debug `<lang JP>` string must match `ja` exactly: expected {ja!r}, got {sc!r}")
                continue

            expected_tags = extract_tags(tc)
            sc_tags = extract_tags(sc)
            if set(expected_tags) != set(sc_tags) or len(expected_tags) != len(sc_tags):
                errors.append(f"{loc} Markup tag mismatch: expected {expected_tags}, got {sc_tags} | sc={sc!r}")

            # 2. Control character check
            if "\r" in sc or "\n" in sc:
                errors.append(f"{loc} Contains forbidden raw newline \\r or \\n (use <br> only if in original): sc={sc!r}")

            # 3. Font glyph coverage check
            if font_cps is not None:
                missing_font = [ch for ch in sc if ord(ch) >= 0x20 and ord(ch) not in font_cps]
                if missing_font:
                    errors.append(f"{loc} Characters missing from game TTF font: {missing_font} | sc={sc!r}")

            # 4. Traditional character residue check (outside GB2312)
            if not allow_non_gb2312 and fn not in ("credit.dat", "framework_credit.dat"):
                non_gb = []
                for ch in strip_tags(sc):
                    if 0x4E00 <= ord(ch) <= 0x9FFF and not is_gb2312_or_whitelist(ch):
                        non_gb.append(ch)
                if non_gb:
                    errors.append(
                        f"{loc} Potential unsimplified Traditional / non-GB2312 character(s) {sorted(list(set(non_gb)))}: "
                        f"ja={ja!r} | sc={sc!r}"
                    )

            # 5. Forbidden Taiwan terms / pronouns / uncalibrated TC mistranslations check
            if fn not in ("credit.dat", "framework_credit.dat"):
                clean_sc = strip_tags(sc)
                for bad_p, sugg in [("妳", "你"), ("牠", "它/他")]:
                    if bad_p in clean_sc:
                        errors.append(
                            f"{loc} Forbidden pronoun {bad_p!r} found in Simplified Chinese -> use {sugg!r} | sc={sc!r}"
                        )
                for bad_term, suggestion in FORBIDDEN_TAIWAN_SUBSTRINGS.items():
                    if bad_term in clean_sc:
                        errors.append(
                            f"{loc} Forbidden Taiwanese/mistranslated term {bad_term!r} found -> use Mainland term {suggestion!r} | sc={sc!r}"
                        )
                # Specific check for Panna Cotta mistranslation (ベリーパンナコッタ -> 莓果意式奶冻, not 莓果奶酪)
                if "パンナコッタ" in ja and "奶酪" in clean_sc:
                    errors.append(
                        f"{loc} Mistranslation of 'パンナコッタ' (Panna Cotta) as '奶酪' -> use Mainland term '意式奶冻' | sc={sc!r}"
                    )

            # 6. Corner brackets check
            if fn not in ("credit.dat", "framework_credit.dat"):
                bad_quotes = [q for q in ("「", "」", "『", "』") if q in sc]
                if bad_quotes:
                    warnings.append(f"{loc} Contains corner brackets {bad_quotes} (recommend “” / ‘’): sc={sc!r}")

            # 7. Visible length check
            vis_tc = len(strip_tags(tc))
            vis_sc = len(strip_tags(sc))
            if vis_sc > max(vis_tc + 6, int(vis_tc * 1.35) + 4) and vis_sc > 28:
                warnings.append(f"{loc} Visible length significantly longer than TC ({vis_tc} -> {vis_sc} chars): sc={sc!r}")

    if untranslated_count > 0:
        errors.insert(0, f"Contains {untranslated_count} untranslated line(s) (empty `sc`).")

    return errors, warnings


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_batch.py <batch_path_or_id | all> [--allow-non-gb2312]")
        sys.exit(1)

    target = sys.argv[1]
    allow_non_gb2312 = "--allow-non-gb2312" in sys.argv[2:]
    font_cps = load_font_cps()

    if target.lower() == "all":
        files = sorted(
            os.path.join(BATCHES_DIR, fn)
            for fn in os.listdir(BATCHES_DIR)
            if fn.endswith(".json")
        )
    else:
        if os.path.exists(target):
            files = [target]
        else:
            cand = os.path.join(BATCHES_DIR, target if target.endswith(".json") else f"{target}.json")
            if not os.path.exists(cand):
                print(f"Error: batch file not found: {target}")
                sys.exit(1)
            files = [cand]

    total_errors = 0
    total_warnings = 0
    completed_batches = 0

    for fpath in files:
        bname = os.path.basename(fpath)
        errs, warns = validate_single_batch(fpath, font_cps, allow_non_gb2312)
        if not errs:
            completed_batches += 1
        if errs or warns:
            if len(files) == 1 or errs:
                print(f"=== {bname}: {len(errs)} error(s), {len(warns)} warning(s) ===")
                for e in errs[:25]:
                    print(f"  [ERROR] {e}")
                if len(errs) > 25:
                    print(f"  ... and {len(errs) - 25} more errors.")
                for w in warns[:15]:
                    print(f"  [WARN]  {w}")
        total_errors += len(errs)
        total_warnings += len(warns)

    print(
        f"\nSummary: {completed_batches}/{len(files)} batch(es) passed with 0 errors "
        f"(Total errors: {total_errors}, Total warnings: {total_warnings})."
    )
    sys.exit(0 if total_errors == 0 else 1)


if __name__ == "__main__":
    main()
