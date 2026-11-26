# Arturia MiniLab 3 — Standalone Dawless Custom Firmware Suite (`STM32G0B1`)

Custom bare-metal **ARM Cortex-M0+ (`STM32G0B1`) Thumb-1** firmware suite that transforms the **Arturia MiniLab 3** (`v1.2.0.1466`) from a passive DAW MIDI controller into a **100% standalone DAWless Master Clock, Dual-Target Drum/Kick & Auto-Fill Sequencer, Scale/Melody Generator, and Live Riser/Drop Macro Commander** — with full 2-line non-blocking `128x64` OLED feedback, RGB pad animations, and persistent STM32 Flash storage.

---

## Included Firmware Builds

| Target Key | Firmware Package (`.mnl3`) | Builder Script | Flash Page | Highlights |
| :--- | :--- | :--- | :---: | :--- |
| **`drop`** *(Latest)* | `minilab-3_Firmware_Update_1.2.0_Dawless_Drop_Commander.mnl3` | `build_fw3_drop_kick.py` | `0x0803A000` | **FW3 (`DK_MAGIC = 0xDE`):** Atomic `24 PPQN` Master Clock, Dual `SH-4d (Ch 5)` + `Donner D1 (Ch 10)` 16-Step Kick Sequencer, `Donner D1` Bar-End Step-1 Lock (`Pad 6`), 16,000+ Generative Drum Auto-Fills (`Pad 5`), Pure `RC-505mkII` 4/8-Bar Auto-Riser & Wobble/Slicer (`Pads 3, 7, 8` + `Hold+Pad 8` Sound Reset), Live 16th Scale/Melody Gen (`Knob 6`), Per-Channel Random Stereo Pan (`Knob 7`) & Step Probability (`Knob 8`), and Microsecond `0–60 ms` 5-Pin DIN Sync Delay Queue (boot default `0 ms`). |
| **`drop_mioxm`** | `minilab-3_Firmware_Update_1.2.0_Dawless_Drop_Commander_NO_DELAY_mioXM.mnl3` | `build_fw3_drop_kick_no_delay_backup.py` | `0x0803A000` | **FW3 Pure Zero-Delay Backup (`DK_MAGIC = 0xDD`):** Untouched hardware-splitter / `iConnectivity mioXM` edition prior to the DIN Sync Delay Queue. |
| **`pro64`** | `minilab-3_Firmware_Update_1.2.0_OTF_Pro_64Step.mnl3` | `build_fw2_pro64.py` | `0x0803A800` | **FW2:** 64-Step *On The Run* / 303 Acid Groovebox Sequencer (per-step pitch, octave, gate/mute, probability, 303 slide/accent, pattern chaining, Flash save, plus Bank B Riser & Drop Deck). |
| **`live8`** | `minilab-3_Firmware_Update_1.2.0_OTF_Live_8Step.mnl3` | `build_fw1_live8.py` | — | **FW1:** Hands-on 8-Knob Live Step Sequencer (`Knobs 1–8` = direct step pitch/expression, `Faders 1–3` = Scale / Direction / Step Length, `Black Knob` = live Master BPM). |
| **`factory`** | `minilab-3_Firmware_Update_1.2.0_FACTORY_BACKUP.mnl3` | *(Unmodified Arturia v1.2.0)* | — | Original unmodified Arturia MiniLab 3 Factory Firmware v1.2.0.1466 (`fw_1`) + v1.2.0.1037 (`fw_2`) for instant 1-click factory restore. |

---

## FW3 (`Dawless Kick, Riser & Drop Commander`) Hardware Map

### MIDI Channel & Parameter Architecture
* **Global Clock & Transport:** Atomic rollover-safe `24 PPQN` MIDI Clock (`0xF8`), Start (`0xFA`), and Bar-End Quantized Stop (`0xFC` after the exact 96th tick so `Donner Essential D1` always parks on `Step 1.1`).
* **`Ch 1–4` → Roland SH-4d (Synth Parts 1–4):**
  * `CC#11` (`0–127`): Auto Sidechain Pump (`Fader 3`), Step Probability gate (`Knob 8`), & Slicer engine
  * `CC#10` (`0–127`): 16th-step LFSR Random Stereo Pan (`Knob 7`, auto-centers to `64` on Drop/Stop/0%)
  * `CC#123` (`0`): Pre-Drop Vacuum All Notes Off (`Pad 4`)
  * Live 16th-note Scale/Melody Generator (`Knob 6`, 7 scales, `Hold + Knob 6` Root `24–72`, `Main Knob + Knob 6/7/8` `SKIP Beat 1` / `PLAY Beat 1`)
