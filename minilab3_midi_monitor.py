#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Arturia MiniLab 3 & Dawless Chain — Real-Time MIDI Monitor
==========================================================
Zero-dependency Windows (winmm.dll) GUI + CLI MIDI Monitor tailored for:
  - Arturia MiniLab 3 (USB: 'Minilab3 MIDI' / 'Minilab3 DIN THRU' or 5-Pin DIN via Audio Interface)
  - Active 5-Device Live Chain (SH-4d Ch 1-5, Donner B1 Ch 6, Donner D1 Ch 10, Boss RC-505mkII Ch 14/16)

Usage:
  GUI Mode : python minilab3_midi_monitor.py
  CLI Mode : python minilab3_midi_monitor.py --cli
"""

from collections import deque
import ctypes
from ctypes import wintypes
import datetime
import json
import os
import queue
import subprocess
import sys
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import winreg

# ==============================================================================
# Windows Multimedia API (winmm.dll) — 32/64-bit Safe Definitions
# ==============================================================================
winmm = ctypes.windll.winmm

MAXPNAMELEN = 32
CALLBACK_FUNCTION = 0x00030000

MIM_OPEN = 0x3C1
MIM_CLOSE = 0x3C2
MIM_DATA = 0x3C3
MIM_LONGDATA = 0x3C4
MIM_ERROR = 0x3C5
MIM_LONGERROR = 0x3C6


class MIDIINCAPSW(ctypes.Structure):
    _fields_ = [
        ("wMid", wintypes.WORD),
        ("wPid", wintypes.WORD),
        ("vDriverVersion", wintypes.UINT),
        ("szPname", wintypes.WCHAR * MAXPNAMELEN),
        ("dwSupport", wintypes.DWORD),
    ]


class MIDIOUTCAPSW(ctypes.Structure):
    _fields_ = [
        ("wMid", wintypes.WORD),
        ("wPid", wintypes.WORD),
        ("vDriverVersion", wintypes.UINT),
        ("szPname", wintypes.WCHAR * MAXPNAMELEN),
        ("wTechnology", wintypes.WORD),
        ("wVoices", wintypes.WORD),
        ("wNotes", wintypes.WORD),
        ("wChannelMask", wintypes.WORD),
        ("dwSupport", wintypes.DWORD),
    ]


class MIDIHDR(ctypes.Structure):
    _fields_ = [
        ("lpData", ctypes.c_void_p),
        ("dwBufferLength", wintypes.DWORD),
        ("dwBytesRecorded", wintypes.DWORD),
        ("dwUser", ctypes.c_size_t),
        ("dwFlags", wintypes.DWORD),
        ("lpNext", ctypes.c_void_p),
        ("reserved", ctypes.c_size_t),
        ("dwOffset", wintypes.DWORD),
        ("dwReserved", ctypes.c_size_t * 8),
    ]


MidiInProc = ctypes.WINFUNCTYPE(
    None,
    ctypes.c_void_p,
    wintypes.UINT,
    ctypes.c_size_t,
    ctypes.c_size_t,
    ctypes.c_size_t,
)

winmm.midiInGetNumDevs.argtypes = []
winmm.midiInGetNumDevs.restype = wintypes.UINT

winmm.midiInGetDevCapsW.argtypes = [
    ctypes.c_size_t,
    ctypes.POINTER(MIDIINCAPSW),
    wintypes.UINT,
]
winmm.midiInGetDevCapsW.restype = wintypes.UINT

winmm.midiInOpen.argtypes = [
    ctypes.POINTER(ctypes.c_void_p),
    wintypes.UINT,
    ctypes.c_size_t,
    ctypes.c_size_t,
    wintypes.DWORD,
]
winmm.midiInOpen.restype = wintypes.UINT

winmm.midiInStart.argtypes = [ctypes.c_void_p]
winmm.midiInStart.restype = wintypes.UINT

winmm.midiInStop.argtypes = [ctypes.c_void_p]
winmm.midiInStop.restype = wintypes.UINT

winmm.midiInReset.argtypes = [ctypes.c_void_p]
winmm.midiInReset.restype = wintypes.UINT

winmm.midiInClose.argtypes = [ctypes.c_void_p]
winmm.midiInClose.restype = wintypes.UINT

winmm.midiInPrepareHeader.argtypes = [
    ctypes.c_void_p,
    ctypes.POINTER(MIDIHDR),
    wintypes.UINT,
]
winmm.midiInPrepareHeader.restype = wintypes.UINT

winmm.midiInUnprepareHeader.argtypes = [
    ctypes.c_void_p,
    ctypes.POINTER(MIDIHDR),
    wintypes.UINT,
]
winmm.midiInUnprepareHeader.restype = wintypes.UINT

winmm.midiInAddBuffer.argtypes = [
    ctypes.c_void_p,
    ctypes.POINTER(MIDIHDR),
    wintypes.UINT,
]
winmm.midiInAddBuffer.restype = wintypes.UINT

winmm.midiOutGetNumDevs.argtypes = []
winmm.midiOutGetNumDevs.restype = wintypes.UINT

winmm.midiOutGetDevCapsW.argtypes = [
    ctypes.c_size_t,
    ctypes.POINTER(MIDIOUTCAPSW),
    wintypes.UINT,
]
winmm.midiOutGetDevCapsW.restype = wintypes.UINT

winmm.midiOutOpen.argtypes = [
    ctypes.POINTER(ctypes.c_void_p),
    wintypes.UINT,
    ctypes.c_size_t,
    ctypes.c_size_t,
    wintypes.DWORD,
]
winmm.midiOutOpen.restype = wintypes.UINT

winmm.midiOutShortMsg.argtypes = [ctypes.c_void_p, wintypes.DWORD]
winmm.midiOutShortMsg.restype = wintypes.UINT

winmm.midiOutReset.argtypes = [ctypes.c_void_p]
winmm.midiOutReset.restype = wintypes.UINT

winmm.midiOutClose.argtypes = [ctypes.c_void_p]
winmm.midiOutClose.restype = wintypes.UINT


def list_midi_inputs():
    """Returns [(device_id, port_name), ...] for all active Windows MIDI In ports."""
    ports = []
    count = winmm.midiInGetNumDevs()
    for dev_id in range(count):
        caps = MIDIINCAPSW()
        if winmm.midiInGetDevCapsW(dev_id, ctypes.byref(caps), ctypes.sizeof(caps)) == 0:
            ports.append((dev_id, caps.szPname.strip()))
    return ports


def list_thru_midi_outputs():
    """Returns [(device_id, port_name), ...] for safe external MIDI Out targets (excludes GS Synth & MiniLab)."""
    ports = []
    count = winmm.midiOutGetNumDevs()
    for dev_id in range(count):
        caps = MIDIOUTCAPSW()
        if winmm.midiOutGetDevCapsW(dev_id, ctypes.byref(caps), ctypes.sizeof(caps)) == 0:
            name = caps.szPname.strip()
            low = name.lower()
            if "wavetable" in low or "minilab" in low:
                continue
            ports.append((dev_id, name))
    return ports


PREFS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "minilab3_monitor_prefs.json")
DEFAULT_DIN_DELAY_MS = 21  # Measured Windows 11 MidiSrv -> UMC1820 MIDI Out acoustic offset (+20.5 ms)


def send_minilab_din_delay_ms(delay_ms: int) -> bool:
    """Sends Ch 15 CC#119 (0xBE, 119, 0..60) to 'Minilab3 MIDI' Out and closes handle immediately (<1 ms)."""
    val = max(0, min(60, int(delay_ms)))
    count = winmm.midiOutGetNumDevs()
    for dev_id in range(count):
        caps = MIDIOUTCAPSW()
        if winmm.midiOutGetDevCapsW(dev_id, ctypes.byref(caps), ctypes.sizeof(caps)) == 0:
            low = caps.szPname.strip().lower()
            if ("minilab" in low) and ("midi" in low) and ("thru" not in low) and ("din" not in low):
                h = ctypes.c_void_p()
                if winmm.midiOutOpen(ctypes.byref(h), dev_id, 0, 0, 0) == 0 and h.value:
                    msg = 0xBE | (119 << 8) | ((val & 0x7F) << 16)
                    winmm.midiOutShortMsg(h, msg)
                    winmm.midiOutClose(h)
                    return True
    return False


