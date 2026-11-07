import os
import shutil
from PIL import Image

def patch_nacp_file(nacp_path, title_sc="静谧田园", author="Clouded Leopard Entertainment Inc."):
    with open(nacp_path, "rb") as f:
        data = bytearray(f.read())
    
    if len(data) != 0x4000:
        raise ValueError(f"Invalid NACP size: {len(data)}, expected 0x4000")
        
    bak_path = nacp_path + ".bak"
    if not os.path.exists(bak_path):
        with open(bak_path, "wb") as f_bak:
            f_bak.write(data)
        print(f"Created backup: {bak_path}")
        
    title_bytes = title_sc.encode("utf-8")
    author_bytes = author.encode("utf-8")
    
    # Slot 13: TraditionalChinese (0x2700 - 0x2A00)
    # Slot 14: SimplifiedChinese (0x2A00 - 0x2D00)
    for slot_idx in [13, 14]:
        base_offset = slot_idx * 0x300
        # Clear title (512 bytes) and author (256 bytes)
        data[base_offset : base_offset + 0x300] = b"\x00" * 0x300
        # Write title
        data[base_offset : base_offset + len(title_bytes)] = title_bytes
        # Write author
        data[base_offset + 0x200 : base_offset + 0x200 + len(author_bytes)] = author_bytes
        
    with open(nacp_path, "wb") as f:
        f.write(data)
    print(f"Patched NACP: {nacp_path} (Slots 13 & 14 set to '{title_sc}' / '{author}')")

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    default_icon = os.path.join(repo_root, "switch_icons", "icon_SimplifiedChinese.png")
    icon_src = os.environ.get("VILLAGE_ICON_SRC", default_icon)
    if not os.path.exists(icon_src):
        dl_path = r"D:\Download\icon_sc.png"
        if os.path.exists(dl_path):
            icon_src = dl_path
        else:
            raise FileNotFoundError(f"Icon source not found: {icon_src}")
        
    print(f"[1/5] Loading user icon: {icon_src}")
    img = Image.open(icon_src).convert("RGB")
    if img.size != (256, 256):
        print(f"Warning: resizing from {img.size} to (256, 256)")
        img = img.resize((256, 256), Image.Resampling.LANCZOS)
        
    # Save temporary JPEG in memory / disk
    temp_jpeg = os.path.join(repo_root, "workspace", "temp_icon.jpg")
    img.save(temp_jpeg, "JPEG", quality=98)
    with open(temp_jpeg, "rb") as f:
        jpeg_bytes = f.read()
    print(f"Generated Switch icon JPEG: {len(jpeg_bytes)} bytes")
    
    # [2/5] Update unpacked/control_base
    print("\n[2/5] Updating unpacked/control_base...")
    base_dir = os.path.join(repo_root, "unpacked", "control_base")
    patch_nacp_file(os.path.join(base_dir, "control.nacp"))
    
    # Backup original icon if needed
    tc_icon_base = os.path.join(base_dir, "icon_TraditionalChinese.dat")
    if not os.path.exists(tc_icon_base + ".bak"):
        shutil.copyfile(tc_icon_base, tc_icon_base + ".bak")
    with open(tc_icon_base, "wb") as f:
        f.write(jpeg_bytes)
    with open(os.path.join(base_dir, "icon_SimplifiedChinese.dat"), "wb") as f:
        f.write(jpeg_bytes)
    print(f"Updated {tc_icon_base} & icon_SimplifiedChinese.dat")

    # [3/5] Update unpacked/control_update
    print("\n[3/5] Updating unpacked/control_update...")
    update_dir = os.path.join(repo_root, "unpacked", "control_update")
    patch_nacp_file(os.path.join(update_dir, "control.nacp"))
    
    tc_icon_update = os.path.join(update_dir, "icon_TraditionalChinese.dat")
    if not os.path.exists(tc_icon_update + ".bak"):
        shutil.copyfile(tc_icon_update, tc_icon_update + ".bak")
    with open(tc_icon_update, "wb") as f:
        f.write(jpeg_bytes)
    with open(os.path.join(update_dir, "icon_SimplifiedChinese.dat"), "wb") as f:
        f.write(jpeg_bytes)
    print(f"Updated {tc_icon_update} & icon_SimplifiedChinese.dat")

    # [4/5] Deploy to output/atmosphere/contents/01001BA027DD8000/
    print("\n[4/5] Deploying to Atmosphere output...")
    atm_dir = os.path.join(repo_root, "output", "atmosphere", "contents", "01001BA027DD8000")
    
    # 1. sys-tweak / sys-icon direct hook file: icon.jpg
    atm_icon_jpg = os.path.join(atm_dir, "icon.jpg")
    with open(atm_icon_jpg, "wb") as f:
        f.write(jpeg_bytes)
    print(f"Deployed sys-tweak icon: {atm_icon_jpg}")
    
    # 2. control/ subfolder for forwarders / loaders
    atm_control_dir = os.path.join(atm_dir, "control")
    os.makedirs(atm_control_dir, exist_ok=True)
    shutil.copyfile(os.path.join(update_dir, "control.nacp"), os.path.join(atm_control_dir, "control.nacp"))
    shutil.copyfile(tc_icon_update, os.path.join(atm_control_dir, "icon_TraditionalChinese.dat"))
    shutil.copyfile(os.path.join(update_dir, "icon_SimplifiedChinese.dat"), os.path.join(atm_control_dir, "icon_SimplifiedChinese.dat"))
    print(f"Deployed control metadata to: {atm_control_dir}")

    # [5/5] Update switch_icons preview directory
    print(f"\n[5/5] Updating preview folder {os.path.join(repo_root, 'switch_icons')}...")
    icons_dir = os.path.join(repo_root, "switch_icons")
    os.makedirs(icons_dir, exist_ok=True)
    
    img.save(os.path.join(icons_dir, "icon_SimplifiedChinese.png"), "PNG")
    with open(os.path.join(icons_dir, "icon_SimplifiedChinese.jpg"), "wb") as f:
        f.write(jpeg_bytes)
    img.save(os.path.join(icons_dir, "icon_TraditionalChinese.png"), "PNG")
    with open(os.path.join(icons_dir, "icon_TraditionalChinese.jpg"), "wb") as f:
        f.write(jpeg_bytes)
    print("Preview images updated successfully.")

if __name__ == "__main__":
    main()
