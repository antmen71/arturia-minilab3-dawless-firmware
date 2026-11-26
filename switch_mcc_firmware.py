"""
Arturia MiniLab 3 — Custom Firmware Switcher for MIDI Control Center (MCC)
Usage:
    python switch_mcc_firmware.py live8     # Stage FW1: OTF Live 8-Step (+ Black Knob BPM)
    python switch_mcc_firmware.py pro64     # Stage FW2: OTF Pro 64-Step Groovebox (+ Riser/Drop Deck on Bank B)
    python switch_mcc_firmware.py drop      # Stage FW3: Dawless Kick, Riser & Drop Commander (Merged M1+M2 Kick Kill!)
    python switch_mcc_firmware.py factory   # Stage Original Arturia Factory 1.2.0
    python switch_mcc_firmware.py status    # Check which firmware is currently staged in MCC
"""
import hashlib
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MCC_FW_PATH = r"C:\ProgramData\Arturia\MIDI Control Center\Firmware\minilab-3_Firmware_Update_1.2.0.mnl3"

TARGETS = {
    "live8": (
        "FW1 — OTF Live 8-Step (2-Line OLED + Direct Pad 5/6 Stop/Start + Black Knob BPM)",
        os.path.join(HERE, "minilab-3_Firmware_Update_1.2.0_OTF_Live_8Step.mnl3"),
    ),
    "pro64": (
        "FW2 — OTF Pro 64-Step Groovebox (+ Pattern Chain + Bank B Riser & Drop Deck)",
        os.path.join(HERE, "minilab-3_Firmware_Update_1.2.0_OTF_Pro_64Step.mnl3"),
    ),
    "drop": (
        "FW3 — Dawless Kick, Riser & Drop Commander (+ Live PC/DIN Sync Delay Queue)",
        os.path.join(HERE, "minilab-3_Firmware_Update_1.2.0_Dawless_Drop_Commander.mnl3"),
    ),
    "drop_mioxm": (
        "FW3 (Pure Zero-Delay Backup for mioXM / Hardware Splitter — DK_MAGIC=0xDD)",
        os.path.join(HERE, "minilab-3_Firmware_Update_1.2.0_Dawless_Drop_Commander_NO_DELAY_mioXM.mnl3"),
    ),
    "factory": (
        "Original Arturia Factory v1.2.0.1466",
        os.path.join(HERE, "minilab-3_Firmware_Update_1.2.0_FACTORY_BACKUP.mnl3"),
    ),
}

def sha256_of(path):
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def show_status():
    cur_hash = sha256_of(MCC_FW_PATH)
    print("=== MiniLab 3 Firmware Files ===")
    matched = None
    for key, (desc, path) in TARGETS.items():
        fh = sha256_of(path)
        size = os.path.getsize(path) if fh else 0
        is_active = (fh is not None and fh == cur_hash)
        if is_active:
            matched = f"{key} ({desc})"
        mark = "  [STAGED IN MCC]" if is_active else ""
        print(f"  - {key:8s}: {os.path.basename(path)} ({size:,} bytes){mark}")
    print(f"\nMCC Cache Path: {MCC_FW_PATH}")
    if cur_hash is None:
        print("Current MCC Cache: (file not present)")
    elif matched:
        print(f"Currently Staged : {matched}")
    else:
        print("Currently Staged : Other / Previous build")

def main():
    if len(sys.argv) < 2 or sys.argv[1].lower() in ("status", "-h", "--help"):
        show_status()
        print("\nTip: In MIDI Control Center, you can ALSO click 'Firmware Revision -> Upgrade'")
        print("and directly select either .mnl3 file from this folder at any time!")
        return

    choice = sys.argv[1].lower()
    if choice not in TARGETS:
        print(f"Unknown option '{choice}'. Choose one of: {', '.join(TARGETS.keys())}, status")
        sys.exit(1)

    desc, src = TARGETS[choice]
    if not os.path.exists(src):
        print(f"Error: Firmware file not found: {src}")
        sys.exit(1)

    os.makedirs(os.path.dirname(MCC_FW_PATH), exist_ok=True)
    shutil.copy2(src, MCC_FW_PATH)
    print(f"Staged -> {desc}")
    print(f"Copied : {src}\n    ->   {MCC_FW_PATH}")

if __name__ == "__main__":
    main()