def is_minilab_usb_physically_present() -> bool:
    """Checks via Windows registry (<0.1ms) if Arturia MiniLab 3 USB (VID_1C75&PID_020B) is plugged in."""
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\arturiausbmidi\Enum") as k:
            cnt, _ = winreg.QueryValueEx(k, "Count")
            for i in range(cnt):
                val, _ = winreg.QueryValueEx(k, str(i))
                if "1C75" in str(val).upper():
                    return True
    except OSError:
        pass
    return False


def is_mcc_running() -> bool:
    """Checks if Arturia 'MIDI Control Center.exe' is currently running."""
    try:
        out = subprocess.check_output(
            ["tasklist", "/FI", "IMAGENAME eq MIDI Control Center.exe", "/NH"],
            creationflags=subprocess.CREATE_NO_WINDOW,
            text=True,
            errors="ignore",
        )
        return "MIDI Control Center" in out
    except Exception:
        return False


# ==============================================================================
# MIDI & Dawless Hardware Lookup Tables (Synced with CIHAZLARIM.md)
# ==============================================================================
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def note_to_name(note_num: int) -> str:
    octave = (note_num // 12) - 1
    return f"{NOTE_NAMES[note_num % 12]}{octave}"


D1_PAD_MAP = {
    36: "Pad 1: BD (Kick)",
    37: "Pad 2: SD (Snare)",
    38: "Pad 3: LT (Low Tom)",
    39: "Pad 4: HC (Hand Clap)",
    40: "Pad 5: CH (Closed Hat)",
    41: "Pad 6: OH (Open Hat)",
    42: "Pad 7: HT (High Tom)",
    43: "Pad 8: CR (Crash)",
    44: "Pad 9: SMP1 (Uplifter/FX1)",
    45: "Pad 10: SMP2 (FX2)",
    46: "Pad 11: SMP3 (FX3)",
    47: "Pad 12: SMP4 (Impact/FX4)",
}

SH4D_DRUM_MAP = {
    36: "BD1 (Kick)",
    37: "Rim / Side Stick",
    38: "SD1 (Snare)",
    39: "Hand Clap",
    40: "SD2 (Snare 2)",
    41: "Low Tom",
    42: "Closed Hi-Hat",
    45: "Mid Tom",
    46: "Open Hi-Hat",
    48: "High Tom",
    49: "Crash Cymbal 1",
    51: "Ride Cymbal",
}

CC_NAMES = {
    1: "Modulation Wheel",
    5: "Portamento Time",
    7: "Channel Volume",
    10: "Pan",
    11: "Expression / Sidechain Pump",
    64: "Sustain Pedal (Hold)",
    70: "Sound Variation",
    71: "Resonance (Timbre)",
    72: "Amp Release (Hold+Fader3)",
    73: "Amp Attack",
    74: "Filter Cutoff",
    75: "Decay (Hold+Fader3)",
    76: "Vibrato Rate",
    77: "Vibrato Depth",
    79: "Filter Env",
    80: "RC-505 Input FX A ON/OFF",
    81: "RC-505 Input FX A Control (Riser)",
    82: "RC-505 Input FX B ON/OFF",
    83: "RC-505 Input FX C ON/OFF (Wobble/Slicer)",
    84: "RC-505 Input FX C Rate (Knob 1)",
    85: "RC-505 Input FX B Control",
    91: "Reverb Send",
    93: "Chorus Send",
    94: "Delay Send",
    95: "Phaser",
    120: "All Sound Off",
    121: "Reset All Controllers",
    123: "All Notes Off (Vacuum Gate)",
}

CHANNEL_TARGETS = {
    1: "SH-4d Part 1",
    2: "SH-4d Part 2",
    3: "SH-4d Part 3",
    4: "SH-4d Part 4",
    5: "SH-4d Rhythm",
    6: "Donner B1 Bass",
    10: "Donner D1 Beat",
    14: "RC-505mkII CTL",
    16: "RC-505mkII Rhythm",
}


def decode_short_midi(dw_param1: int):
    """
    Decodes packed WinMM DWORD MIDI message into a structured dict:
      category: 'note_on' | 'note_off' | 'cc' | 'pb' | 'pc' | 'at' | 'transport' | 'clock' | 'other'
      ch: 1..16 or None
      hex_str, msg_type, detail, target_hw
    """
    b0 = dw_param1 & 0xFF
    b1 = (dw_param1 >> 8) & 0x7F
    b2 = (dw_param1 >> 16) & 0x7F

    # System Real-Time & System Common (0xF0..0xFF)
    if b0 >= 0xF0:
        hex_1 = f"{b0:02X}"
        if b0 == 0xF8:
            return {
                "category": "clock",
                "ch": None,
                "b0": b0,
                "b1": 0,
                "b2": 0,
                "hex": hex_1,
                "type": "Clock (0xF8)",
                "detail": "24 PPQN Sync Pulse",
                "target": "All Devices (Sync)",
            }
        if b0 == 0xFA:
            return {
                "category": "transport",
                "ch": None,
                "b0": b0,
                "b1": 0,
                "b2": 0,
                "hex": hex_1,
                "type": "START (0xFA)",
                "detail": "Master Transport START -> Bar 1.1",
                "target": "All Sequencers",
            }
        if b0 == 0xFB:
            return {
                "category": "transport",
                "ch": None,
                "b0": b0,
                "b1": 0,
                "b2": 0,
                "hex": hex_1,
                "type": "CONTINUE (0xFB)",
                "detail": "Transport Continue",
                "target": "All Sequencers",
            }
        if b0 == 0xFC:
            return {
                "category": "transport",
                "ch": None,
                "b0": b0,
                "b1": 0,
                "b2": 0,
                "hex": hex_1,
                "type": "STOP (0xFC)",
                "detail": "Master Transport STOP",
                "target": "All Sequencers",
            }
        if b0 == 0xFE:
            return {
                "category": "other",
                "ch": None,
                "b0": b0,
                "b1": 0,
                "b2": 0,
                "hex": hex_1,
                "type": "Active Sensing",
                "detail": "0xFE Keepalive",
                "target": "System",
            }
        return {
            "category": "other",
            "ch": None,
            "b0": b0,
            "b1": b1,
            "b2": b2,
            "hex": f"{b0:02X} {b1:02X} {b2:02X}",
            "type": f"System 0x{b0:02X}",
            "detail": f"Data=({b1}, {b2})",
            "target": "System",
        }

    status_hi = b0 & 0xF0
    ch = (b0 & 0x0F) + 1
    base_target = CHANNEL_TARGETS.get(ch, f"Synth Ch {ch}")

    if status_hi in (0x80, 0x90):
        is_on = (status_hi == 0x90) and (b2 > 0)
        n_name = note_to_name(b1)
        drum_label = ""
        if ch == 10:
            drum_label = f" -> {D1_PAD_MAP.get(b1, 'Unmapped D1 Note!')}"
        elif ch == 5:
            drum_label = f" -> {SH4D_DRUM_MAP.get(b1, 'SH-4d Drum')}"
        return {
            "category": "note_on" if is_on else "note_off",
            "ch": ch,
            "b0": b0,
            "b1": b1,
            "b2": b2,
            "hex": f"{b0:02X} {b1:02X} {b2:02X}",
            "type": "Note ON" if is_on else "Note OFF",
            "detail": f"{n_name:<4s} (#{b1:<3d})  Vel={b2:<3d}{drum_label}",
            "target": base_target,
        }

    if status_hi == 0xB0:
        cc_desc = CC_NAMES.get(b1, f"CC #{b1}")
        if ch == 14 and 1 <= b1 <= 5:
            cc_desc = f"RC-505 Track {b1} Play/Stop"
        return {
            "category": "cc",
            "ch": ch,
            "b0": b0,
            "b1": b1,
            "b2": b2,
            "hex": f"{b0:02X} {b1:02X} {b2:02X}",
            "type": f"CC #{b1}",
            "detail": f"{cc_desc} = {b2}",
            "target": base_target,
        }

    if status_hi == 0xE0:
        pb_val = ((b2 << 7) | b1) - 8192
        return {
            "category": "pb",
            "ch": ch,
            "b0": b0,
            "b1": b1,
            "b2": b2,
            "hex": f"{b0:02X} {b1:02X} {b2:02X}",
            "type": "Pitch Bend",
            "detail": f"{pb_val:+d}  (raw={((b2 << 7) | b1)})",
            "target": base_target,
        }

    if status_hi == 0xC0:
        return {
            "category": "pc",
            "ch": ch,
            "b0": b0,
            "b1": b1,
            "b2": 0,
            "hex": f"{b0:02X} {b1:02X}",
            "type": "Prog Change",
            "detail": f"Program #{b1} (Slot {b1 + 1})",
            "target": base_target,
        }

    if status_hi == 0xA0:
        return {
            "category": "at",
            "ch": ch,
            "b0": b0,
            "b1": b1,
            "b2": b2,
            "hex": f"{b0:02X} {b1:02X} {b2:02X}",
            "type": "Poly Aftertouch",
            "detail": f"{note_to_name(b1)} (#{b1})  Pressure={b2}",
            "target": base_target,
        }

    if status_hi == 0xD0:
        return {
            "category": "at",
            "ch": ch,
            "b0": b0,
            "b1": b1,
            "b2": 0,
            "hex": f"{b0:02X} {b1:02X}",
            "type": "Ch Aftertouch",
            "detail": f"Pressure={b1}",
            "target": base_target,
        }

    return {
        "category": "other",
        "ch": ch,
        "b0": b0,
        "b1": b1,
        "b2": b2,
        "hex": f"{b0:02X} {b1:02X} {b2:02X}",
        "type": f"Status 0x{b0:02X}",
        "detail": f"d1={b1}, d2={b2}",
        "target": base_target,
    }


# ==============================================================================
# Open Port Handle Wrapper (Short MIDI + SysEx)
# ==============================================================================
class OpenMidiInPort:
    def __init__(
        self,
        dev_id: int,
        name: str,
        event_queue: queue.SimpleQueue,
        thru_targets: list,
        thru_cfg: dict | None = None,
    ):
        self.dev_id = dev_id
        self.name = name
        self.event_queue = event_queue
        self.thru_targets = thru_targets
        self.thru_cfg = thru_cfg if thru_cfg is not None else {"lead_ticks": 0, "pending_lead": 0}
        self.handle = ctypes.c_void_p()
        self.closing = False
        self.dead = False
        self.last_open_rc = 0
        self._sysex_bufs = []
        self._sysex_hdrs = []
        self._cb = MidiInProc(self._on_midi)

    def open(self, retries: int = 1, delay_s: float = 0.15) -> bool:
        cb_addr = ctypes.cast(self._cb, ctypes.c_void_p).value
        res = 1
        for attempt in range(retries):
            self.handle = ctypes.c_void_p()
            res = winmm.midiInOpen(
                ctypes.byref(self.handle),
                self.dev_id,
                cb_addr,
                0,
                CALLBACK_FUNCTION,
            )
            self.last_open_rc = res
            if res == 0 and self.handle.value:
                self.dead = False
                break
            if attempt + 1 < retries:
                time.sleep(delay_s)
        if res != 0 or not self.handle.value:
            return False

        # Allocate 4 SysEx buffers (1 KB each)
        for _ in range(4):
            buf = ctypes.create_string_buffer(1024)
            hdr = MIDIHDR()
            hdr.lpData = ctypes.addressof(buf)
            hdr.dwBufferLength = 1024
            hdr.dwBytesRecorded = 0
            hdr.dwFlags = 0
            if winmm.midiInPrepareHeader(self.handle, ctypes.byref(hdr), ctypes.sizeof(MIDIHDR)) == 0:
                winmm.midiInAddBuffer(self.handle, ctypes.byref(hdr), ctypes.sizeof(MIDIHDR))
                self._sysex_bufs.append(buf)
                self._sysex_hdrs.append(hdr)

        winmm.midiInStart(self.handle)
        return True

    def _on_midi(self, h_midi_in, w_msg, dw_instance, dw_param1, dw_param2):
        ts = time.perf_counter()
        if w_msg == MIM_DATA:
            msg24 = dw_param1 & 0xFFFFFF
            b0 = msg24 & 0xFF
            targets = tuple(self.thru_targets)
            if targets:
                if b0 == 0xFA:
                    self.thru_cfg["pending_lead"] = int(self.thru_cfg.get("lead_ticks", 0))
                for out_h in targets:
                    if out_h:
                        winmm.midiOutShortMsg(out_h, msg24)
                if b0 == 0xF8 and self.thru_cfg.get("pending_lead", 0) > 0:
                    extra = self.thru_cfg["pending_lead"]
                    self.thru_cfg["pending_lead"] = 0
                    for _ in range(extra):
                        time.sleep(0.0012)
                        for out_h in targets:
                            if out_h:
                                winmm.midiOutShortMsg(out_h, 0xF8)
            self.event_queue.put((ts, self.name, "short", dw_param1))
        elif w_msg == MIM_LONGDATA and dw_param1:
            hdr = ctypes.cast(dw_param1, ctypes.POINTER(MIDIHDR)).contents
            if hdr.dwBytesRecorded > 0:
                raw = ctypes.string_at(hdr.lpData, hdr.dwBytesRecorded)
                self.event_queue.put((ts, self.name, "sysex", raw))
            if not self.closing and self.handle.value:
                hdr.dwBytesRecorded = 0
                winmm.midiInAddBuffer(self.handle, ctypes.byref(hdr), ctypes.sizeof(MIDIHDR))
        elif w_msg == MIM_CLOSE and not self.closing:
            self.dead = True

    def close(self):
        self.closing = True
        if self.handle.value:
            winmm.midiInStop(self.handle)
            winmm.midiInReset(self.handle)
            for hdr in self._sysex_hdrs:
                winmm.midiInUnprepareHeader(self.handle, ctypes.byref(hdr), ctypes.sizeof(MIDIHDR))
            winmm.midiInClose(self.handle)
            self.handle = ctypes.c_void_p()
        self._sysex_hdrs.clear()
        self._sysex_bufs.clear()


# ==============================================================================
# Tkinter GUI Application
# ==============================================================================
class MiniLab3MidiMonitorApp:
    MAX_ROWS = 1500

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Arturia MiniLab 3 & Dawless Chain — Real-Time MIDI Monitor")
        self.root.geometry("1260x800")
        self.root.configure(bg="#0f1318")

        self.event_queue: queue.SimpleQueue = queue.SimpleQueue()
        self.open_ports: dict[str, OpenMidiInPort] = {}
        self.busy_ports: set[str] = set()
        self.port_vars: dict[str, tk.BooleanVar] = {}
        self.known_port_names: list[str] = []
        self.auto_connected_minilab = False

        # Sub-ms Virtual mioXM MIDI Out Thru Splitter state
        self.thru_handles: list[int] = []
        self.thru_cfg: dict = {"lead_ticks": 0, "pending_lead": 0}
        self.lead_ticks_var = tk.IntVar(value=0)
        saved_delay = self._load_saved_din_delay()
        self.din_delay_ms_var = tk.IntVar(value=saved_delay)
        self._last_sent_din_delay: int | None = None
        self.open_out_ports: dict[str, ctypes.c_void_p] = {}
        self.busy_out_ports: set[str] = set()
        self.out_port_vars: dict[str, tk.BooleanVar] = {}
        self.known_out_names: list[str] = []

        # Timing & Statistics
        self.t0_wall = datetime.datetime.now()
        self.t0_perf = time.perf_counter()
        self.paused = False
        self.last_msg_ts = None
        self.f8_times = deque(maxlen=48)
        self.last_f8_ts = 0.0
        self.clock_ticks = 0
        self.total_msgs = 0
        self.cnt_sh4d_kick = 0
        self.cnt_d1_kick = 0
        self.cnt_sh4d_snare = 0
        self.cnt_d1_snare = 0
        self.cnt_rc505_cc = 0
        self.log_history = deque(maxlen=5000)

        # Filter Variables
        self.flt_note_on = tk.BooleanVar(value=True)
        self.flt_note_off = tk.BooleanVar(value=True)
        self.flt_cc = tk.BooleanVar(value=True)
        self.flt_pb = tk.BooleanVar(value=True)
        self.flt_transport = tk.BooleanVar(value=True)
        self.flt_sysex = tk.BooleanVar(value=True)
        self.flt_clock = tk.BooleanVar(value=False)  # Off by default so 0xF8 doesn't flood log
        self.flt_autoscroll = tk.BooleanVar(value=True)
        self.flt_channel = tk.StringVar(value="All")

        self._setup_styles()
        self._build_ui()
        self.refresh_ports(initial=True)

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(15, self._poll_midi_queue)
        self.root.after(1500, self._hotplug_watchdog)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", background="#0f1318", foreground="#e6edf3", font=("Segoe UI", 9))
        style.configure("Card.TFrame", background="#171d24")
        style.configure("Card.TLabel", background="#171d24", foreground="#e6edf3")
        style.configure("Title.TLabel", background="#171d24", foreground="#58a6ff", font=("Segoe UI", 12, "bold"))
        style.configure("MetricTitle.TLabel", background="#171d24", foreground="#8b949e", font=("Segoe UI", 8, "bold"))
        style.configure("MetricVal.TLabel", background="#171d24", foreground="#3fb950", font=("Consolas", 13, "bold"))
        style.configure("Card.TCheckbutton", background="#171d24", foreground="#e6edf3")
        style.map("Card.TCheckbutton", background=[("active", "#212934")])
        style.configure("Action.TButton", background="#238636", foreground="#ffffff", font=("Segoe UI", 9, "bold"), padding=5)
        style.map("Action.TButton", background=[("active", "#2ea043")])
        style.configure("Secondary.TButton", background="#21262d", foreground="#e6edf3", font=("Segoe UI", 9, "bold"), padding=5)
        style.map("Secondary.TButton", background=[("active", "#30363d")])

        style.configure(
            "Treeview",
            background="#0b0e13",
            foreground="#e6edf3",
            fieldbackground="#0b0e13",
            rowheight=24,
            font=("Consolas", 9),
        )
        style.configure(
            "Treeview.Heading",
            background="#1c232d",
            foreground="#58a6ff",
            font=("Segoe UI", 9, "bold"),
        )
        style.map("Treeview", background=[("selected", "#1f6feb")])

    def _build_ui(self):
        # 1. Header + Port Selection Bar
        hdr = ttk.Frame(self.root, style="Card.TFrame", padding=10)
        hdr.pack(fill="x", padx=10, pady=(10, 6))

        top_row = ttk.Frame(hdr, style="Card.TFrame")
        top_row.pack(fill="x")
        ttk.Label(
            top_row,
            text="ARTURIA MINILAB 3 & DAWLESS CHAIN — CANLI MIDI MONİTÖRÜ",
            style="Title.TLabel",
        ).pack(side="left")

        self.status_lbl = ttk.Label(
            top_row,
            text="Portlar taranıyor...",
            style="Card.TLabel",
            font=("Segoe UI", 9, "bold"),
        )
        self.status_lbl.pack(side="right", padx=6)

        port_row = ttk.Frame(hdr, style="Card.TFrame")
        port_row.pack(fill="x", pady=(8, 0))
        ttk.Label(
            port_row,
            text="Dinlenen MIDI Girişleri:",
            style="Card.TLabel",
            font=("Segoe UI", 9, "bold"),
        ).pack(side="left", padx=(0, 8))

        self.ports_container = ttk.Frame(port_row, style="Card.TFrame")
        self.ports_container.pack(side="left", fill="x", expand=True)

        ttk.Button(
            port_row,
            text="Portları Yenile / Bağla",
            style="Secondary.TButton",
            command=lambda: self.refresh_ports(initial=False, force_reopen=True),
        ).pack(side="right", padx=(4, 0))

        ttk.Button(
            port_row,
            text="MCC Kapat & USB Onar",
            style="Action.TButton",
            command=self.repair_minilab_usb,
        ).pack(side="right", padx=4)

        out_row = ttk.Frame(hdr, style="Card.TFrame")
        out_row.pack(fill="x", pady=(6, 0))
        ttk.Label(
            out_row,
            text="Geçici mioXM MIDI Out Dağıtıcı (<0.2ms Thru):",
            style="Card.TLabel",
            foreground="#f2cc60",
            font=("Segoe UI", 9, "bold"),
        ).pack(side="left", padx=(0, 8))
        self.out_ports_container = ttk.Frame(out_row, style="Card.TFrame")
        self.out_ports_container.pack(side="left", fill="x", expand=True)

        din_spin = ttk.Spinbox(
            out_row,
            from_=0,
            to=60,
            width=4,
            textvariable=self.din_delay_ms_var,
            command=lambda: self._on_din_delay_changed(),
        )
        din_spin.pack(side="right")
        din_spin.bind("<Return>", lambda _e: self._on_din_delay_changed())
        din_spin.bind("<FocusOut>", lambda _e: self._on_din_delay_changed())
        ttk.Label(
            out_row,
            text="SH-4d 5-Pin DIN Telafi (ms):",
            style="Card.TLabel",
            foreground="#79c0ff",
            font=("Segoe UI", 9, "bold"),
        ).pack(side="right", padx=(10, 4))

        # 2. Live Transport, BPM & Hardware Hit Counters Bar
        dash = ttk.Frame(self.root, style="Card.TFrame", padding=8)
        dash.pack(fill="x", padx=10, pady=4)

        self.lbl_transport = self._make_metric_box(dash, "TRANSPORT", "IDLE")
        self.lbl_bpm = self._make_metric_box(dash, "24 PPQN SAAT (0xF8)", "--.- BPM  (1.1)")
        self.lbl_sh4d_kick = self._make_metric_box(dash, "SH-4d KICK (Ch5 N36)", "0")
        self.lbl_d1_kick = self._make_metric_box(dash, "DONNER D1 KICK (Ch10 N36)", "0")
        self.lbl_snare = self._make_metric_box(dash, "SNARE (D1:37 / SH4d:38)", "0 / 0")
        self.lbl_rc505 = self._make_metric_box(dash, "RC-505 FX/KILL (Ch14)", "0")

        # 3. Filters & Action Toolbar
        bar = ttk.Frame(self.root, style="Card.TFrame", padding=8)
        bar.pack(fill="x", padx=10, pady=4)

        for text, var in [
            ("Note ON", self.flt_note_on),
            ("Note OFF", self.flt_note_off),
            ("CC", self.flt_cc),
            ("Pitch Bend", self.flt_pb),
            ("FA/FC", self.flt_transport),
            ("SysEx", self.flt_sysex),
            ("0xF8 Satırları", self.flt_clock),
            ("Oto-Kaydır", self.flt_autoscroll),
        ]:
            ttk.Checkbutton(bar, text=text, variable=var, style="Card.TCheckbutton").pack(side="left", padx=4)

        ttk.Label(bar, text=" | Kanal:", style="Card.TLabel").pack(side="left", padx=(6, 4))
        ch_combo = ttk.Combobox(
            bar,
            textvariable=self.flt_channel,
            values=["All"] + [str(i) for i in range(1, 17)],
            width=5,
            state="readonly",
        )
        ch_combo.pack(side="left", padx=(0, 8))

        ttk.Button(bar, text="Log Kaydet (.txt)", style="Secondary.TButton", command=self.save_log).pack(
            side="right", padx=3
        )
        ttk.Button(bar, text="Kopyala", style="Secondary.TButton", command=self.copy_log).pack(
            side="right", padx=3
        )
        ttk.Button(bar, text="Temizle / Sıfırla", style="Secondary.TButton", command=self.clear_all).pack(
            side="right", padx=3
        )
        self.btn_pause = ttk.Button(bar, text="Duraklat", style="Action.TButton", command=self.toggle_pause)
        self.btn_pause.pack(side="right", padx=3)

        # 4. Main Event Table (Treeview)
        table_frame = ttk.Frame(self.root, style="Card.TFrame")
        table_frame.pack(fill="both", expand=True, padx=10, pady=(4, 10))

        cols = ("time", "delta", "port", "hex", "ch", "type", "detail", "target")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="extended")
        headings = [
            ("time", "Saat", 95, "center"),
            ("delta", "Δt (ms)", 75, "e"),
            ("port", "MIDI Portu", 145, "w"),
            ("hex", "Ham Hex", 110, "center"),
            ("ch", "Kanal", 60, "center"),
            ("type", "Mesaj Türü", 120, "w"),
            ("detail", "Nota / CC / Değer Detayı", 370, "w"),
            ("target", "Hedef Cihaz (CIHAZLARIM.md)", 210, "w"),
        ]
        for col_id, title, width, anchor in headings:
            self.tree.heading(col_id, text=title)
            self.tree.column(col_id, width=width, anchor=anchor)

        # Color-coded tags for instant readability
        self.tree.tag_configure("d1_drum", foreground="#58a6ff")       # Bright Blue for Donner D1 Ch 10
        self.tree.tag_configure("sh4d_drum", foreground="#79c0ff")     # Light Cyan for SH-4d Ch 5
        self.tree.tag_configure("note_on", foreground="#3fb950")       # Green for Synth Note ON
        self.tree.tag_configure("note_off", foreground="#6e7681")      # Muted Gray for Note OFF
        self.tree.tag_configure("cc", foreground="#d2a8ff")            # Lavender for MIDI CC
        self.tree.tag_configure("rc505", foreground="#ffa657")         # Orange for RC-505 Ch 14 FX/Kill
        self.tree.tag_configure("pb", foreground="#f2cc60")            # Gold for Pitch Bend
        self.tree.tag_configure("transport", foreground="#ff7b72")     # Coral Red for START/STOP
        self.tree.tag_configure("clock", foreground="#484f58")         # Dim Gray for raw 0xF8
        self.tree.tag_configure("sysex", foreground="#a5d6ff")         # Ice Blue for SysEx

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

    def _make_metric_box(self, parent, title: str, initial_val: str) -> ttk.Label:
        box = ttk.Frame(parent, style="Card.TFrame", padding=(10, 4))
        box.pack(side="left", fill="x", expand=True, padx=4)
        ttk.Label(box, text=title, style="MetricTitle.TLabel").pack(anchor="w")
        val_lbl = ttk.Label(box, text=initial_val, style="MetricVal.TLabel")
        val_lbl.pack(anchor="w", pady=(2, 0))
        return val_lbl

    # --------------------------------------------------------------------------
    # Port Management & Hot-Plug Auto-Connect
    # --------------------------------------------------------------------------
    def refresh_ports(self, initial: bool = False, force_reopen: bool = False):
        ports = list_midi_inputs()
        port_names = [name for _, name in ports]
        self.known_port_names = port_names

        # Close removed ports (or all open ports when user clicks 'Portları Yenile / Bağla' to heal stale USB handles!)
        if force_reopen:
            self._last_sent_din_delay = None
        for old_name in list(self.open_ports.keys()):
            if force_reopen or (old_name not in port_names) or self.open_ports[old_name].dead:
                self.open_ports.pop(old_name).close()
                if "minilab" in old_name.lower():
                    self._last_sent_din_delay = None

        for child in self.ports_container.winfo_children():
            child.destroy()

        if not ports:
            ttk.Label(
                self.ports_container,
                text="Hiçbir MIDI girişi bulunamadı (MiniLab 3 USB kablosunu veya ses kartını takın)",
                foreground="#ff7b72",
                background="#171d24",
            ).pack(side="left")
            self._update_status_banner()
            return

        has_minilab = any("minilab" in n.lower() for _, n in ports)
        has_any_minilab_checked = any(
            v.get() for k, v in self.port_vars.items() if "minilab" in k.lower()
        )

        for dev_id, name in ports:
            low = name.lower()
            is_primary_minilab = ("minilab" in low) and ("midi" in low) and ("thru" not in low)
            if name not in self.port_vars:
                is_fallback_din = (not has_minilab) and initial and (len(ports) == 1 or "umc" in low or "midi" in low)
                self.port_vars[name] = tk.BooleanVar(value=(is_primary_minilab or is_fallback_din))
            elif is_primary_minilab and (force_reopen or not self.auto_connected_minilab or not has_any_minilab_checked):
                self.port_vars[name].set(True)

            cb = ttk.Checkbutton(
                self.ports_container,
                text=f"[{dev_id}] {name}",
                variable=self.port_vars[name],
                style="Card.TCheckbutton",
                command=lambda: self._sync_selected_ports(manual=True),
            )
            cb.pack(side="left", padx=6)

        if has_minilab:
            self.auto_connected_minilab = True

        self.refresh_out_ports(force_reopen=force_reopen)
        self._sync_selected_ports(manual=False)

    def refresh_out_ports(self, force_reopen: bool = False):
        out_ports = list_thru_midi_outputs()
        out_names = [name for _, name in out_ports]
        self.known_out_names = out_names

        for old_name in list(self.open_out_ports.keys()):
            if force_reopen or (old_name not in out_names):
                h = self.open_out_ports.pop(old_name)
                if h.value:
                    winmm.midiOutReset(h)
                    winmm.midiOutClose(h)

        for child in self.out_ports_container.winfo_children():
            child.destroy()

        if not out_ports:
            ttk.Label(
                self.out_ports_container,
                text="(Harici MIDI Out portu yok — UMC1820 veya USB üzerinden B1/D1 takabilirsiniz)",
                foreground="#8b949e",
                background="#171d24",
            ).pack(side="left")
            self._sync_selected_out_ports()
            return

        has_any_out_checked = any(v.get() for v in self.out_port_vars.values())
        for dev_id, name in out_ports:
            is_umc = "umc" in name.lower()
            if name not in self.out_port_vars:
                self.out_port_vars[name] = tk.BooleanVar(value=is_umc)
            elif is_umc and force_reopen and not has_any_out_checked:
                self.out_port_vars[name].set(True)
            cb = ttk.Checkbutton(
                self.out_ports_container,
                text=f"→ [{dev_id}] {name}",
                variable=self.out_port_vars[name],
                style="Card.TCheckbutton",
                command=self._sync_selected_out_ports,
            )
            cb.pack(side="left", padx=6)

        self._sync_selected_out_ports()

    def _sync_selected_out_ports(self):
        id_by_name = {name: dev_id for dev_id, name in list_thru_midi_outputs()}
        for name, var in list(self.out_port_vars.items()):
            want_open = var.get() and (name in id_by_name)
            is_open = name in self.open_out_ports
            if want_open and not is_open:
                h = ctypes.c_void_p()
                if winmm.midiOutOpen(ctypes.byref(h), id_by_name[name], 0, 0, 0) == 0 and h.value:
                    self.open_out_ports[name] = h
                    self.busy_out_ports.discard(name)
                else:
                    # Keep checked (do NOT var.set(False)) so _hotplug_watchdog auto-retries UMC1820 MIDI Out for D1!
                    self.busy_out_ports.add(name)
            elif (not want_open) and is_open:
                h = self.open_out_ports.pop(name)
                self.busy_out_ports.discard(name)
                if h.value:
                    winmm.midiOutReset(h)
                    winmm.midiOutClose(h)
            elif not want_open:
                self.busy_out_ports.discard(name)

        self.thru_handles[:] = [h.value for h in self.open_out_ports.values() if h.value]
        self._sync_din_delay_to_hw()
        if hasattr(self, "status_lbl"):
            self._update_status_banner()

    def _load_saved_din_delay(self) -> int:
        try:
            with open(PREFS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return max(0, min(60, int(data.get("din_delay_ms", DEFAULT_DIN_DELAY_MS))))
        except Exception:
            return DEFAULT_DIN_DELAY_MS

    def _get_safe_din_delay_ms(self) -> int:
        try:
            val = max(0, min(60, int(self.din_delay_ms_var.get())))
        except Exception:
            val = DEFAULT_DIN_DELAY_MS
            self.din_delay_ms_var.set(val)
        return val

    def _on_din_delay_changed(self):
        val = self._get_safe_din_delay_ms()
        self.din_delay_ms_var.set(val)
        try:
            with open(PREFS_PATH, "w", encoding="utf-8") as f:
                json.dump({"din_delay_ms": val}, f)
        except Exception:
            pass
        self._sync_din_delay_to_hw(force=True)
        if hasattr(self, "status_lbl"):
            self._update_status_banner()

    def _sync_din_delay_to_hw(self, force: bool = False):
        has_minilab_open = any("minilab" in n.lower() for n in self.open_ports)
        if not has_minilab_open:
            self._last_sent_din_delay = None
            return
        target_ms = self._get_safe_din_delay_ms() if self.open_out_ports else 0
        if force or (self._last_sent_din_delay != target_ms):
            if send_minilab_din_delay_ms(target_ms):
                self._last_sent_din_delay = target_ms

    def _sync_selected_ports(self, manual: bool = False):
        id_by_name = {name: dev_id for dev_id, name in list_midi_inputs()}
        for name, p_old in list(self.open_ports.items()):
            if p_old.dead or (name not in id_by_name):
                self.open_ports.pop(name).close()
                if "minilab" in name.lower():
                    self._last_sent_din_delay = None

        for name, var in list(self.port_vars.items()):
            want_open = var.get() and (name in id_by_name)
            is_open = name in self.open_ports
            if want_open and not is_open:
                p = OpenMidiInPort(id_by_name[name], name, self.event_queue, self.thru_handles, self.thru_cfg)
                if p.open(retries=1):
                    self.open_ports[name] = p
                    self.busy_ports.discard(name)
                else:
                    # NEVER uncheck var when busy (rc=4): keep it checked so _hotplug_watchdog
                    # auto-connects the instant MIDI Control Center / Cubase / Browser releases it!
                    self.busy_ports.add(name)
                    if manual:
                        mcc_hint = (
                            "\n\nŞu an 'Arturia MIDI Control Center' AÇIK görünüyor!\n"
                            "MCC'yi kapattığınız anda otomatik bağlanacaktır (veya sağ üstteki 'MCC Kapat & USB Onar' butonuna basın)."
                            if is_mcc_running()
                            else "\n\nCubase, MIDI Control Center veya WebMIDI kullanan bir tarayıcı sekmesi portu tutuyor olabilir.\n"
                            "İlgili programı kapattığınız anda otomatik bağlanacaktır."
                        )
                        messagebox.showwarning(
                            "MIDI Port Başka Programda Açık (WinMM Kilitli)",
                            f"'{name}' portu şu an meşgul (Hata kodu: {p.last_open_rc}).{mcc_hint}",
                        )
            elif (not want_open) and is_open:
                self.open_ports.pop(name).close()
                self.busy_ports.discard(name)
                if "minilab" in name.lower():
                    self._last_sent_din_delay = None
            elif not want_open:
                self.busy_ports.discard(name)

        self._sync_din_delay_to_hw()
        self._update_status_banner()

    def _update_status_banner(self):
        active = list(self.open_ports.keys())
        open_outs = list(self.open_out_ports.keys())
        all_winmm = [n for _, n in list_midi_inputs()]
        has_minilab_winmm = any("minilab" in n.lower() for n in all_winmm)
        has_minilab_open = any("minilab" in n.lower() for n in active)

        if has_minilab_open:
            if self.busy_out_ports:
                self.status_lbl.configure(
                    text=f"⚠ Giriş bağlı ({', '.join(active)}) ama Thru ÇIKIŞI MEŞGUL: {', '.join(sorted(self.busy_out_ports))} (D1 saat alamaz!)",
                    foreground="#ffa657",
                )
            elif open_outs:
                d_ms = self._get_safe_din_delay_ms()
                d_tag = f"  [SH-4d DIN: +{d_ms}ms]" if d_ms > 0 else "  [DIN Telafi: 0ms]"
                self.status_lbl.configure(
                    text=f"● BAĞLI: {', '.join(active)}  ➔  Thru: {', '.join(open_outs)}{d_tag}",
                    foreground="#3fb950",
                )
            else:
                self.status_lbl.configure(
                    text=f"● BAĞLI ({', '.join(active)})  [Thru çıkışı seçili değil]",
                    foreground="#3fb950",
                )
            return

        if self.busy_ports:
            mcc_note = " ('MIDI Control Center' AÇIK — kapatın veya 'MCC Kapat'a basın!)" if is_mcc_running() else " (Başka program kilitliyor — kapanınca oto-bağlanacak)"
            self.status_lbl.configure(
                text=f"⏳ BEKLİYOR: {', '.join(sorted(self.busy_ports))} meşgul{mcc_note}",
                foreground="#ffa657",
            )
            return

        if not has_minilab_winmm and is_minilab_usb_physically_present():
            mcc_note = " ('MIDI Control Center' AÇIK!)" if is_mcc_running() else ""
            self.status_lbl.configure(
                text=f"⚠ MiniLab 3 USB takılı ama Windows MidiSrv kilitli{mcc_note} -> 'MCC Kapat & USB Onar'a basın veya USB çıkar-tak yapın",
                foreground="#ff7b72",
            )
            return

        if active:
            thru_txt = f"  ➔  Thru: {', '.join(open_outs)}" if open_outs else ""
            self.status_lbl.configure(
                text=f"● DİNLENİYOR: {', '.join(active)}{thru_txt}",
                foreground="#f2cc60",
            )
        else:
            self.status_lbl.configure(
                text="○ Port seçilmedi (MiniLab 3 USB bekleniyor...)",
                foreground="#ff7b72",
            )

    def repair_minilab_usb(self):
        """Closes MIDI Control Center and immediately reconnects; only restarts MidiSrv if port is missing from WinMM."""
        if is_mcc_running():
            subprocess.run(
                ["taskkill", "/IM", "MIDI Control Center.exe", "/F"],
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            time.sleep(0.6)

        self.auto_connected_minilab = False
        self.refresh_ports(initial=False, force_reopen=True)
        if any("minilab" in n.lower() for n in self.open_ports):
            return

        # Only restart Windows 11 MidiSrv via UAC if MiniLab is still invisible/broken in WinMM
        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Start-Process powershell -Verb RunAs -Wait -WindowStyle Hidden -ArgumentList '-NoProfile -Command Restart-Service MidiSrv'",
            ],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        time.sleep(1.0)
        self.auto_connected_minilab = False
        self.refresh_ports(initial=False, force_reopen=True)
        if not any("minilab" in n.lower() for n in self.open_ports):
            messagebox.showinfo(
                "USB Yeniden Eşleştirme",
                "MIDI Control Center kapatıldı.\n\n"
                "Eğer hala bağlanmadıysa MiniLab 3'ün USB kablosunu 1 saniyeliğine çıkarıp takın "
                "veya açık olan Cubase / WebMIDI tarayıcı sekmesini kapatın.",
            )

    def _hotplug_watchdog(self):
        current_names = [name for _, name in list_midi_inputs()]
        current_outs = [name for _, name in list_thru_midi_outputs()]
        has_dead = any(p.dead for p in self.open_ports.values())
        if current_names != self.known_port_names or current_outs != self.known_out_names or has_dead:
            self.refresh_ports(initial=False)
        else:
            if self.busy_out_ports or any(
                var.get() and (name in current_outs) and (name not in self.open_out_ports)
                for name, var in self.out_port_vars.items()
            ):
                self._sync_selected_out_ports()
            if self.busy_ports or any(
                var.get() and (name in current_names) and (name not in self.open_ports)
                for name, var in self.port_vars.items()
            ):
                # Auto-retry locked/busy ports every 1.5s so closing MCC/Cubase connects instantly!
                self._sync_selected_ports(manual=False)
        # Dim BPM indicator if clock stopped > 1.2s ago
        if self.last_f8_ts and (time.perf_counter() - self.last_f8_ts > 1.2):
            self.f8_times.clear()
            bar = (self.clock_ticks // 96) + 1
            beat = ((self.clock_ticks % 96) // 24) + 1
            self.lbl_bpm.configure(text=f"DURDU  ({bar}.{beat})", foreground="#8b949e")
        self.root.after(1500, self._hotplug_watchdog)

    # --------------------------------------------------------------------------
    # Real-Time Queue Polling & Decoding
    # --------------------------------------------------------------------------
    def _poll_midi_queue(self):
        processed = 0
        while processed < 250:
            try:
                ts, port_name, kind, payload = self.event_queue.get_nowait()
            except queue.Empty:
                break
            processed += 1
            self._handle_event(ts, port_name, kind, payload)

        self.root.after(15, self._poll_midi_queue)

    def _handle_event(self, ts: float, port_name: str, kind: str, payload):
        if kind == "sysex":
            hex_preview = " ".join(f"{b:02X}" for b in payload[:16])
            if len(payload) > 16:
                hex_preview += f" ... ({len(payload)}B)"
            info = {
                "category": "sysex",
                "ch": None,
                "b0": 0xF0,
                "b1": 0,
                "b2": 0,
                "hex": hex_preview[:20],
                "type": f"SysEx ({len(payload)}B)",
                "detail": hex_preview,
                "target": "SysEx / Editor",
            }
        else:
            info = decode_short_midi(payload)

        cat = info["category"]

        # Update live clock & hardware hit counters even when table is filtered!
        if cat == "clock":
            self.last_f8_ts = ts
            self.f8_times.append(ts)
            bar = (self.clock_ticks // 96) + 1
            beat = ((self.clock_ticks % 96) // 24) + 1
            self.clock_ticks += 1
            bpm_txt = "--.-"
            if len(self.f8_times) >= 6:
                span = self.f8_times[-1] - self.f8_times[0]
                if span > 0:
                    bpm = 60.0 / ((span / (len(self.f8_times) - 1)) * 24.0)
                    bpm_txt = f"{bpm:5.1f}"
            pulse = "●" if (self.clock_ticks % 24) < 6 else "○"
            self.lbl_bpm.configure(text=f"{pulse} {bpm_txt} BPM  ({bar}.{beat})", foreground="#3fb950")
        elif cat == "transport":
            if info["b0"] == 0xFA:
                self.clock_ticks = 0
                self.f8_times.clear()
                self.lbl_transport.configure(text="▶ PLAYING (0xFA)", foreground="#3fb950")
            elif info["b0"] == 0xFB:
                self.lbl_transport.configure(text="▶ CONTINUE (0xFB)", foreground="#3fb950")
            elif info["b0"] == 0xFC:
                self.lbl_transport.configure(text="■ STOPPED (0xFC)", foreground="#ff7b72")
        elif cat == "note_on":
            ch, note = info["ch"], info["b1"]
            if ch == 5 and note == 36:
                self.cnt_sh4d_kick += 1
                self.lbl_sh4d_kick.configure(text=str(self.cnt_sh4d_kick))
            elif ch == 10 and note == 36:
                self.cnt_d1_kick += 1
                self.lbl_d1_kick.configure(text=str(self.cnt_d1_kick))
            elif ch == 5 and note == 38:
                self.cnt_sh4d_snare += 1
                self.lbl_snare.configure(text=f"{self.cnt_d1_snare} / {self.cnt_sh4d_snare}")
            elif ch == 10 and note == 37:
                self.cnt_d1_snare += 1
                self.lbl_snare.configure(text=f"{self.cnt_d1_snare} / {self.cnt_sh4d_snare}")
        elif cat == "cc" and info["ch"] == 14 and info["b1"] in (80, 81, 82):
            self.cnt_rc505_cc += 1
            self.lbl_rc505.configure(text=f"{self.cnt_rc505_cc} (CC{info['b1']}={info['b2']})")

        if self.paused:
            return

        # Apply user display filters
        if cat == "clock" and not self.flt_clock.get():
            return
        if cat == "note_on" and not self.flt_note_on.get():
            return
        if cat == "note_off" and not self.flt_note_off.get():
            return
        if cat == "cc" and not self.flt_cc.get():
            return
        if cat == "pb" and not self.flt_pb.get():
            return
        if cat == "transport" and not self.flt_transport.get():
            return
        if cat == "sysex" and not self.flt_sysex.get():
            return

        ch_filter = self.flt_channel.get()
        if ch_filter != "All":
            if info["ch"] != int(ch_filter):
                return

        dt_ms = 0.0 if self.last_msg_ts is None else (ts - self.last_msg_ts) * 1000.0
        self.last_msg_ts = ts
        dt_str = f"{dt_ms:6.1f}" if dt_ms < 9999.9 else ">9999"
        exact_dt = self.t0_wall + datetime.timedelta(seconds=(ts - self.t0_perf))
        wall_str = exact_dt.strftime("%H:%M:%S.%f")[:-3]
        ch_str = f"Ch {info['ch']}" if info["ch"] is not None else "Sys"

        # Choose row highlight tag
        tag = cat
        if cat == "note_on" and info["ch"] == 10:
            tag = "d1_drum"
        elif cat == "note_on" and info["ch"] == 5:
            tag = "sh4d_drum"
        elif cat == "cc" and info["ch"] == 14:
            tag = "rc505"

        row_vals = (
            wall_str,
            dt_str,
            port_name,
            info["hex"],
            ch_str,
            info["type"],
            info["detail"],
            info["target"],
        )
        self.log_history.append("\t".join(row_vals))

        children = self.tree.get_children()
        if len(children) >= self.MAX_ROWS:
            self.tree.delete(children[0])

        item_id = self.tree.insert("", "end", values=row_vals, tags=(tag,))
        if self.flt_autoscroll.get():
            self.tree.see(item_id)

    # --------------------------------------------------------------------------
    # Toolbar Commands
    # --------------------------------------------------------------------------
    def toggle_pause(self):
        self.paused = not self.paused
        self.btn_pause.configure(text="Devam Et" if self.paused else "Duraklat")

    def clear_all(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.log_history.clear()
        self.last_msg_ts = None
        self.clock_ticks = 0
        self.cnt_sh4d_kick = 0
        self.cnt_d1_kick = 0
        self.cnt_sh4d_snare = 0
        self.cnt_d1_snare = 0
        self.cnt_rc505_cc = 0
        self.lbl_sh4d_kick.configure(text="0")
        self.lbl_d1_kick.configure(text="0")
        self.lbl_snare.configure(text="0 / 0")
        self.lbl_rc505.configure(text="0")
        self.lbl_transport.configure(text="IDLE", foreground="#3fb950")

    def copy_log(self):
        header = "Time\tdt_ms\tPort\tHex\tCh\tType\tDetail\tTarget"
        text = "\n".join([header] + list(self.log_history)[-300:])
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("Kopyalandı", f"Son {min(len(self.log_history), 300)} MIDI mesajı panoya kopyalandı.")

    def save_log(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Log", "*.txt"), ("All Files", "*.*")],
            initialfile=f"minilab3_midi_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        )
        if not path:
            return
        header = "Time\tdt_ms\tPort\tHex\tCh\tType\tDetail\tTarget\n"
        with open(path, "w", encoding="utf-8") as f:
            f.write(header)
            for line in self.log_history:
                f.write(line + "\n")
        messagebox.showinfo("Kaydedildi", f"MIDI log dosyası kaydedildi:\n{path}")

    def _on_close(self):
        # Reset MiniLab 3 5-Pin DIN Sync Delay back to 0 ms (mioXM / standalone zero-delay mode) on exit!
        try:
            send_minilab_din_delay_ms(0)
        except Exception:
            pass
        self.thru_handles.clear()
        for p in list(self.open_ports.values()):
            p.close()
        self.open_ports.clear()
        for h in list(self.open_out_ports.values()):
            if h.value:
                winmm.midiOutReset(h)
                winmm.midiOutClose(h)
        self.open_out_ports.clear()
        self.root.destroy()


# ==============================================================================
# Optional Terminal / CLI Mode (--cli)
# ==============================================================================
def run_cli_monitor(show_clock: bool = False):
    q = queue.SimpleQueue()
    opened: dict[str, OpenMidiInPort] = {}

    def sync_ports():
        ports = list_midi_inputs()
        has_ml = any("minilab" in n.lower() for _, n in ports)
        for dev_id, name in ports:
            low = name.lower()
            want = (("minilab" in low) and ("mcu" not in low) and ("alv" not in low)) or (not has_ml)
            if want and name not in opened:
                p = OpenMidiInPort(dev_id, name, q, [])
                if p.open():
                    opened[name] = p
                    print(f"[CONNECTED] [{dev_id}] {name}", flush=True)

    print("=== Arturia MiniLab 3 & Dawless Chain CLI MIDI Monitor (Ctrl+C to stop) ===", flush=True)
    sync_ports()
    if not opened:
        print("[WAITING] Waiting for MiniLab 3 or MIDI interface...", flush=True)

    last_scan = time.perf_counter()
    last_ts = None
    f8_count = 0
    try:
        while True:
            now = time.perf_counter()
            if now - last_scan > 1.5:
                sync_ports()
                last_scan = now
            try:
                ts, port_name, kind, payload = q.get(timeout=0.05)
            except queue.Empty:
                continue

            if kind == "sysex":
                hex_s = " ".join(f"{b:02X}" for b in payload[:24])
                print(f"[{port_name}] SysEx ({len(payload)}B): {hex_s}", flush=True)
                continue

            info = decode_short_midi(payload)
            if info["category"] == "clock" and not show_clock:
                f8_count += 1
                if f8_count % 24 == 0:
                    print(f"[{port_name}] ● Beat {(f8_count // 24)} (24x 0xF8 Clock OK)", flush=True)
                continue

            dt = 0.0 if last_ts is None else (ts - last_ts) * 1000.0
            last_ts = ts
            ch_s = f"Ch {info['ch']:2d}" if info["ch"] else "Sys  "
            print(
                f"+{dt:6.1f}ms | {port_name:<18s} | {info['hex']:<8s} | {ch_s} | "
                f"{info['type']:<14s} | {info['detail']}  [{info['target']}]",
                flush=True,
            )
    except KeyboardInterrupt:
        print("\nStopping MIDI monitor...", flush=True)
    finally:
        for p in opened.values():
            p.close()


if __name__ == "__main__":
    if "--cli" in sys.argv:
        run_cli_monitor(show_clock=("--clock" in sys.argv))
    else:
        root_win = tk.Tk()
        app = MiniLab3MidiMonitorApp(root_win)
        root_win.mainloop()
