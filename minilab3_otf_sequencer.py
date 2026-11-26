#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Arturia MiniLab 3 -> Stylophone OTF (On-The-Fly) 8-Step Performance Sequencer
=============================================================================
- MiniLab 3'ün 8 Knob, 8 RGB Pad (Bank A/B), 4 Fader, 25 Tuş ve 128x32 OLED
  ekranını gerçek zamanlı Arturia Prot42 SysEx protokolü ile sürer.
- Üretilen sekansı "Minilab3 DIN THRU" (MiniLab 3'ün 5-pin MIDI OUT portu)
  veya seçilen harici MIDI çıkışı üzerinden MOTU MIDI Express XT kurulumuna gönderir.
- Boss RC-505mkII / Polyend Tracker'dan gelen harici MIDI Clock (0xF8) sinyaline
  otomatik kilitlenir veya dahili (Internal) saat ile çalışır.
"""

import os
import sys
import json
import time
import random
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import mido

# ---------------------------------------------------------------------------
# SABİTLER, GAMLAR (SCALES), ZİNCİRLER (CHAINS) VE HEDEF CİHAZLAR
# ---------------------------------------------------------------------------

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def midi_to_note_str(n: int) -> str:
    n = max(0, min(127, int(n)))
    name = NOTE_NAMES[n % 12]
    octv = (n // 12) - 1
    return f"{name}{octv}"

SCALES = [
    ("Minor (Aeolian)",    [0, 2, 3, 5, 7, 8, 10]),
    ("Phrygian (Techno)",  [0, 1, 3, 5, 7, 8, 10]),
    ("Dorian",             [0, 2, 3, 5, 7, 9, 10]),
    ("Major (Ionian)",     [0, 2, 4, 5, 7, 9, 11]),
    ("Harmonic Minor",     [0, 2, 3, 5, 7, 8, 11]),
    ("Minor Pentatonic",   [0, 3, 5, 7, 10]),
    ("Major Pentatonic",   [0, 2, 4, 7, 9]),
    ("Blues",              [0, 3, 5, 6, 7, 10]),
    ("Fifths & Octaves",   [0, 7]),
    ("Chromatic",          [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]),
]

PATTERN_CHAINS = [
    ("A (1-4)",        [0, 1, 2, 3]),
    ("B (5-8)",        [4, 5, 6, 7]),
    ("A-B (1-8)",      [0, 1, 2, 3, 4, 5, 6, 7]),
    ("A-A-B (12)",     [0, 1, 2, 3, 0, 1, 2, 3, 4, 5, 6, 7]),
    ("A-A-A-B (16)",   [0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 4, 5, 6, 7]),
    ("A-B-B-B (16)",   [0, 1, 2, 3, 4, 5, 6, 7, 4, 5, 6, 7, 4, 5, 6, 7]),
    ("A-A-B-B (16)",   [0, 1, 2, 3, 0, 1, 2, 3, 4, 5, 6, 7, 4, 5, 6, 7]),
    ("A-B-A-VarB(32)", [0, 1, 2, 3, 4, 5, 6, 7, 0, 1, 2, 3, 7, 6, 5, 4]),
]

DIRECTIONS = ["FWD ->", "REV <-", "BOUNCE <>", "RANDOM ?"]

TARGET_SYNTHS = [
    ("SH-4d Part 1 (Ch 8)",   8),
    ("SH-4d Part 2 (Ch 9)",   9),
    ("SH-4d Part 3 (Ch 11)", 11),
    ("SH-4d Part 4 (Ch 12)", 12),
    ("microKORG 1 (Ch 6)",    6),
    ("microKORG 2 (Ch 7)",    7),
    ("Nord Lead 1 (Ch 1)",    1),
    ("Donner B1 / Ch 5",      5),
    ("Donner D1 Drum (Ch10)", 10),
]

DIVISIONS = [
    ("1/4",   24),
    ("1/8",   12),
    ("1/8T",   8),
    ("1/16",   6),
    ("1/16T",  4),
    ("1/32",   3),
]

# Adım Durumları (Per-Step Modes) & MiniLab 3 RGB Renk Karşılıkları (0..127)
STEP_STATES = {
    "NORMAL":   {"label": "NORM", "gui_color": "#10b981", "rgb": (0x00, 0x55, 0x08)}, # Yeşil
    "REST":     {"label": "REST", "gui_color": "#ef4444", "rgb": (0x60, 0x00, 0x00)}, # Kırmızı
    "SKIP":     {"label": "SKIP", "gui_color": "#3b82f6", "rgb": (0x00, 0x15, 0x70)}, # Mavi
    "TIE":      {"label": "TIE",  "gui_color": "#eab308", "rgb": (0x65, 0x50, 0x00)}, # Sarı
    "SLIDE":    {"label": "SLID", "gui_color": "#06b6d4", "rgb": (0x00, 0x65, 0x65)}, # Turkuaz
    "RATCHET2": {"label": "RAT2", "gui_color": "#a855f7", "rgb": (0x45, 0x00, 0x65)}, # Mor
    "RATCHET3": {"label": "RAT3", "gui_color": "#c084fc", "rgb": (0x65, 0x00, 0x7F)}, # Açık Mor
    "RATCHET4": {"label": "RAT4", "gui_color": "#e879f9", "rgb": (0x7F, 0x10, 0x7F)}, # Parlak Pembe/Mor
    "RANDOM":   {"label": "RAND", "gui_color": "#f97316", "rgb": (0x70, 0x25, 0x00)}, # Turuncu
}

EDIT_MODES = ["REST", "SKIP", "TIE_SLIDE", "RATCHET", "RANDOM"]


class StepData:
    def __init__(self, degree=0, state="NORMAL", velocity=100):
        self.degree = degree      # Gam içindeki derece ofseti (-14 .. +14)
        self.state = state        # NORMAL, REST, SKIP, TIE, SLIDE, RATCHET2/3/4, RANDOM
        self.velocity = velocity  # 1..127

    def to_dict(self):
        return {"degree": self.degree, "state": self.state, "velocity": self.velocity}

    @staticmethod
    def from_dict(d):
        return StepData(d.get("degree", 0), d.get("state", "NORMAL"), d.get("velocity", 100))


# ---------------------------------------------------------------------------
# ARTURIA MINILAB 3 PROT42 SYSEX SÜRÜCÜSÜ (OLED EKRAN & RGB PAD LED)
# ---------------------------------------------------------------------------

class MiniLab3SysExDriver:
    """
    MiniLab 3 firmware v1.2.0 içinden tersine mühendislikle çıkarılan
    Prot42 SysEx komutlarını kullanarak 128x32 OLED ekranı ve 8 RGB Pad'i sürer.
    """
    HEADER = [0x00, 0x20, 0x6B, 0x7F, 0x42]

    @staticmethod
    def build_led_sysex(led_id: int, r: int, g: int, b: int) -> mido.Message:
        # led_id: 0x00=Shift, 0x01=Oct-, 0x02=Hold, 0x03=Oct+, 0x04..0x0B=Pad 1..8, 0x60=All
        data = MiniLab3SysExDriver.HEADER + [
            0x02, 0x00, 0x16,
            led_id & 0x7F,
            max(0, min(127, int(r))),
            max(0, min(127, int(g))),
            max(0, min(127, int(b))),
        ]
        return mido.Message('sysex', data=data)

    @staticmethod
    def build_oled_sysex(line1: str, line2: str) -> mido.Message:
        # Firmware Prot42 OLED 2-satır metin paketi:
        # 04 00 60 1F 05 01 7E 00 00 01 <line1_ascii> 00 02 <line2_ascii> 00
        l1 = [ord(c) & 0x7F for c in (line1 or "")[:16]]
        l2 = [ord(c) & 0x7F for c in (line2 or "")[:16]]
        data = (
            MiniLab3SysExDriver.HEADER
            + [0x04, 0x00, 0x60, 0x1F, 0x05, 0x01, 0x7E, 0x00, 0x00, 0x01]
            + l1 + [0x00, 0x02]
            + l2 + [0x00]
        )
        return mido.Message('sysex', data=data)

    @staticmethod
    def build_oled_clear() -> mido.Message:
        data = MiniLab3SysExDriver.HEADER + [0x04, 0x00, 0x60, 0x1F, 0x02, 0x01, 0x00, 0x01, 0x00, 0x02, 0x00]
        return mido.Message('sysex', data=data)


# ---------------------------------------------------------------------------
# ANA STYLOPHONE OTF SEQUENCER MOTORU
# ---------------------------------------------------------------------------

class StylophoneOTFEngine:
    def __init__(self, gui_callback=None):
        self.gui_callback = gui_callback
        self.running = False
        self.alive = True

        # Müzikal Parametreler
        self.bpm = 124.0
        self.external_sync = False
        self.division_idx = 3            # Varsayılan: 1/16 (6 MIDI Clock pulse)
        self.root_note = 48              # C3 (MIDI 48)
        self.scale_idx = 1               # Phrygian (Techno)
        self.chain_idx = 2               # A-B (1-8)
        self.direction_idx = 0           # FWD ->
        self.gate_pct = 0.55             # %55 Gate Length
        self.swing_pct = 0.50            # %50 (Düz) .. %75 (Ağır Swing)
        self.target_synth_idx = 0        # SH-4d Part 1 (Ch 8)
        self.edit_mode = "REST"          # Bank A pad'lerine basınca ne yapılacağı
        self.stutter_active = False      # Bank B Pad 7 (Manual Fill/Stutter)
        self.live_record_keys = False    # Üst oktav tuşlarıyla canlı adım yazma

        # 8 Adım Verisi (Başlangıçta enerjik bir Phrygian/Techno dizisi)
        default_degrees = [0, 0, 4, 1, 0, 5, 3, 1]
        default_states  = ["NORMAL", "NORMAL", "SLIDE", "NORMAL", "NORMAL", "RATCHET2", "NORMAL", "NORMAL"]
        self.steps = [StepData(default_degrees[i], default_states[i], 105) for i in range(8)]

        # 24 Hafıza Slotu
        self.memories_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "otf_memories.json")
        self.memories = [None] * 24
        self.current_memory = 0
        self._init_preset_memories()

        # Çalışma Durumu
        self.chain_pos = 0
        self.bounce_dir = 1
        self.active_step_idx = 0
        self.step_counter = 0
        self.current_playing_note = None
        self.current_playing_ch = 8
        self.glide_active = False

        # MIDI Portları
        self.ctrl_in_port = None         # Minilab3 MIDI (Giriş)
        self.sysex_out_ports = []        # Minilab3 MIDI & Minilab3 ALV (OLED & RGB LED Çıkışı)
        self.synth_out_port = None       # Minilab3 DIN THRU veya UMC1820 (Synth Çıkışı)
        self.clock_in_port = None        # Harici Clock Girişi (RC-505 / Tracker / UMC1820)

        self.last_knob_raw = [None] * 8  # Factory Absolute modda çalışan knob'lar için delta takibi
        self.ext_clock_ticks = 0
        self.last_clock_ts = None

        # Thread'ler
        self.lock = threading.Lock()
        self.seq_thread = threading.Thread(target=self._internal_clock_loop, daemon=True)
        self.seq_thread.start()

    # -----------------------------------------------------------------------
    # HAFIZA & HAZIR PRESET DİZİLERİ
    # -----------------------------------------------------------------------
    def _init_preset_memories(self):
        presets = [
            # 1: Dark Phrygian Acid
            {"name": "1: Phrygian Acid", "scale": 1, "chain": 2, "root": 48,
             "steps": [(0,"NORMAL"), (0,"NORMAL"), (4,"SLIDE"), (1,"NORMAL"), (0,"NORMAL"), (5,"RATCHET2"), (3,"SLIDE"), (1,"NORMAL")]},
            # 2: Berlin 16-Step Chain (AAAB)
            {"name": "2: Berlin AAAB", "scale": 0, "chain": 4, "root": 45,
             "steps": [(0,"NORMAL"), (7,"NORMAL"), (3,"TIE"), (0,"NORMAL"), (5,"RATCHET3"), (4,"SLIDE"), (2,"NORMAL"), (-2,"SLIDE")]},
            # 3: Stylophone Classic Bounce
            {"name": "3: Stylo Bounce", "scale": 5, "chain": 2, "root": 50,
             "steps": [(0,"NORMAL"), (1,"NORMAL"), (2,"NORMAL"), (3,"TIE"), (4,"NORMAL"), (5,"RATCHET2"), (3,"NORMAL"), (2,"RANDOM")]},
            # 4: Polymetric 7/8 Rave (Step 8 Skipped!)
            {"name": "4: Polymeter 7/8", "scale": 1, "chain": 2, "root": 48,
             "steps": [(0,"NORMAL"), (1,"NORMAL"), (4,"SLIDE"), (0,"NORMAL"), (5,"NORMAL"), (3,"RATCHET2"), (1,"NORMAL"), (0,"SKIP")]},
            # 5: Donner B1 303 Bassline
            {"name": "5: B1 303 Bass", "scale": 0, "chain": 6, "root": 36,
             "steps": [(0,"NORMAL"), (0,"SLIDE"), (7,"NORMAL"), (0,"REST"), (3,"SLIDE"), (2,"NORMAL"), (0,"RATCHET2"), (-2,"SLIDE")]},
        ]
        for idx, p in enumerate(presets):
            self.memories[idx] = {
                "name": p["name"],
                "scale_idx": p["scale"],
                "chain_idx": p["chain"],
                "root_note": p["root"],
                "steps": [{"degree": deg, "state": st, "velocity": 108} for deg, st in p["steps"]]
            }
        for idx in range(len(presets), 24):
            self.memories[idx] = {
                "name": f"{idx+1}: User OTF {idx+1}",
                "scale_idx": 0,
                "chain_idx": 2,
                "root_note": 48,
                "steps": [{"degree": 0, "state": "NORMAL", "velocity": 100} for _ in range(8)]
            }
        if os.path.isfile(self.memories_file):
            try:
                with open(self.memories_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, list) and len(loaded) == 24:
                    self.memories = loaded
            except Exception:
                pass

    def save_memory(self, slot_idx: int):
        self.memories[slot_idx] = {
            "name": self.memories[slot_idx].get("name", f"{slot_idx+1}: User OTF {slot_idx+1}"),
            "scale_idx": self.scale_idx,
            "chain_idx": self.chain_idx,
            "root_note": self.root_note,
            "steps": [s.to_dict() for s in self.steps],
        }
        try:
            with open(self.memories_file, "w", encoding="utf-8") as f:
                json.dump(self.memories, f, indent=2)
        except Exception:
            pass
        self.send_oled_status(f"Saved Mem #{slot_idx+1}", self.memories[slot_idx]["name"][:16])

    def recall_memory(self, slot_idx: int):
        m = self.memories[slot_idx]
        if not m:
            return
        with self.lock:
            self.current_memory = slot_idx
            self.scale_idx = m.get("scale_idx", 0)
            self.chain_idx = m.get("chain_idx", 2)
            self.root_note = m.get("root_note", 48)
            self.steps = [StepData.from_dict(x) for x in m.get("steps", [])]
        self.refresh_all_pad_leds()
        self.send_oled_status(f"Load {m['name'][:11]}", self.get_step_notes_summary())
        self._notify_gui()

    # -----------------------------------------------------------------------
    # GAM (SCALE) VE NOTA HESAPLAMA
    # -----------------------------------------------------------------------
    def compute_step_midi_note(self, step_idx: int, allow_random: bool = True) -> int:
        step = self.steps[step_idx]
        _, intervals = SCALES[self.scale_idx]
        deg = step.degree
        if allow_random and step.state == "RANDOM":
            deg += random.choice([-2, -1, 0, 1, 2, len(intervals)])
        n_int = len(intervals)
        oct_shift = deg // n_int
        rem = deg % n_int
        note = self.root_note + (oct_shift * 12) + intervals[rem]
        return max(12, min(108, note))

    def get_step_notes_summary(self, bank: int = 0) -> str:
        # OLED 2. satır için 4 adımın notalarını döndürür (max 16 karakter)
        start = 0 if bank == 0 else 4
        parts = []
        for i in range(start, start + 4):
            st = self.steps[i]
            if st.state == "REST":
                parts.append("---")
            elif st.state == "SKIP":
                parts.append("SKP")
            else:
                parts.append(midi_to_note_str(self.compute_step_midi_note(i, allow_random=False)))
        return " ".join(parts)[:16]

    # -----------------------------------------------------------------------
    # MINILAB 3 OLED VE RGB PAD SÜRÜCÜSÜ
    # -----------------------------------------------------------------------
    def _send_sysex_all(self, msg: mido.Message):
        for p in self.sysex_out_ports:
            try:
                p.send(msg)
            except Exception:
                pass

    def send_oled_status(self, line1: str, line2: str):
        if not self.sysex_out_ports:
            return
        try:
            msg = MiniLab3SysExDriver.build_oled_sysex(line1, line2)
            self._send_sysex_all(msg)
        except Exception:
            pass

    def refresh_all_pad_leds(self, active_step: int = None):
        if not self.sysex_out_ports:
            return
        try:
            for i in range(8):
                if active_step is not None and i == active_step and self.running:
                    # Yürüyen adım imleci: Parlak Beyaz!
                    r, g, b = (0x7F, 0x7F, 0x7F)
                else:
                    st_info = STEP_STATES.get(self.steps[i].state, STEP_STATES["NORMAL"])
                    r, g, b = st_info["rgb"]
                # Hem doğrudan (0x04..0x0B) hem Working Memory Bank A (0x34..0x3B) LED adreslerine gönder
                self._send_sysex_all(MiniLab3SysExDriver.build_led_sysex(0x04 + i, r, g, b))
                self._send_sysex_all(mido.Message('sysex', data=MiniLab3SysExDriver.HEADER + [0x02, 0x02, 0x16, 0x34 + i, r, g, b]))
        except Exception:
            pass

    def reset_minilab_hardware_ui(self):
        """MiniLab 3'ün LED ve OLED ekranını normal moduna döndürür."""
        if not self.sysex_out_ports:
            return
        try:
            for i in range(8):
                self._send_sysex_all(MiniLab3SysExDriver.build_led_sysex(0x04 + i, 0, 0x35, 0x10))
                self._send_sysex_all(mido.Message('sysex', data=MiniLab3SysExDriver.HEADER + [0x02, 0x02, 0x16, 0x34 + i, 0, 0x35, 0x10]))
            self._send_sysex_all(MiniLab3SysExDriver.build_oled_sysex("MiniLab 3 Ready", "Normal Mode"))
        except Exception:
            pass

    # -----------------------------------------------------------------------
    # MIDI PORT BAĞLANTILARI VE MİDİ GİRİŞ İŞLEYİCİSİ
    # -----------------------------------------------------------------------
    def connect_ports(self, ctrl_in_name: str, synth_out_name: str, clock_in_name: str = ""):
        self.close_ports()
        try:
            if ctrl_in_name:
                self.ctrl_in_port = mido.open_input(ctrl_in_name, callback=self._on_ctrl_midi)
                # Hem Minilab3 MIDI hem Minilab3 ALV çıkış portlarını OLED & RGB SysEx için aç
                for out_name in mido.get_output_names():
                    if "Minilab3 MIDI" in out_name or "Minilab3 ALV" in out_name:
                        try:
                            p = mido.open_output(out_name)
                            # DAW/ALV ekran yenileme el sıkışması
                            p.send(mido.Message('sysex', data=MiniLab3SysExDriver.HEADER + [0x02, 0x00, 0x40, 0x6A, 0x21]))
                            self.sysex_out_ports.append(p)
                        except Exception:
                            pass
            if synth_out_name:
                self.synth_out_port = mido.open_output(synth_out_name)
            if clock_in_name and clock_in_name != "(Yok / Dahili Clock)" and clock_in_name != ctrl_in_name:
                self.clock_in_port = mido.open_input(clock_in_name, callback=self._on_clock_midi)
        except Exception as e:
            print("MIDI Port Hatası:", e)

        self.refresh_all_pad_leds()
        synth_label, _ = TARGET_SYNTHS[self.target_synth_idx]
        self.send_oled_status("Stylophone OTF", synth_label[:16])

    def close_ports(self):
        self._stop_current_note()
        for p in [self.ctrl_in_port, self.clock_in_port, self.synth_out_port] + self.sysex_out_ports:
            if p:
                try:
                    p.close()
                except Exception:
                    pass
        self.ctrl_in_port = None
        self.clock_in_port = None
        self.sysex_out_ports = []
        self.synth_out_port = None

    def _on_clock_midi(self, msg):
        if msg.type == 'start':
            self.start_sequencer(from_external=True)
        elif msg.type == 'continue':
            self.running = True
            self._notify_gui()
        elif msg.type == 'stop':
            self.stop_sequencer()
        elif msg.type == 'clock':
            now = time.perf_counter()
            if self.last_clock_ts is not None:
                dt = now - self.last_clock_ts
                if 0.005 < dt < 0.2:
                    inst_bpm = 60.0 / (dt * 24.0)
                    self.bpm = round(self.bpm * 0.85 + inst_bpm * 0.15, 1)
            self.last_clock_ts = now
            if self.external_sync and self.running:
                _, pulses_per_step = DIVISIONS[self.division_idx]
                if self.ext_clock_ticks % pulses_per_step == 0:
                    threading.Thread(target=self._trigger_next_step, daemon=True).start()
                self.ext_clock_ticks += 1

    def _on_ctrl_midi(self, msg):
        # 1. Clock mesajları doğrudan bu porttan gelirse de işle
        if msg.type in ('clock', 'start', 'stop', 'continue'):
            self._on_clock_midi(msg)
            return

        # 2. Knob & Fader CC Kontrolleri
        if msg.type == 'control_change':
            cc = msg.control
            val = msg.value

            # A) 8 Adım Pitch Knob'ları:
            # Hem OTF Preset (Relative CC 21..28) hem Fabrika/User1 (CC 74,71,76,77,93,18,19,16 / 58,57,54) desteklenir!
            knob_idx = None
            is_relative = False
            if 21 <= cc <= 28:
                knob_idx = cc - 21
                is_relative = True
            elif cc in (74, 71, 76, 77, 93, 18, 19, 16):
                knob_idx = (74, 71, 76, 77, 93, 18, 19, 16).index(cc)
            elif cc in (58, 57, 54):
                knob_idx = (58, 57, 54).index(cc)

            if knob_idx is not None:
                if is_relative or val in (61, 62, 63, 65, 66, 67):
                    delta = val - 64
                    self.steps[knob_idx].degree = max(-14, min(14, self.steps[knob_idx].degree + delta))
                else:
                    # Absolute mod: 0..127 -> -12..+12 derece
                    new_deg = int(round(((val / 127.0) * 24) - 12))
                    self.steps[knob_idx].degree = new_deg
                note_num = self.compute_step_midi_note(knob_idx, allow_random=False)
                bank = 0 if knob_idx < 4 else 1
                self.send_oled_status(
                    f"Step {knob_idx+1}: {midi_to_note_str(note_num)} ({self.steps[knob_idx].degree:+d})",
                    self.get_step_notes_summary(bank)
                )
                self._notify_gui()
                return

            # Ana Tıklanabilir Knob Dönüşü (CC 114 = BPM veya Hedef Synth, CC 115 = Başlat/Durdur)
            if cc == 114:
                delta = val - 64 if val in range(55, 75) else (1 if val > 64 else -1)
                self.bpm = max(40.0, min(240.0, self.bpm + delta))
                self.send_oled_status(f"Tempo: {int(self.bpm)} BPM", f"Div: {DIVISIONS[self.division_idx][0]}")
                self._notify_gui()
                return
            elif cc == 115 and val >= 64:
                if self.running:
                    self.stop_sequencer()
                else:
                    self.start_sequencer()
                return

            # B) 4 Fader Kontrolü (CC 82, 83, 85, 17)
            if cc == 82:  # Fader 1: Gate Length (%5 .. %95)
                self.gate_pct = round(0.05 + (val / 127.0) * 0.90, 2)
                self.send_oled_status(f"Gate Len: {int(self.gate_pct*100)}%", self.get_step_notes_summary(0))
                self._notify_gui()
            elif cc == 83:  # Fader 2: Swing (%50 .. %75)
                self.swing_pct = round(0.50 + (val / 127.0) * 0.25, 2)
                self.send_oled_status(f"Swing: {int(self.swing_pct*100)}%", self.get_step_notes_summary(0))
                self._notify_gui()
            elif cc == 85:  # Fader 3: Musical Scale (0..9)
                self.scale_idx = min(len(SCALES) - 1, int((val / 128.0) * len(SCALES)))
                sc_name, _ = SCALES[self.scale_idx]
                self.send_oled_status(f"Scale: {sc_name[:9]}", self.get_step_notes_summary(0))
                self._notify_gui()
            elif cc == 17:  # Fader 4: Pattern Chain (0..7)
                self.chain_idx = min(len(PATTERN_CHAINS) - 1, int((val / 128.0) * len(PATTERN_CHAINS)))
                ch_name, _ = PATTERN_CHAINS[self.chain_idx]
                self.send_oled_status(f"Chain: {ch_name[:9]}", self.get_step_notes_summary(0))
                self._notify_gui()

        # 3. Pad'ler ve 25-Tuşlu Klavye (Note On / Note Off)
        elif msg.type == 'note_on' and msg.velocity > 0:
            note = msg.note
            ch = msg.channel  # 0-tabanlı: Ch 10 = 9, Ch 15 = 14

            # A) Bank A Pad 1..8 (Note 36..43, Pad Kanalı Ch 10 veya Ch 15)
            if 36 <= note <= 43 and ch in (9, 14):
                pad_idx = note - 36
                self.toggle_step_by_edit_mode(pad_idx)
                return

            # B) Bank B Pad 1..8 (Note 44..51, Pad Kanalı Ch 10 veya Ch 15)
            if 44 <= note <= 51 and ch in (9, 14):
                b_idx = note - 44
                self._handle_bank_b_pad(b_idx, pressed=True)
                return

            # C) 25-Tuşlu Klavye:
            # Alt Oktav (C2..B2 = MIDI 36..59 klavye kanalından geldiğinde) -> CANLI TRANSPOSE!
            if note < 60:
                pitch_class = note % 12
                # Kök notayı C3 (48..59) oktavında güncelle
                self.root_note = 48 + pitch_class
                root_name = midi_to_note_str(self.root_note)
                sc_name, _ = SCALES[self.scale_idx]
                self.send_oled_status(f"Root: {root_name} {sc_name[:7]}", self.get_step_notes_summary(0))
                self._notify_gui()
            else:
                # Üst Oktav (MIDI >= 60): Canlı Solo Çalım veya Aktif Adıma Kayıt!
                if self.live_record_keys:
                    diff = note - 12 - self.root_note
                    self.steps[self.active_step_idx].degree = max(-14, min(14, diff))
                    self.send_oled_status(f"Rec Step {self.active_step_idx+1}: {midi_to_note_str(note-12)}", self.get_step_notes_summary(0))
                    self._notify_gui()
                else:
                    # Doğrudan hedef synth'e solo nota gönder
                    _, target_ch = TARGET_SYNTHS[self.target_synth_idx]
                    if self.synth_out_port:
                        self.synth_out_port.send(mido.Message('note_on', channel=target_ch - 1, note=note, velocity=msg.velocity))

        elif msg.type in ('note_off', 'note_on') and (msg.type == 'note_off' or msg.velocity == 0):
            note = msg.note
            ch = msg.channel
            if 44 <= note <= 51 and ch in (9, 14):
                if note - 44 == 6:  # Bank B Pad 7 (Stutter Bırakıldı)
                    self.stutter_active = False
                return
            if note >= 60 and not self.live_record_keys and self.synth_out_port:
                _, target_ch = TARGET_SYNTHS[self.target_synth_idx]
                self.synth_out_port.send(mido.Message('note_off', channel=target_ch - 1, note=note, velocity=0))

    # -----------------------------------------------------------------------
    # BANK A & BANK B PAD AKSİYONLARI (STYLOPHONE OTF MODLARI)
    # -----------------------------------------------------------------------
    def toggle_step_by_edit_mode(self, step_idx: int):
        cur = self.steps[step_idx].state
        if self.edit_mode == "REST":
            new_st = "REST" if cur != "REST" else "NORMAL"
        elif self.edit_mode == "SKIP":
            new_st = "SKIP" if cur != "SKIP" else "NORMAL"
        elif self.edit_mode == "TIE_SLIDE":
            order = ["NORMAL", "TIE", "SLIDE"]
            new_st = order[(order.index(cur) + 1) % len(order)] if cur in order else "TIE"
        elif self.edit_mode == "RATCHET":
            order = ["NORMAL", "RATCHET2", "RATCHET3", "RATCHET4"]
            new_st = order[(order.index(cur) + 1) % len(order)] if cur in order else "RATCHET2"
        elif self.edit_mode == "RANDOM":
            new_st = "RANDOM" if cur != "RANDOM" else "NORMAL"
        else:
            new_st = "NORMAL"

        self.steps[step_idx].state = new_st
        self.refresh_all_pad_leds(self.active_step_idx if self.running else None)
        bank = 0 if step_idx < 4 else 1
        self.send_oled_status(f"Step {step_idx+1} -> {STEP_STATES[new_st]['label']}", self.get_step_notes_summary(bank))
        self._notify_gui()

    def _handle_bank_b_pad(self, b_idx: int, pressed: bool = True):
        if not pressed:
            return
        if b_idx < 5:
            self.edit_mode = EDIT_MODES[b_idx]
            self.send_oled_status(f"Pad Mode: {self.edit_mode}", "Press BankA 1-8")
        elif b_idx == 5:
            # Pad 6: Playback Direction (FWD -> REV -> BOUNCE -> RANDOM)
            self.direction_idx = (self.direction_idx + 1) % len(DIRECTIONS)
            self.send_oled_status(f"Dir: {DIRECTIONS[self.direction_idx]}", self.get_step_notes_summary(0))
        elif b_idx == 6:
            # Pad 7: Manual Fill / Stutter
            self.stutter_active = True
            self.send_oled_status("MANUAL STUTTER!", f"Step {self.active_step_idx+1} Roll")
        elif b_idx == 7:
            # Pad 8: Target Synth Değiştirici (SH-4d, microKORG, B1, Nord...)
            self._stop_current_note()
            self.target_synth_idx = (self.target_synth_idx + 1) % len(TARGET_SYNTHS)
            s_name, s_ch = TARGET_SYNTHS[self.target_synth_idx]
            self.send_oled_status("Target Synth:", s_name[:16])
        self._notify_gui()

    def randomize_all_steps(self):
        """Stylophone OTF 'Spice/Random' — tüm 8 adıma müzikal varyasyon üretir."""
        _, intervals = SCALES[self.scale_idx]
        for i in range(8):
            self.steps[i].degree = random.choice(range(-4, len(intervals) + 3))
            self.steps[i].state = random.choices(
                ["NORMAL", "SLIDE", "TIE", "RATCHET2", "REST"],
                weights=[60, 15, 10, 10, 5]
            )[0]
        self.refresh_all_pad_leds(self.active_step_idx if self.running else None)
        self.send_oled_status("OTF Randomized!", self.get_step_notes_summary(0))
        self._notify_gui()

    # -----------------------------------------------------------------------
    # ZAMANLAYICI, ADIM İLERLETME VE RATCHET / SLIDE / TIE ÇALICI
    # -----------------------------------------------------------------------
    def start_sequencer(self, from_external: bool = False):
        with self.lock:
            self.running = True
            self.chain_pos = 0
            self.step_counter = 0
            self.ext_clock_ticks = 0
        self.send_oled_status(f"PLAY {int(self.bpm)}BPM", self.get_step_notes_summary(0))
        self._notify_gui()

    def stop_sequencer(self):
        with self.lock:
            self.running = False
        self._stop_current_note()
        self.refresh_all_pad_leds(active_step=None)
        self.send_oled_status("STOPPED", self.get_step_notes_summary(0))
        self._notify_gui()

    def _stop_current_note(self):
        if self.current_playing_note is not None and self.synth_out_port:
            try:
                if self.glide_active:
                    self.synth_out_port.send(mido.Message('control_change', channel=self.current_playing_ch - 1, control=65, value=0))
                    self.glide_active = False
                self.synth_out_port.send(mido.Message('note_off', channel=self.current_playing_ch - 1, note=self.current_playing_note, velocity=0))
            except Exception:
                pass
        self.current_playing_note = None

    def _internal_clock_loop(self):
        while self.alive:
            if not self.running or self.external_sync:
                time.sleep(0.01)
                continue

            # Adım süresini BPM, Division ve Swing'e göre hesapla
            _, pulses = DIVISIONS[self.division_idx]
            quarter_sec = 60.0 / max(30.0, self.bpm)
            base_step_sec = quarter_sec * (pulses / 24.0)

            # Çift/Tek adıma göre Swing uygula
            if self.step_counter % 2 == 0:
                step_duration = base_step_sec * (self.swing_pct * 2.0)
            else:
                step_duration = base_step_sec * ((1.0 - self.swing_pct) * 2.0)

            t0 = time.perf_counter()
            self._trigger_next_step(step_duration)
            elapsed = time.perf_counter() - t0
            rem = max(0.002, step_duration - elapsed)
            time.sleep(rem)

    def _select_next_step_index(self) -> int:
        _, seq = PATTERN_CHAINS[self.chain_idx]
        # SKIP olan adımları atla (en fazla 8 deneme)
        for _ in range(len(seq)):
            if self.stutter_active:
                return self.active_step_idx

            if self.direction_idx == 0:    # FWD ->
                idx = seq[self.chain_pos % len(seq)]
                self.chain_pos = (self.chain_pos + 1) % len(seq)
            elif self.direction_idx == 1:  # REV <-
                idx = seq[self.chain_pos % len(seq)]
                self.chain_pos = (self.chain_pos - 1) % len(seq)
            elif self.direction_idx == 2:  # BOUNCE <>
                idx = seq[self.chain_pos % len(seq)]
                if len(seq) > 1:
                    if self.chain_pos + self.bounce_dir >= len(seq) or self.chain_pos + self.bounce_dir < 0:
                        self.bounce_dir *= -1
                    self.chain_pos += self.bounce_dir
            else:                          # RANDOM ?
                idx = random.choice(seq)

            if self.steps[idx].state != "SKIP":
                return idx
        return 0

    def _trigger_next_step(self, step_duration: float = None):
        if not self.running:
            return
        if step_duration is None:
            _, pulses = DIVISIONS[self.division_idx]
            step_duration = (60.0 / max(30.0, self.bpm)) * (pulses / 24.0)

        step_idx = self._select_next_step_index()
        self.active_step_idx = step_idx
        self.step_counter += 1
        step = self.steps[step_idx]
        _, target_ch = TARGET_SYNTHS[self.target_synth_idx]

        # MiniLab 3 RGB Pad'lerde yürüyen beyaz ışığı yak ve GUI'yi güncelle
        self.refresh_all_pad_leds(active_step=step_idx)
        self._notify_gui()

        # REST (Sus)
        if step.state == "REST":
            self._stop_current_note()
            return

        note = self.compute_step_midi_note(step_idx, allow_random=True)
        vel = step.velocity

        # Stutter aktifse 2x hızlı vuruş yap
        state = "RATCHET2" if self.stutter_active and step.state == "NORMAL" else step.state

        # RATCHET 2x / 3x / 4x
        if state in ("RATCHET2", "RATCHET3", "RATCHET4"):
            self._stop_current_note()
            sub_count = int(state[-1])
            sub_dur = step_duration / sub_count
            gate_dur = max(0.015, sub_dur * self.gate_pct)
            for r_i in range(sub_count):
                if not self.running:
                    break
                if self.synth_out_port:
                    self.synth_out_port.send(mido.Message('note_on', channel=target_ch - 1, note=note, velocity=vel))
                time.sleep(gate_dur)
                if self.synth_out_port:
                    self.synth_out_port.send(mido.Message('note_off', channel=target_ch - 1, note=note, velocity=0))
                if r_i < sub_count - 1:
                    time.sleep(max(0.005, sub_dur - gate_dur))
            return

        # TIE (Sonraki adıma uzayan legato nota)
        if state == "TIE":
            if self.current_playing_note != note:
                self._stop_current_note()
                if self.synth_out_port:
                    self.synth_out_port.send(mido.Message('note_on', channel=target_ch - 1, note=note, velocity=vel))
                self.current_playing_note = note
                self.current_playing_ch = target_ch
            return

        # SLIDE (Acid 303 Glide: Portamento CC#65 + Legato Overlap!)
        if state == "SLIDE":
            prev_note = self.current_playing_note
            prev_ch = self.current_playing_ch
            if self.synth_out_port:
                # Portamento ON (CC 65 = 127, CC 5 = 45)
                self.synth_out_port.send(mido.Message('control_change', channel=target_ch - 1, control=5, value=45))
                self.synth_out_port.send(mido.Message('control_change', channel=target_ch - 1, control=65, value=127))
                # Yeni notayı eski notayı kapatmadan (overlap) bas!
                self.synth_out_port.send(mido.Message('note_on', channel=target_ch - 1, note=note, velocity=min(127, vel + 12)))
                if prev_note is not None and prev_note != note:
                    time.sleep(0.025)
                    self.synth_out_port.send(mido.Message('note_off', channel=prev_ch - 1, note=prev_note, velocity=0))
            self.current_playing_note = note
            self.current_playing_ch = target_ch
            self.glide_active = True
            return

        # NORMAL veya RANDOM adım
        self._stop_current_note()
        if self.synth_out_port:
            self.synth_out_port.send(mido.Message('note_on', channel=target_ch - 1, note=note, velocity=vel))
        self.current_playing_note = note
        self.current_playing_ch = target_ch

        gate_dur = max(0.015, step_duration * self.gate_pct)
        time.sleep(gate_dur)
        # Eğer bir sonraki adıma TIE/SLIDE olarak bağlanmadıysa kapat
        if self.current_playing_note == note and not self.glide_active:
            self._stop_current_note()

    def _notify_gui(self):
        if self.gui_callback:
            try:
                self.gui_callback()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# KARANLIK TEMALI CANLI PERFORMANS ARAYÜZÜ (TKINTER GUI)
# ---------------------------------------------------------------------------

class StylophoneOTFApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Arturia MiniLab 3 — Stylophone OTF (On-The-Fly) Performance Sequencer")
        self.root.geometry("1120x720")
        self.root.configure(bg="#0f172a")

        self.engine = StylophoneOTFEngine(gui_callback=self.schedule_ui_refresh)
        self._ui_pending = False

        self._build_ui()
        self._auto_connect_midi()
        self.refresh_ui()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self):
        # Üst Başlık ve MIDI Bağlantı Çubuğu
        top_frame = tk.Frame(self.root, bg="#1e293b", padx=12, pady=8)
        top_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        tk.Label(
            top_frame, text="⚡ MINILAB 3 -> STYLOPHONE OTF SEQUENCER",
            fg="#38bdf8", bg="#1e293b", font=("Segoe UI", 13, "bold")
        ).pack(side=tk.LEFT, padx=(0, 15))

        tk.Label(top_frame, text="MiniLab 3 Port:", fg="#cbd5e1", bg="#1e293b", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self.ctrl_port_var = tk.StringVar()
        self.ctrl_combo = ttk.Combobox(top_frame, textvariable=self.ctrl_port_var, width=22, state="readonly")
        self.ctrl_combo.pack(side=tk.LEFT, padx=5)

        tk.Label(top_frame, text="5-Pin Synth Çıkışı:", fg="#cbd5e1", bg="#1e293b", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self.out_port_var = tk.StringVar()
        self.out_combo = ttk.Combobox(top_frame, textvariable=self.out_port_var, width=24, state="readonly")
        self.out_combo.pack(side=tk.LEFT, padx=5)

        tk.Label(top_frame, text="Master Clock In:", fg="#cbd5e1", bg="#1e293b", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self.clk_port_var = tk.StringVar()
        self.clk_combo = ttk.Combobox(top_frame, textvariable=self.clk_port_var, width=22, state="readonly")
        self.clk_combo.pack(side=tk.LEFT, padx=5)

        tk.Button(
            top_frame, text="🔄 Bağlan", bg="#0284c7", fg="white", font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT, padx=8, command=self._apply_port_selection
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            top_frame, text="🎹 Normal Klavye Moduna Dön", bg="#475569", fg="white", font=("Segoe UI", 9),
            relief=tk.FLAT, padx=8, command=self._return_to_normal_mode
        ).pack(side=tk.RIGHT, padx=4)

        # Orta-Üst: Transport, Clock, Target Synth, Scale, Chain, Direction
        bar_frame = tk.Frame(self.root, bg="#1e293b", padx=12, pady=10)
        bar_frame.pack(fill=tk.X, padx=10, pady=5)

        self.play_btn = tk.Button(
            bar_frame, text="▶ PLAY (OTF)", bg="#10b981", fg="#0f172a",
            font=("Segoe UI", 12, "bold"), width=14, relief=tk.FLAT, command=self.toggle_play
        )
        self.play_btn.pack(side=tk.LEFT, padx=(0, 12))

        self.sync_btn = tk.Button(
            bar_frame, text="CLOCK: INT", bg="#334155", fg="#f8fafc",
            font=("Segoe UI", 10, "bold"), width=12, relief=tk.FLAT, command=self.toggle_sync_mode
        )
        self.sync_btn.pack(side=tk.LEFT, padx=6)

        # BPM & Division
        tk.Label(bar_frame, text="BPM:", fg="#94a3b8", bg="#1e293b", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(10, 2))
        self.bpm_var = tk.DoubleVar(value=124.0)
        bpm_spin = tk.Spinbox(
            bar_frame, from_=40, to=240, increment=1, textvariable=self.bpm_var,
            width=5, font=("Segoe UI", 11, "bold"), bg="#0f172a", fg="#38bdf8",
            command=self._on_param_gui_change
        )
        bpm_spin.pack(side=tk.LEFT, padx=4)

        tk.Label(bar_frame, text="Div:", fg="#94a3b8", bg="#1e293b", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(8, 2))
        self.div_combo = ttk.Combobox(bar_frame, values=[d[0] for d in DIVISIONS], width=7, state="readonly")
        self.div_combo.current(self.engine.division_idx)
        self.div_combo.bind("<<ComboboxSelected>>", lambda e: self._on_param_gui_change())
        self.div_combo.pack(side=tk.LEFT, padx=4)

        # Target Synth (16-Kanal Haritasından)
        tk.Label(bar_frame, text="Hedef Synth (Pad B8):", fg="#fbbf24", bg="#1e293b", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(14, 4))
        self.synth_combo = ttk.Combobox(bar_frame, values=[s[0] for s in TARGET_SYNTHS], width=21, state="readonly")
        self.synth_combo.current(self.engine.target_synth_idx)
        self.synth_combo.bind("<<ComboboxSelected>>", lambda e: self._on_synth_gui_change())
        self.synth_combo.pack(side=tk.LEFT, padx=4)

        # Randomize / Spice Butonu
        tk.Button(
            bar_frame, text="🎲 SPICE / RANDOMIZE", bg="#f97316", fg="white",
            font=("Segoe UI", 10, "bold"), relief=tk.FLAT, padx=10, command=self.engine.randomize_all_steps
        ).pack(side=tk.RIGHT, padx=4)

        # 8 ADIM PANELİ (PATTERN A: 1-4 | PATTERN B: 5-8)
        steps_outer = tk.Frame(self.root, bg="#0f172a")
        steps_outer.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        self.step_cards = []
        self.step_note_labels = []
        self.step_deg_scales = []
        self.step_state_btns = []

        for i in range(8):
            pat_color = "#1e293b" if i < 4 else "#172554"
            card = tk.Frame(steps_outer, bg=pat_color, bd=2, relief=tk.RIDGE, padx=8, pady=8)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)
            self.step_cards.append(card)

            hdr_txt = f"A{i+1} (Knob {i+1})" if i < 4 else f"B{i-3} (Knob {i+1})"
            tk.Label(card, text=hdr_txt, fg="#94a3b8", bg=pat_color, font=("Segoe UI", 9, "bold")).pack()

            note_lbl = tk.Label(card, text="C3", fg="#f8fafc", bg="#0f172a", font=("Consolas", 18, "bold"), width=6, pady=6)
            note_lbl.pack(pady=6)
            self.step_note_labels.append(note_lbl)

            deg_scale = tk.Scale(
                card, from_=14, to=-14, orient=tk.VERTICAL, bg=pat_color, fg="#38bdf8",
                highlightthickness=0, troughcolor="#0f172a", length=160,
                command=lambda val, idx=i: self._on_step_slider(idx, int(val))
            )
            deg_scale.set(self.engine.steps[i].degree)
            deg_scale.pack(pady=4)
            self.step_deg_scales.append(deg_scale)

            st_btn = tk.Button(
                card, text="NORM", bg="#10b981", fg="#0f172a",
                font=("Segoe UI", 10, "bold"), relief=tk.FLAT, pady=6,
                command=lambda idx=i: self.engine.toggle_step_by_edit_mode(idx)
            )
            st_btn.pack(fill=tk.X, pady=(6, 2))
            self.step_state_btns.append(st_btn)

        # Alt Performans Çubuğu (4 Fader + Bank B Mod Seçicileri + 24 Hafıza)
        bot_frame = tk.Frame(self.root, bg="#1e293b", padx=12, pady=10)
        bot_frame.pack(fill=tk.X, padx=10, pady=(4, 10))

        # Sol: 4 Fader Karşılığı (Gate, Swing, Scale, Chain)
        fader_box = tk.LabelFrame(bot_frame, text=" 🎚️ MiniLab 3 Fader 1–4 (Groove, Scale & Pattern Chain) ", fg="#38bdf8", bg="#1e293b", font=("Segoe UI", 9, "bold"), padx=10, pady=6)
        fader_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        self.info_labels = {}
        for row_i, (key, title) in enumerate([
            ("gate",  "Fader 1 (Gate):"),
            ("swing", "Fader 2 (Swing):"),
            ("scale", "Fader 3 (Scale):"),
            ("chain", "Fader 4 (Chain):"),
        ]):
            tk.Label(fader_box, text=title, fg="#cbd5e1", bg="#1e293b", font=("Segoe UI", 9, "bold")).grid(row=row_i, column=0, sticky="w", pady=2)
            lbl = tk.Label(fader_box, text="", fg="#f8fafc", bg="#1e293b", font=("Segoe UI", 10, "bold"), width=22, anchor="w")
            lbl.grid(row=row_i, column=1, sticky="w", padx=6)
            self.info_labels[key] = lbl

        # Orta: Bank B Pad Modları & Yön & Transpose
        mode_box = tk.LabelFrame(bot_frame, text=" 🎛️ Bank B Pad 1–6 (Adım Modu & Yön) + Klavye Transpose ", fg="#a855f7", bg="#1e293b", font=("Segoe UI", 9, "bold"), padx=10, pady=6)
        mode_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8)

        self.mode_btns = {}
        for idx, m_name in enumerate(EDIT_MODES):
            btn = tk.Button(
                mode_box, text=f"B{idx+1}: {m_name}", bg="#334155", fg="white",
                font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=8, pady=4,
                command=lambda m=m_name: self._set_edit_mode(m)
            )
            btn.grid(row=0, column=idx, padx=3, pady=4)
            self.mode_btns[m_name] = btn

        self.dir_btn = tk.Button(
            mode_box, text="B6 Yön: FWD ->", bg="#eab308", fg="#0f172a",
            font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=10, pady=4,
            command=lambda: self.engine._handle_bank_b_pad(5, True)
        )
        self.dir_btn.grid(row=1, column=0, columnspan=2, sticky="ew", padx=3, pady=4)

        self.root_lbl = tk.Label(mode_box, text="Kök Nota (Alt Oktav): C3", fg="#38bdf8", bg="#1e293b", font=("Segoe UI", 10, "bold"))
        self.root_lbl.grid(row=1, column=2, columnspan=3, sticky="w", padx=8)

        # Sağ: 24 Hafıza Slotu (Memories)
        mem_box = tk.LabelFrame(bot_frame, text=" 💾 24 OTF Pattern Hafızası ", fg="#10b981", bg="#1e293b", font=("Segoe UI", 9, "bold"), padx=10, pady=6)
        mem_box.pack(side=tk.RIGHT, fill=tk.Y)

        self.mem_combo = ttk.Combobox(mem_box, values=[m["name"] for m in self.engine.memories], width=20, state="readonly")
        self.mem_combo.current(0)
        self.mem_combo.pack(pady=4)

        btn_row = tk.Frame(mem_box, bg="#1e293b")
        btn_row.pack(pady=4)
        tk.Button(btn_row, text="📂 Yükle", bg="#10b981", fg="#0f172a", font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=8, command=self._load_selected_mem).pack(side=tk.LEFT, padx=3)
        tk.Button(btn_row, text="💾 Kaydet", bg="#0284c7", fg="white", font=("Segoe UI", 9, "bold"), relief=tk.FLAT, padx=8, command=self._save_selected_mem).pack(side=tk.LEFT, padx=3)

    # -----------------------------------------------------------------------
    # OTOMATİK MİDİ PORT ALGILAMA VE EŞLEŞTİRME
    # -----------------------------------------------------------------------
    def _auto_connect_midi(self):
        in_ports = mido.get_input_names()
        out_ports = mido.get_output_names()

        self.ctrl_combo["values"] = in_ports
        self.out_combo["values"] = out_ports
        self.clk_combo["values"] = ["(Yok / Dahili Clock)"] + in_ports

        # 1. MiniLab 3 Girişini Bul
        ctrl_sel = ""
        for p in in_ports:
            if "Minilab3 MIDI" in p or ("MiniLab" in p and "MCU" not in p and "ALV" not in p):
                ctrl_sel = p
                break
        if not ctrl_sel and in_ports:
            ctrl_sel = in_ports[0]
        self.ctrl_port_var.set(ctrl_sel)

        # 2. MiniLab 3 5-Pin DIN THRU Çıkışını (veya UMC1820'yi) Bul
        out_sel = ""
        for p in out_ports:
            if "DIN THRU" in p:
                out_sel = p
                break
        if not out_sel:
            for p in out_ports:
                if "UMC1820" in p or "SH-4d" in p or "RC-505" in p:
                    out_sel = p
                    break
        if not out_sel and out_ports:
            out_sel = out_ports[0]
        self.out_port_var.set(out_sel)

        # 3. Harici Clock Girişi
        clk_sel = "(Yok / Dahili Clock)"
        for p in in_ports:
            if "RC-505" in p or "Tracker" in p or "UMC1820" in p:
                clk_sel = p
                break
        self.clk_port_var.set(clk_sel)

        self._apply_port_selection()

    def _apply_port_selection(self):
        self.engine.connect_ports(
            self.ctrl_port_var.get(),
            self.out_port_var.get(),
            self.clk_port_var.get()
        )

    def _return_to_normal_mode(self):
        self.engine.stop_sequencer()
        self.engine.reset_minilab_hardware_ui()
        messagebox.showinfo(
            "Normal Klavye Modu",
            "MiniLab 3'ün OLED ekranı ve RGB Pad ışıkları standart moda döndürüldü.\n\n"
            "Cihaz üzerinden Shift + Pad 2 (Prog) ile User 1 veya Arturia moduna geçerek normal klavye olarak kullanmaya devam edebilirsin."
        )

    # -----------------------------------------------------------------------
    # GUI ETKİLEŞİMLERİ
    # -----------------------------------------------------------------------
    def toggle_play(self):
        if self.engine.running:
            self.engine.stop_sequencer()
        else:
            self.engine.start_sequencer()

    def toggle_sync_mode(self):
        self.engine.external_sync = not self.engine.external_sync
        mode_str = "EXT (MIDI Clock)" if self.engine.external_sync else "INT (Dahili)"
        self.engine.send_oled_status("Clock Sync:", mode_str[:16])
        self.refresh_ui()

    def _on_param_gui_change(self):
        try:
            self.engine.bpm = float(self.bpm_var.get())
        except Exception:
            pass
        if self.div_combo.current() >= 0:
            self.engine.division_idx = self.div_combo.current()
        self.refresh_ui()

    def _on_synth_gui_change(self):
        if self.synth_combo.current() >= 0:
            self.engine._stop_current_note()
            self.engine.target_synth_idx = self.synth_combo.current()
            s_name, _ = TARGET_SYNTHS[self.engine.target_synth_idx]
            self.engine.send_oled_status("Target Synth:", s_name[:16])
            self.refresh_ui()

    def _on_step_slider(self, idx: int, val: int):
        self.engine.steps[idx].degree = val
        self.refresh_ui()

    def _set_edit_mode(self, mode_name: str):
        self.engine.edit_mode = mode_name
        self.engine.send_oled_status(f"Pad Mode: {mode_name}", "Press BankA 1-8")
        self.refresh_ui()

    def _load_selected_mem(self):
        idx = self.mem_combo.current()
        if idx >= 0:
            self.engine.recall_memory(idx)

    def _save_selected_mem(self):
        idx = self.mem_combo.current()
        if idx >= 0:
            self.engine.save_memory(idx)

    def schedule_ui_refresh(self):
        if not self._ui_pending:
            self._ui_pending = True
            self.root.after(25, self.refresh_ui)

    def refresh_ui(self):
        self._ui_pending = False
        if self.engine.running:
            self.play_btn.configure(text="⏹ STOP (OTF)", bg="#ef4444", fg="white")
        else:
            self.play_btn.configure(text="▶ PLAY (OTF)", bg="#10b981", fg="#0f172a")

        if self.engine.external_sync:
            self.sync_btn.configure(text="CLOCK: EXT", bg="#0284c7")
        else:
            self.sync_btn.configure(text="CLOCK: INT", bg="#334155")

        self.bpm_var.set(round(self.engine.bpm, 1))
        self.synth_combo.current(self.engine.target_synth_idx)

        # 8 Adım Kartlarını Güncelle
        for i in range(8):
            st = self.engine.steps[i]
            st_info = STEP_STATES.get(st.state, STEP_STATES["NORMAL"])
            is_curr = (self.engine.running and self.engine.active_step_idx == i)

            border_col = "#f8fafc" if is_curr else ("#1e293b" if i < 4 else "#172554")
            self.step_cards[i].configure(bg=border_col)

            note_num = self.engine.compute_step_midi_note(i, allow_random=False)
            n_str = "---" if st.state == "REST" else ("SKP" if st.state == "SKIP" else midi_to_note_str(note_num))
            self.step_note_labels[i].configure(
                text=n_str,
                bg="#f8fafc" if is_curr else "#0f172a",
                fg="#0f172a" if is_curr else "#f8fafc"
            )
            if self.step_deg_scales[i].get() != st.degree:
                self.step_deg_scales[i].set(st.degree)
            self.step_state_btns[i].configure(text=st_info["label"], bg=st_info["gui_color"])

        # Alt Bilgi Etiketleri
        self.info_labels["gate"].configure(text=f"%{int(self.engine.gate_pct*100)}")
        self.info_labels["swing"].configure(text=f"%{int(self.engine.swing_pct*100)}")
        self.info_labels["scale"].configure(text=SCALES[self.engine.scale_idx][0])
        self.info_labels["chain"].configure(text=PATTERN_CHAINS[self.engine.chain_idx][0])

        for m_name, btn in self.mode_btns.items():
            btn.configure(bg="#a855f7" if self.engine.edit_mode == m_name else "#334155")

        self.dir_btn.configure(text=f"B6 Yön: {DIRECTIONS[self.engine.direction_idx]}")
        self.root_lbl.configure(text=f"Kök Nota (Alt Oktav): {midi_to_note_str(self.engine.root_note)}")

    def on_close(self):
        self.engine.alive = False
        self.engine.stop_sequencer()
        self.engine.reset_minilab_hardware_ui()
        self.engine.close_ports()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = StylophoneOTFApp(root)
    root.mainloop()