* **`Ch 5` → Roland SH-4d (Rhythm Part):** Kick (`36`), Snare (`38`), Clap (`39`), Low Tom (`43`), Open Hat (`46`), High Tom (`48`), Crash (`49`)
* **`Ch 6` → Donner Essential B1 (Analog 303 Bass):** `CC#123` (`0`) Pre-Drop mute + optional Scale Generator notes
* **`Ch 10` → Donner Essential D1 (Sample Beat Machine):** Kick (`36`), Snare (`37`), Low Tom (`38`), Clap (`39`), Open Hat (`41`), High Tom (`42`), Crash (`43`)
* **`Ch 14` → Boss RC-505mkII (`RX CTL CH`):**
  * `CC#80` / `CC#81`: `INPUT FX A` ON/OFF & Control (`Pad 3` 4/8-Bar Auto-Riser & `Mod Strip`)
  * `CC#82` / `CC#85`: `INPUT FX B` ON/OFF & Control (`Hold + Fader 3`)
  * `CC#83` / `CC#84`: `INPUT FX C` ON/OFF & Filter/Slicer Rate (`Pad 7` + `Knob 1`)
* **USB Cable 0 RX (`Ch 15 CC#119`, `0–60`):** Live `0–60 ms` 5-Pin DIN Sync Delay adjustment from `minilab3_midi_monitor.py` (or directly on hardware via `Hold + Black Main Knob Turn`). Boot default is always **`0 ms (OFF)`**.

---

## Quick Start: Switching & Flashing Firmware

1. **Check currently staged firmware in Arturia MIDI Control Center (MCC):**
   ```powershell
   python switch_mcc_firmware.py status
   ```
2. **Stage your desired firmware into MCC (`drop`, `drop_mioxm`, `pro64`, `live8`, or `factory`):**
   ```powershell
   python switch_mcc_firmware.py drop
   ```
3. Open **Arturia MIDI Control Center**, click **`Firmware Revision: 1.2.0 -> Upgrade`**, wait for reboot, and **close MCC** so USB MIDI ports are released.

---

## Rebuilding Firmware from Source

Requires Python 3.10+ and `capstone` (used to disassemble and verify 100% of emitted ARM Thumb-1 machine code and DFU checksums at build time):

```powershell
pip install capstone
python build_fw3_drop_kick.py
python build_fw2_pro64.py
python build_fw1_live8.py
```

---

## Companion Real-Time MIDI Monitor & `<0.2 ms` Virtual Splitter

`minilab3_midi_monitor.py` (`Baslat_MiniLab3_MIDI_Monitor.bat`) is a zero-dependency Windows (`winmm.dll`) real-time MIDI monitor and sub-millisecond callback MIDI Thru router with automatic `SH-4d` 5-Pin DIN latency compensation (`+21 ms` when bridging USB MIDI to `Behringer UMC1820 MIDI Out`, automatically resetting MiniLab 3 to `0 ms` on exit).

---

## Detailed Turkish Guides
* **FW3 Drop Commander Full Reference:** [MINILAB3_DROP_COMMANDER_KILAVUZU.md](MINILAB3_DROP_COMMANDER_KILAVUZU.md)
* **FW3 Step-by-Step Hardware Test Guide:** [MINILAB3_DROP_COMMANDER_ADIM_ADIM_TEST_REHBERI.md](MINILAB3_DROP_COMMANDER_ADIM_ADIM_TEST_REHBERI.md)
* **FW2 Pro 64-Step Groovebox Manual:** [MINILAB3_OTF64_KULLANIM_KILAVUZU.md](MINILAB3_OTF64_KULLANIM_KILAVUZU.md)
* **FW2 Key Combinations Cheat Sheet:** [MINILAB3_OTF64_TUS_KOMBINASYONLARI_OZETI.md](MINILAB3_OTF64_TUS_KOMBINASYONLARI_OZETI.md)
* **FW1 + Factory Dual Firmware Guide:** [MINILAB3_DUAL_FIRMWARE_REHBERI.md](MINILAB3_DUAL_FIRMWARE_REHBERI.md)
