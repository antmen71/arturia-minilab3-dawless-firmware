import os
import struct
import zipfile
import capstone

# ==============================================================================
# Multi-pass Thumb-1 / Thumb-2 assembler for ARMv6-M (Cortex-M0+ STM32G0B1)
# ==============================================================================
class ThumbAsm:
    def __init__(self, base_addr):
        self.base_addr = base_addr
        self.items = []

    def label(self, name):
        self.items.append(('label', name))

    def align4(self):
        self.items.append(('align4',))

    def u32(self, val):
        self.items.append(('u32', val, 0))

    def u32_thumb(self, label_name):
        self.items.append(('u32', label_name, 1))

    def raw_bytes(self, b):
        self.items.append(('bytes', b))

    def emit(self, b):
        self.items.append(('ins', lambda pc, labels: b))

    def b_cond(self, cond, target_label):
        cond_map = {'eq':0, 'ne':1, 'cs':2, 'hs':2, 'cc':3, 'lo':3, 'mi':4, 'pl':5,
                    'vs':6, 'vc':7, 'hi':8, 'ls':9, 'ge':10, 'lt':11, 'gt':12, 'le':13}
        c = cond_map[cond]
        self.items.append(('bcond', c, target_label))

    def b(self, target_label):
        def gen(pc, labels):
            off = labels[target_label] - (pc + 4)
            assert -2048 <= off <= 2046 and (off & 1) == 0, f"b -> {target_label} out of range: {off} at 0x{pc:x}"
            return struct.pack('<H', 0xE000 | ((off >> 1) & 0x7FF))
        self.items.append(('ins', gen))

    def bl(self, target_label):
        def gen(pc, labels):
            offset = labels[target_label] - (pc + 4)
            assert -16777216 <= offset <= 16777214 and (offset & 1) == 0
            S = (offset >> 24) & 1
            I1 = (offset >> 23) & 1
            I2 = (offset >> 22) & 1
            imm10 = (offset >> 12) & 0x3FF
            imm11 = (offset >> 1) & 0x7FF
            J1 = (~(I1 ^ S)) & 1
            J2 = (~(I2 ^ S)) & 1
            hw1 = 0xF000 | (S << 10) | imm10
            hw2 = 0xD000 | (J1 << 13) | (J2 << 11) | imm11
            return struct.pack('<HH', hw1, hw2)
        self.items.append(('ins4', gen))

    def ldr_lit(self, rt, lit_label):
        def gen(pc, labels):
            aligned_pc = (pc + 4) & ~3
            off = labels[lit_label] - aligned_pc
            assert 0 <= off <= 1020 and (off & 3) == 0, f"ldr_lit {lit_label} range/align: off={off} (pc=0x{pc:x}, lit=0x{labels[lit_label]:x})"
            return struct.pack('<H', 0x4800 | (rt << 8) | (off >> 2))
        self.items.append(('ins', gen))

    def build(self):
        far_set = set()
        while True:
            labels = {}
            pcs = []
            pc = self.base_addr
            for idx, item in enumerate(self.items):
                kind = item[0]
                pcs.append(pc)
                if kind == 'label':
                    assert item[1] not in labels, f"Duplicate label {item[1]}"
                    labels[item[1]] = pc
                elif kind == 'align4':
                    if pc & 1: pc += 1
                    if pc & 2: pc += 2
                elif kind == 'u32':
                    pc += 4
                elif kind == 'bytes':
                    pc += len(item[1])
                elif kind == 'ins':
                    pc += 2
                elif kind == 'ins4':
                    pc += 4
                elif kind == 'bcond':
                    pc += 4 if idx in far_set else 2
            changed = False
            for idx, item in enumerate(self.items):
                if item[0] == 'bcond' and idx not in far_set:
                    off = labels[item[2]] - (pcs[idx] + 4)
                    if not (-256 <= off <= 254):
                        far_set.add(idx)
                        changed = True
            if not changed:
                break

        out = bytearray()
        pc = self.base_addr
        for idx, item in enumerate(self.items):
            kind, *rest = item
            if kind == 'label':
                pass
            elif kind == 'align4':
                if pc & 1:
                    out += b'\x00'
                    pc += 1
                if pc & 2:
                    out += struct.pack('<H', 0x46C0)
                    pc += 2
            elif kind == 'u32':
                val, or_bit = rest
                if isinstance(val, str):
                    val = labels[val] | or_bit
                out += struct.pack('<I', val)
                pc += 4
            elif kind == 'bytes':
                out += rest[0]
                pc += len(rest[0])
            elif kind == 'ins':
                b = rest[0](pc, labels)
                assert len(b) == 2
                out += b
                pc += 2
            elif kind == 'ins4':
                b = rest[0](pc, labels)
                assert len(b) == 4
                out += b
                pc += 4
            elif kind == 'bcond':
                c, target_label = rest
                if idx not in far_set:
                    off = labels[target_label] - (pc + 4)
                    assert -256 <= off <= 254 and (off & 1) == 0
                    out += struct.pack('<H', 0xD000 | (c << 8) | ((off >> 1) & 0xFF))
                    pc += 2
                else:
                    off2 = labels[target_label] - (pc + 6)
                    assert -2048 <= off2 <= 2046 and (off2 & 1) == 0
                    hw_skip = 0xD000 | ((c ^ 1) << 8) | 0
                    hw_b    = 0xE000 | ((off2 >> 1) & 0x7FF)
                    out += struct.pack('<HH', hw_skip, hw_b)
                    pc += 4
        return bytes(out), labels

def movs_imm(rd, imm8): return struct.pack('<H', 0x2000 | (rd << 8) | (imm8 & 0xFF))
def cmp_imm(rn, imm8):  return struct.pack('<H', 0x2800 | (rn << 8) | (imm8 & 0xFF))
def adds_imm8(rdn, imm8): return struct.pack('<H', 0x3000 | (rdn << 8) | (imm8 & 0xFF))
def subs_imm8(rdn, imm8): return struct.pack('<H', 0x3800 | (rdn << 8) | (imm8 & 0xFF))
def adds_imm3(rd, rn, imm3): return struct.pack('<H', 0x1C00 | ((imm3 & 7) << 6) | (rn << 3) | rd)
def subs_imm3(rd, rn, imm3): return struct.pack('<H', 0x1E00 | ((imm3 & 7) << 6) | (rn << 3) | rd)
def adds_reg(rd, rn, rm): return struct.pack('<H', 0x1800 | (rm << 6) | (rn << 3) | rd)
def subs_reg(rd, rn, rm): return struct.pack('<H', 0x1A00 | (rm << 6) | (rn << 3) | rd)
def movs_reg(rd, rm): return struct.pack('<H', 0x0000 | (rm << 3) | rd)
def mov_hi(rd, rm):
    D = (rd >> 3) & 1
    return struct.pack('<H', 0x4600 | (D << 7) | ((rm & 0xF) << 3) | (rd & 7))
def lsls_imm(rd, rm, imm5): return struct.pack('<H', 0x0000 | ((imm5 & 0x1F) << 6) | (rm << 3) | rd)
def lsrs_imm(rd, rm, imm5): return struct.pack('<H', 0x0800 | ((imm5 & 0x1F) << 6) | (rm << 3) | rd)
def asrs_imm(rd, rm, imm5): return struct.pack('<H', 0x1000 | ((imm5 & 0x1F) << 6) | (rm << 3) | rd)
def lsls_reg(rdn, rm): return struct.pack('<H', 0x4080 | (rm << 3) | rdn)
def lsrs_reg(rdn, rm): return struct.pack('<H', 0x40C0 | (rm << 3) | rdn)
def ands_reg(rdn, rm): return struct.pack('<H', 0x4000 | (rm << 3) | rdn)
def eors_reg(rdn, rm): return struct.pack('<H', 0x4040 | (rm << 3) | rdn)
def orrs_reg(rdn, rm): return struct.pack('<H', 0x4300 | (rm << 3) | rdn)
def bics_reg(rdn, rm): return struct.pack('<H', 0x4380 | (rm << 3) | rdn)
def tst_reg(rn, rm):   return struct.pack('<H', 0x4200 | (rm << 3) | rn)
def muls_reg(rdm, rn): return struct.pack('<H', 0x4340 | (rn << 3) | rdm)
def rsbs_zero(rd, rn): return struct.pack('<H', 0x4240 | (rn << 3) | rd)
def cmp_reg(rn, rm):   return struct.pack('<H', 0x4280 | (rm << 3) | rn)
def uxtb(rd, rm):      return struct.pack('<H', 0xB2C0 | (rm << 3) | rd)
def uxth(rd, rm):      return struct.pack('<H', 0xB280 | (rm << 3) | rd)
def sxtb(rd, rm):      return struct.pack('<H', 0xB240 | (rm << 3) | rd)
def sxth(rd, rm):      return struct.pack('<H', 0xB200 | (rm << 3) | rd)
def bx(rm):            return struct.pack('<H', 0x4700 | (rm << 3))
def blx(rm):           return struct.pack('<H', 0x4780 | (rm << 3))
def sub_sp(imm_bytes): return struct.pack('<H', 0xB080 | ((imm_bytes >> 2) & 0x7F))
def add_sp(imm_bytes): return struct.pack('<H', 0xB000 | ((imm_bytes >> 2) & 0x7F))
def add_r_sp(rd, imm_bytes): return struct.pack('<H', 0xA800 | (rd << 8) | ((imm_bytes >> 2) & 0xFF))
def push(regs, lr=False):
    mask = sum(1 << r for r in regs) | (0x100 if lr else 0)
    return struct.pack('<H', 0xB400 | mask)
def pop(regs, pc=False):
    mask = sum(1 << r for r in regs) | (0x100 if pc else 0)
    return struct.pack('<H', 0xBC00 | mask)
def ldrb_imm(rt, rn, imm5): return struct.pack('<H', 0x7800 | ((imm5 & 0x1F) << 6) | (rn << 3) | rt)
def strb_imm(rt, rn, imm5): return struct.pack('<H', 0x7000 | ((imm5 & 0x1F) << 6) | (rn << 3) | rt)
def ldrh_imm(rt, rn, imm5_bytes): return struct.pack('<H', 0x8800 | (((imm5_bytes >> 1) & 0x1F) << 6) | (rn << 3) | rt)
def strh_imm(rt, rn, imm5_bytes): return struct.pack('<H', 0x8000 | (((imm5_bytes >> 1) & 0x1F) << 6) | (rn << 3) | rt)
def ldr_imm(rt, rn, imm5_bytes):  return struct.pack('<H', 0x6800 | (((imm5_bytes >> 2) & 0x1F) << 6) | (rn << 3) | rt)
def str_imm(rt, rn, imm5_bytes):  return struct.pack('<H', 0x6000 | (((imm5_bytes >> 2) & 0x1F) << 6) | (rn << 3) | rt)
def ldr_sp(rt, imm8_bytes):       return struct.pack('<H', 0x9800 | (rt << 8) | ((imm8_bytes >> 2) & 0xFF))
def str_sp(rt, imm8_bytes):       return struct.pack('<H', 0x9000 | (rt << 8) | ((imm8_bytes >> 2) & 0xFF))
def ldrb_reg(rt, rn, rm):  return struct.pack('<H', 0x5C00 | (rm << 6) | (rn << 3) | rt)
def ldrsb_reg(rt, rn, rm): return struct.pack('<H', 0x5600 | (rm << 6) | (rn << 3) | rt)
def strb_reg(rt, rn, rm):  return struct.pack('<H', 0x5400 | (rm << 6) | (rn << 3) | rt)
def ldrh_reg(rt, rn, rm):  return struct.pack('<H', 0x5A00 | (rm << 6) | (rn << 3) | rt)
def ldrsh_reg(rt, rn, rm): return struct.pack('<H', 0x5E00 | (rm << 6) | (rn << 3) | rt)
def strh_reg(rt, rn, rm):  return struct.pack('<H', 0x5200 | (rm << 6) | (rn << 3) | rt)

# ==============================================================================
# OTF_RAM (0x20022000) Layout for FW1 (OTF Live 8-Step)
# ==============================================================================
OTF_RAM        = 0x20022000
ST_MAGIC       = 0   # 0xA7
ST_PAD_HELD    = 1
ST_PAD_USED    = 2
ST_MUTE_MASK   = 3
ST_CHAIN_POS   = 4
ST_ACTIVE_STEP = 5
ST_LFSR        = 6
ST_TICKS       = 7
# +8..+15:  step_semi[0..7]
# +16..+23: step_vel[0..7]
ST_ROOT_NOTE   = 24
ST_TMP_OCT     = 25
ST_MCLK_ACT    = 26
ST_PLAYING     = 27
ST_LAST_US     = 28  # u32
ST_PHASE_ACC   = 32  # u32
# +36: arp_armed, +37: prev_f1, +38: prev_f2, +39: prev_f3 (accessed via reg offset)
ST_ARP_ARMED   = 36
ST_PREV_F1     = 37
ST_PREV_F2     = 38
ST_PREV_F3     = 39
ST_TITLE_PTR   = 40  # u32
ST_VAL_PTR     = 44  # u32
ST_TITLE_BUF   = 48  # char[24]
ST_VAL_BUF     = 72  # char[32]
ST_SHIFT_CC    = 104 # uint8[8] (live Synth CC knob values 0..127, init 64)
ST_FADER_CC    = 112 # uint8[4] (last Synth CC fader values, init 0xFF)
ST_SIZE        = 120 # total OTF_RAM size in bytes

SCALES = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
    [0, 2, 4, 5, 7, 9, 11],
    [0, 2, 3, 5, 7, 8, 10],
    [0, 3, 5, 7, 10],
    [0, 2, 3, 5, 7, 9, 10],
    [0, 1, 4, 5, 7, 8, 10],
    [0, 2, 3, 5, 7, 8, 11],
    [0, 3, 5, 6, 7, 10],
]

def quantize_to_scale(semi, intervals):
    if semi == 0: return 0
    best = semi
    best_dist = 999
    for s in range(-24, 25):
        if (s % 12) in intervals:
            d = abs(s - semi)
            if d < best_dist or (d == best_dist and abs(s) < abs(best)):
                best_dist = d
                best = s
    return best

scale_table_bytes = bytearray()
for intervals in SCALES:
    row = bytearray(32)
    row[0] = 0x80
    for idx in range(1, 32):
        row[idx] = quantize_to_scale(idx - 16, intervals) & 0xFF
    scale_table_bytes += row

CHAINS = [
    [0,1,2,3, 4,5,6,7, 0,1,2,3, 4,5,6,7], # 0: 1-8 Linear
    [0,1,2,3, 0,1,2,3, 0,1,2,3, 0,1,2,3], # 1: 1-4 Loop A
    [4,5,6,7, 4,5,6,7, 4,5,6,7, 4,5,6,7], # 2: 5-8 Loop B
    [0,1,2,3, 0,1,2,3, 0,1,2,3, 4,5,6,7], # 3: Chain AAAB
    [0,1,2,3, 4,5,6,7, 4,5,6,7, 0,1,2,3], # 4: Chain ABBA
    [0,1,2,3, 4,5,6,7, 0,1,2,3, 7,6,5,4], # 5: A-B-A-revB
    [0,1,2,3, 3,2,1,0, 4,5,6,7, 7,6,5,4], # 6: A-revA-B-rB
    [0,1,2,3, 4,5,6,7, 7,6,5,4, 3,2,1,0], # 7: Ping-Pong
]
chain_table_bytes = b''.join(bytes(c) for c in CHAINS)
default_steps_bytes = bytes([0, 0, 12, 0, 7, 10, 0, (-2) & 0xFF])

PATCH_BASE = 0x08037180
a = ThumbAsm(PATCH_BASE)

# ==============================================================================
# ISLAND 1: Init + 8-Step Sequencer Core (Advance, Note, Vel, Shift-Aware CC Filter)
# ==============================================================================

a.label('ensure_otf_init')
a.ldr_lit(0, 'p1_otf_ram')
a.emit(ldrb_imm(1, 0, ST_MAGIC))
a.emit(cmp_imm(1, 0xA7))
a.b_cond('ne', 'do_otf_init')
a.emit(bx(14))

a.label('do_otf_init')
a.emit(push([4, 5], lr=True))
a.emit(movs_reg(4, 0))
a.emit(movs_imm(1, 0))
a.emit(movs_imm(2, ST_SIZE))
a.ldr_lit(3, 'p1_memset')
a.emit(blx(3))

a.emit(movs_reg(0, 4))
a.emit(adds_imm8(0, ST_SHIFT_CC))
a.emit(movs_imm(1, 64))
a.emit(movs_imm(2, 8))
a.ldr_lit(3, 'p1_memset')
a.emit(blx(3))

a.emit(movs_reg(0, 4))
a.emit(adds_imm8(0, ST_FADER_CC))
a.emit(movs_imm(1, 0xFF))
a.emit(movs_imm(2, 4))
a.ldr_lit(3, 'p1_memset')
a.emit(blx(3))

a.emit(movs_imm(1, 0xA7))
a.emit(strb_imm(1, 4, ST_MAGIC))
a.emit(movs_imm(1, 0x5A))
a.emit(strb_imm(1, 4, ST_LFSR))
a.emit(movs_imm(1, 60))
a.emit(strb_imm(1, 4, ST_ROOT_NOTE))
a.emit(movs_imm(1, 0xFF))
a.emit(movs_imm(2, ST_PREV_F1))
a.emit(strb_reg(1, 4, 2))
a.emit(adds_imm8(2, 1))
a.emit(strb_reg(1, 4, 2))
a.emit(adds_imm8(2, 1))
a.emit(strb_reg(1, 4, 2))

a.ldr_lit(5, 'p1_default_steps')
a.emit(movs_imm(2, 0))
a.label('init_steps_loop')
a.emit(adds_reg(3, 4, 2))
a.emit(ldrb_reg(1, 5, 2))
a.emit(strb_imm(1, 3, 8))
a.emit(movs_imm(1, 100))
a.emit(strb_imm(1, 3, 16))
a.emit(adds_imm8(2, 1))
a.emit(cmp_imm(2, 8))
a.b_cond('lo', 'init_steps_loop')

# ONLY initialize Knobs/Faders & Arp ON if currently in Mode 5!
a.ldr_lit(1, 'p1_arp_params')
a.emit(ldrh_imm(2, 1, 2))
a.emit(cmp_imm(2, 5))
a.b_cond('ne', 'init_skip_mode5')
a.bl('otf_arm_mode5_once')
a.label('init_skip_mode5')
a.emit(movs_reg(0, 4))
a.emit(pop([4, 5], pc=True))

# Helper: otf_arm_mode5_once (sets Knobs 1-8=64, Faders 1-3=0, Arp=ON once on first Mode 5 entry)
a.label('otf_arm_mode5_once')
a.ldr_lit(0, 'p1_otf_ram')
a.emit(movs_imm(2, ST_ARP_ARMED))
a.emit(ldrb_reg(1, 0, 2))
a.emit(cmp_imm(1, 0))
a.b_cond('ne', 'arm5_ret')
a.emit(movs_imm(1, 1))
a.emit(strb_reg(1, 0, 2))

a.ldr_lit(1, 'p1_knobs_base')
a.emit(movs_imm(2, 0))
a.emit(movs_imm(3, 64))
a.label('init_knobs_loop')
a.emit(strh_reg(3, 1, 2))
a.emit(adds_imm8(2, 2))
a.emit(cmp_imm(2, 16))
a.b_cond('lo', 'init_knobs_loop')

a.ldr_lit(1, 'p1_fader1_addr')
a.emit(movs_imm(3, 0))
a.emit(strh_imm(3, 1, 0))
a.emit(strh_imm(3, 1, 2))
a.emit(strh_imm(3, 1, 4))

a.ldr_lit(1, 'p1_arp_params')
a.emit(movs_imm(2, 1))
a.emit(strh_imm(2, 1, 0))
a.ldr_lit(1, 'p1_arp_handler')
a.emit(movs_imm(3, 0x4A))
a.emit(strb_reg(2, 1, 3))
a.label('arm5_ret')
a.emit(bx(14))

# Hook: otf_advance_step (0x08027EC4)
a.label('otf_advance_step')
a.emit(movs_imm(2, 0x44))
a.emit(ldrh_reg(2, 0, 2))
a.emit(cmp_imm(2, 5))
a.b_cond('eq', 'otf_adv_mode')
a.ldr_lit(2, 'p1_arp_adv_orig')
a.emit(bx(2))

a.label('otf_adv_mode')
a.emit(movs_imm(3, 0xCF))
a.emit(ldrb_reg(3, 0, 3))
a.emit(cmp_imm(3, 0))
a.b_cond('ne', 'otf_adv_run')
a.ldr_lit(2, 'p1_arp_adv_ret')
a.emit(bx(2))

a.label('otf_adv_run')
a.emit(push([4, 5, 6, 7], lr=True))
a.emit(movs_reg(4, 0))
a.bl('ensure_otf_init')
a.emit(movs_reg(5, 0))

a.emit(movs_imm(2, 1))
a.emit(movs_imm(1, 0xD4))
a.emit(strb_reg(2, 4, 1))
a.emit(adds_imm8(1, 1))
a.emit(strb_reg(2, 4, 1))
a.emit(movs_imm(2, 0))
a.emit(movs_imm(1, 0xD1))
a.emit(strb_reg(2, 4, 1))

a.emit(ldrb_imm(1, 5, 6))
a.emit(cmp_imm(1, 0))
a.b_cond('ne', 'lfsr_ok')
a.emit(movs_imm(1, 0x5A))
a.label('lfsr_ok')
a.emit(lsrs_imm(2, 1, 1))
a.emit(movs_imm(3, 1))
a.emit(ands_reg(1, 3))
a.b_cond('eq', 'lfsr_no_xor')
a.emit(movs_imm(3, 0xB8))
a.emit(eors_reg(2, 3))
a.label('lfsr_no_xor')
a.emit(strb_imm(2, 5, 6))
a.emit(ldrb_imm(1, 5, 7))
a.emit(adds_imm8(1, 1))
a.emit(strb_imm(1, 5, 7))

a.emit(movs_imm(2, 0x8D))
a.emit(lsls_imm(2, 2, 1))
a.emit(ldrb_reg(1, 4, 2))
a.emit(cmp_imm(1, 0))
a.b_cond('eq', 'not_first_step')
a.emit(movs_imm(1, 0))
a.emit(strb_reg(1, 4, 2))
a.emit(movs_imm(6, 0))
a.b('have_chain_pos')

a.label('not_first_step')
a.emit(ldrb_imm(6, 5, 4))
a.emit(adds_imm8(6, 1))

a.label('have_chain_pos')
a.ldr_lit(2, 'p1_fader3_addr')
a.emit(ldrh_imm(2, 2, 0))
a.emit(cmp_imm(2, 16))
a.b_cond('lo', 'len_16')
a.emit(cmp_imm(2, 112))
a.b_cond('hs', 'len_16')
a.emit(lsrs_imm(7, 2, 4))
a.emit(adds_imm8(7, 1))
a.b('have_chain_len')
a.label('len_16')
a.emit(movs_imm(7, 16))

a.label('have_chain_len')
a.emit(movs_imm(1, 8))
a.label('skip_check_loop')
a.emit(cmp_reg(6, 7))
a.b_cond('lo', 'pos_wrapped')
a.emit(movs_imm(6, 0))
a.label('pos_wrapped')
a.ldr_lit(2, 'p1_fader2_addr')
a.emit(ldrh_imm(2, 2, 0))
a.emit(cmp_imm(2, 127))
a.b_cond('ls', 'f2_ok')
a.emit(movs_imm(2, 0))
a.label('f2_ok')
a.emit(lsrs_imm(2, 2, 4))
a.emit(lsls_imm(2, 2, 4))
a.emit(adds_reg(2, 2, 6))
a.ldr_lit(3, 'p1_chain_table')
a.emit(ldrb_reg(0, 3, 2))

a.ldr_lit(3, 'p1_knobs_base')
a.emit(lsls_imm(2, 0, 1))
a.emit(ldrsh_reg(2, 3, 2))
a.emit(cmp_imm(2, 15))
a.b_cond('gt', 'step_resolved')

a.emit(adds_imm8(6, 1))
a.emit(subs_imm8(1, 1))
a.b_cond('ne', 'skip_check_loop')

a.label('step_resolved')
a.emit(strb_imm(6, 5, 4))
a.emit(strb_imm(0, 5, 5))
a.emit(movs_imm(2, 0xD0))
a.emit(strb_reg(0, 4, 2))
a.bl('otf_refresh_pads')
a.emit(pop([4, 5, 6, 7], pc=True))

a.label('otf_arp_event_dispatch')
a.emit(cmp_imm(3, 1))
a.b_cond('eq', 'arp_ev_stop')
a.emit(cmp_imm(3, 6))
a.b_cond('eq', 'arp_ev_ratchet_on')
a.ldr_lit(2, 'p1_arp_ev_other')
a.emit(bx(2))
a.label('arp_ev_ratchet_on')
a.ldr_lit(2, 'p1_arp_ev_note')
a.emit(bx(2))
a.label('arp_ev_stop')
a.emit(movs_reg(0, 4))
a.ldr_lit(2, 'p1_arp_stop_fn')
a.emit(blx(2))
a.bl('otf_refresh_pads')
a.ldr_lit(2, 'p1_arp_ev_after_stop')
a.emit(bx(2))

a.label('otf_arp_stop_hook')
a.emit(push([4], lr=True))
a.ldr_lit(2, 'p1_arp_stop_fn')
a.emit(blx(2))
a.bl('otf_refresh_pads')
a.emit(pop([4], pc=True))

a.label('otf_note_player_ratchet')
a.emit(cmp_imm(3, 6))
a.b_cond('eq', 'np_ratchet_on')
a.emit(cmp_imm(3, 7))
a.b_cond('eq', 'np_ratchet_off')
a.emit(bx(14))
a.label('np_ratchet_on')
a.ldr_lit(2, 'p1_np_note_on')
a.emit(bx(2))
a.label('np_ratchet_off')
a.ldr_lit(2, 'p1_np_note_off')
a.emit(bx(2))

# Literal Pool 1A
a.align4()
a.label('p1_otf_ram');           a.u32(OTF_RAM)
a.label('p1_memset');            a.u32(0x0802D1A3)
a.label('p1_knobs_base');        a.u32(0x2000129C)
a.label('p1_fader1_addr');       a.u32(0x200012AE)
a.label('p1_fader2_addr');       a.u32(0x200012B0)
a.label('p1_fader3_addr');       a.u32(0x200012B2)
a.label('p1_arp_params');        a.u32(0x2000122A)
a.label('p1_arp_handler');       a.u32(0x20005944)
a.label('p1_arp_adv_orig');      a.u32(0x08027AD5)
a.label('p1_arp_adv_ret');       a.u32(0x08027B8B)
a.label('p1_arp_ev_other');      a.u32(0x08027EE5)
a.label('p1_arp_ev_note');       a.u32(0x08027EC9)
a.label('p1_arp_ev_after_stop'); a.u32(0x08027EB7)
a.label('p1_arp_stop_fn');       a.u32(0x08027A75)
a.label('p1_np_note_on');        a.u32(0x08028B27)
a.label('p1_np_note_off');       a.u32(0x08028B2D)
a.label('p1_default_steps');     a.u32('default_steps')
a.label('p1_chain_table');       a.u32('chain_table')

# ==============================================================================
# ISLAND 1B: Note, Velocity & Shift-Aware MIDI CC Filter
# ==============================================================================

a.label('otf_get_current_note')
a.emit(push([4, 5, 6, 7], lr=True))
a.emit(movs_reg(4, 0))
a.emit(movs_imm(3, 0xCF))
a.emit(ldrb_reg(1, 4, 3))
a.emit(cmp_imm(1, 0))
a.b_cond('eq', 'ret_rest')

a.emit(movs_imm(3, 0x44))
a.emit(ldrh_reg(3, 4, 3))
a.emit(cmp_imm(3, 5))
a.b_cond('eq', 'otf_note_mode')

a.emit(movs_reg(0, 4))
a.ldr_lit(3, 'p1b_orig_get_note')
a.emit(blx(3))
a.emit(pop([4, 5, 6, 7], pc=True))

a.label('otf_note_mode')
a.bl('ensure_otf_init')
a.emit(movs_reg(5, 0))

a.emit(movs_imm(1, 0))
a.emit(movs_imm(3, 0x2A))
a.emit(strb_reg(1, 4, 3))

a.emit(ldrb_imm(2, 5, 5))
a.emit(movs_imm(3, 7))
a.emit(ands_reg(2, 3))

a.emit(ldrb_imm(1, 5, 3))
a.emit(lsrs_reg(1, 2))
a.emit(movs_imm(3, 1))
a.emit(tst_reg(1, 3))
a.b_cond('ne', 'ret_rest')

a.ldr_lit(1, 'p1b_knobs_base')
a.emit(lsls_imm(3, 2, 1))
a.emit(ldrsh_reg(6, 1, 3))
a.emit(cmp_imm(6, 15))
a.b_cond('le', 'ret_rest')

a.emit(adds_reg(3, 5, 2))
a.emit(adds_imm8(3, 8))
a.emit(movs_imm(1, 0))
a.emit(ldrsb_reg(7, 3, 1))

a.emit(movs_imm(2, 0))
a.emit(cmp_imm(6, 31))
a.b_cond('gt', 'check_mod_norm')
a.emit(subs_imm8(2, 12))
a.b('mod_done')

a.label('check_mod_norm')
a.emit(cmp_imm(6, 68))
a.b_cond('le', 'mod_done')

a.emit(cmp_imm(6, 80))
a.b_cond('gt', 'check_ratchet_2x')
a.emit(movs_imm(2, 12))
a.b('mod_done')

a.label('check_ratchet_2x')
a.emit(cmp_imm(6, 92))
a.b_cond('gt', 'check_ratchet_3x')
a.emit(movs_imm(1, 1))
a.b('set_ratchet_done')

a.label('check_ratchet_3x')
a.emit(cmp_imm(6, 104))
a.b_cond('gt', 'check_ratchet_4x')
a.emit(movs_imm(1, 2))
a.b('set_ratchet_done')

a.label('check_ratchet_4x')
a.emit(cmp_imm(6, 115))
a.b_cond('gt', 'mod_random')
a.emit(movs_imm(1, 3))

a.label('set_ratchet_done')
a.emit(movs_imm(3, 0x2A))
a.emit(strb_reg(1, 4, 3))
a.b('mod_done')

a.label('mod_random')
a.emit(ldrb_imm(7, 5, 6))
a.emit(movs_imm(3, 0x1F))
a.emit(ands_reg(7, 3))
a.emit(cmp_imm(7, 0))
a.b_cond('ne', 'rnd_nz')
a.emit(movs_imm(7, 16))
a.label('rnd_nz')
a.emit(subs_imm8(7, 16))

a.label('mod_done')
a.ldr_lit(3, 'p1b_fader1_addr')
a.emit(ldrh_imm(3, 3, 0))
a.emit(cmp_imm(3, 127))
a.b_cond('ls', 'f1_ok')
a.emit(movs_imm(3, 0))
a.label('f1_ok')
a.emit(lsrs_imm(3, 3, 4))
a.emit(movs_imm(1, 7))
a.emit(ands_reg(3, 1))
a.emit(cmp_imm(3, 0))
a.b_cond('ne', 'do_quantize')
a.emit(cmp_imm(6, 116))
a.b_cond('lt', 'skip_quantize')
a.emit(movs_imm(3, 3))

a.label('do_quantize')
a.emit(adds_imm8(7, 16))
a.emit(cmp_imm(7, 1))
a.b_cond('lt', 'restore_unquant')
a.emit(cmp_imm(7, 31))
a.b_cond('gt', 'restore_unquant')
a.emit(lsls_imm(3, 3, 5))
a.emit(adds_reg(3, 3, 7))
a.ldr_lit(1, 'p1b_scale_table')
a.emit(ldrsb_reg(7, 1, 3))
a.b('skip_quantize')

a.label('restore_unquant')
a.emit(subs_imm8(7, 16))

a.label('skip_quantize')
a.emit(ldrb_imm(0, 5, 24))
a.emit(cmp_imm(0, 127))
a.b_cond('ls', 'root_ok')
a.emit(movs_imm(0, 60))
a.label('root_ok')

a.emit(adds_reg(0, 0, 7))
a.emit(adds_reg(0, 0, 2))
a.emit(cmp_imm(0, 0))
a.b_cond('ge', 'check_max_note')
a.emit(movs_imm(0, 0))
a.b('done_note')
a.label('check_max_note')
a.emit(cmp_imm(0, 127))
a.b_cond('le', 'done_note')
a.emit(movs_imm(0, 127))
a.label('done_note')
a.emit(pop([4, 5, 6, 7], pc=True))

a.label('ret_rest')
a.emit(movs_imm(0, 0x80))
a.emit(pop([4, 5, 6, 7], pc=True))

a.label('otf_get_current_velocity')
a.emit(movs_imm(3, 0x44))
a.emit(ldrh_reg(3, 0, 3))
a.emit(cmp_imm(3, 5))
a.b_cond('eq', 'otf_vel_mode')
a.ldr_lit(3, 'p1b_orig_get_vel')
a.emit(bx(3))

a.label('otf_vel_mode')
a.ldr_lit(1, 'p1b_otf_ram')
a.emit(ldrb_imm(2, 1, 5))
a.emit(movs_imm(3, 7))
a.emit(ands_reg(2, 3))

a.ldr_lit(3, 'p1b_knobs_base')
a.emit(lsls_imm(0, 2, 1))
a.emit(ldrsh_reg(0, 3, 0))
a.emit(cmp_imm(0, 69))
a.b_cond('lt', 'vel_from_step')
a.emit(cmp_imm(0, 80))
a.b_cond('gt', 'vel_from_step')
a.emit(movs_imm(0, 127))
a.emit(bx(14))

a.label('vel_from_step')
a.emit(adds_reg(1, 1, 2))
a.emit(ldrb_imm(0, 1, 16))
a.emit(bx(14))

# Hook: otf_filter_midi_cc (0x0801179A)
# Suppresses Knobs 1-8 & Faders 1-3 CC in Mode 5 UNLESS Shift (0x16) is held!
a.label('otf_filter_midi_cc')
a.emit(ldrh_imm(2, 1, 0))
a.emit(cmp_imm(2, 0x07))
a.b_cond('lo', 'send_cc_normal')
a.emit(cmp_imm(2, 0x0E))
a.b_cond('ls', 'cc_chk_mode')
a.emit(cmp_imm(2, 0x10))
a.b_cond('lo', 'send_cc_normal')
a.emit(cmp_imm(2, 0x12))
a.b_cond('hi', 'send_cc_normal')

a.label('cc_chk_mode')
a.ldr_lit(3, 'p1b_arp_params')
a.emit(ldrh_imm(2, 3, 2))
a.emit(cmp_imm(2, 5))
a.b_cond('ne', 'send_cc_normal')

# If Shift (0x16) held -> pass live MIDI CC through to synth!
a.emit(push([0, 1, 2, 4], lr=True))
a.ldr_lit(0, 'p1b_shift_obj')
a.emit(movs_imm(1, 0x16))
a.ldr_lit(3, 'p1b_check_btn')
a.emit(blx(3))
a.emit(movs_reg(4, 0))
a.emit(pop([0, 1, 2], pc=False))
a.emit(cmp_imm(4, 0))
a.b_cond('ne', 'cc_pop_lr_pass')
a.emit(pop([4], pc=True))

a.label('cc_pop_lr_pass')
a.emit(pop([4], pc=False))
a.emit(pop([3], pc=False))
a.emit(mov_hi(14, 3))
a.label('send_cc_normal')
a.ldr_lit(3, 'p1b_orig_send_cc')
a.emit(bx(3))

# Literal Pool 1B
a.align4()
a.label('p1b_otf_ram');      a.u32(OTF_RAM)
a.label('p1b_knobs_base');   a.u32(0x2000129C)
a.label('p1b_fader1_addr');  a.u32(0x200012AE)
a.label('p1b_arp_params');   a.u32(0x2000122A)
a.label('p1b_orig_get_note');a.u32(0x08027D97)
a.label('p1b_orig_get_vel'); a.u32(0x08027D31)
a.label('p1b_orig_send_cc'); a.u32(0x08010F3D)
a.label('p1b_shift_obj');    a.u32(0x20000B5C)
a.label('p1b_check_btn');    a.u32(0x0800A7B9)
a.label('p1b_scale_table');  a.u32('scale_table')

# ==============================================================================
# ISLAND 2A: Native 2-Line OLED Parameter Display Engine + String Formatters
# ==============================================================================

a.label('otf_render_param_cb')
a.emit(push([4, 5], lr=True))
a.emit(movs_reg(4, 0))
a.ldr_lit(5, 'po_ram')

a.ldr_lit(3, 'po_clear_fn')
a.emit(blx(3))

a.emit(ldr_imm(1, 5, ST_TITLE_PTR))
a.emit(cmp_imm(1, 0))
a.b_cond('eq', 'po_skip_hdr')
a.emit(movs_reg(0, 4))
a.emit(movs_imm(2, 0))
a.ldr_lit(3, 'po_hdr_fn')
a.emit(blx(3))
a.label('po_skip_hdr')

a.emit(movs_reg(0, 4))
a.emit(movs_imm(1, 0))
a.emit(movs_imm(2, 14))
a.ldr_lit(3, 'po_setpos_fn')
a.emit(blx(3))

a.emit(ldr_imm(1, 5, ST_VAL_PTR))
a.emit(cmp_imm(1, 0))
a.b_cond('eq', 'po_skip_val')
a.ldr_lit(5, 'po_text_fn')
a.emit(movs_reg(0, 4))
a.emit(movs_imm(2, 1))
a.emit(movs_imm(3, 0))
a.emit(blx(5))
a.label('po_skip_val')

a.emit(movs_reg(0, 4))
a.ldr_lit(3, 'po_flush_fn')
a.emit(blx(3))
a.emit(pop([4, 5], pc=True))

a.label('otf_show_param')
a.emit(push([4, 5], lr=True))
a.ldr_lit(4, 'po_ram')
a.emit(str_imm(0, 4, ST_TITLE_PTR))
a.emit(str_imm(1, 4, ST_VAL_PTR))

a.ldr_lit(4, 'po_disp_mgr')
a.emit(movs_reg(0, 4))
a.ldr_lit(1, 'po_render_cb')
a.emit(movs_imm(2, 0))
a.emit(movs_imm(3, 150))
a.emit(lsls_imm(3, 3, 3))      # 1200 ms
a.ldr_lit(5, 'po_timed_fn')
a.emit(blx(5))

a.emit(movs_reg(0, 4))
a.bl('otf_render_param_cb')
a.emit(pop([4, 5], pc=True))

a.label('otf_show_arp_popup')
a.emit(push([4, 5], lr=True))
a.emit(movs_reg(4, 0))
a.ldr_lit(5, 'po_disp_arp_id')
a.emit(strh_imm(4, 5, 0))
a.ldr_lit(0, 'po_arp_ui_ctx')
a.emit(movs_reg(1, 4))
a.ldr_lit(3, 'po_set_arp_ui')
a.emit(blx(3))
a.ldr_lit(0, 'po_disp_mgr')
a.emit(movs_reg(1, 4))
a.ldr_lit(3, 'po_show_popup')
a.emit(blx(3))
a.emit(pop([4, 5], pc=True))

a.label('otf_fmt_cstr')
a.label('fc_loop')
a.emit(ldrb_imm(2, 1, 0))
a.emit(strb_imm(2, 0, 0))
a.emit(cmp_imm(2, 0))
a.b_cond('eq', 'fc_done')
a.emit(adds_imm8(0, 1))
a.emit(adds_imm8(1, 1))
a.b('fc_loop')
a.label('fc_done')
a.emit(bx(14))

a.label('otf_fmt_u8')
a.emit(cmp_imm(1, 100))
a.b_cond('lo', 'fu_lt100')
a.emit(movs_imm(2, 0x31))
a.emit(strb_imm(2, 0, 0))
a.emit(adds_imm8(0, 1))
a.emit(subs_imm8(1, 100))
a.emit(movs_reg(2, 1))
a.emit(movs_imm(3, 205))
a.emit(muls_reg(2, 3))
a.emit(lsrs_imm(2, 2, 11))
a.emit(movs_imm(3, 10))
a.emit(muls_reg(3, 2))
a.emit(subs_reg(1, 1, 3))
a.emit(adds_imm8(2, 0x30))
a.emit(strb_imm(2, 0, 0))
a.emit(adds_imm8(0, 1))
a.b('fu_ones')

a.label('fu_lt100')
a.emit(cmp_imm(1, 10))
a.b_cond('lo', 'fu_ones')
a.emit(movs_reg(2, 1))
a.emit(movs_imm(3, 205))
a.emit(muls_reg(2, 3))
a.emit(lsrs_imm(2, 2, 11))
a.emit(movs_imm(3, 10))
a.emit(muls_reg(3, 2))
a.emit(subs_reg(1, 1, 3))
a.emit(adds_imm8(2, 0x30))
a.emit(strb_imm(2, 0, 0))
a.emit(adds_imm8(0, 1))

a.label('fu_ones')
a.emit(adds_imm8(1, 0x30))
a.emit(strb_imm(1, 0, 0))
a.emit(adds_imm8(0, 1))
a.emit(movs_imm(2, 0))
a.emit(strb_imm(2, 0, 0))
a.emit(bx(14))

a.label('otf_fmt_note')
a.emit(push([4], lr=True))
a.emit(cmp_imm(1, 0))
a.b_cond('ge', 'fn_min_ok')
a.emit(movs_imm(1, 0))
a.label('fn_min_ok')
a.emit(cmp_imm(1, 127))
a.b_cond('ls', 'fn_max_ok')
a.emit(movs_imm(1, 127))
a.label('fn_max_ok')
a.emit(movs_reg(2, 1))
a.emit(movs_imm(3, 171))
a.emit(muls_reg(2, 3))
a.emit(lsrs_imm(2, 2, 11))
a.emit(movs_imm(3, 12))
a.emit(muls_reg(3, 2))
a.emit(subs_reg(1, 1, 3))
a.emit(lsls_imm(1, 1, 1))
a.ldr_lit(4, 'po_note_names')
a.emit(adds_reg(4, 4, 1))
a.emit(ldrb_imm(3, 4, 0))
a.emit(strb_imm(3, 0, 0))
a.emit(adds_imm8(0, 1))
a.emit(ldrb_imm(3, 4, 1))
a.emit(cmp_imm(3, 0x20))
a.b_cond('eq', 'fn_no_sharp')
a.emit(strb_imm(3, 0, 0))
a.emit(adds_imm8(0, 1))
a.label('fn_no_sharp')
a.emit(cmp_imm(2, 0))
a.b_cond('ne', 'fn_oct_pos')
a.emit(movs_imm(3, 0x2D))
a.emit(strb_imm(3, 0, 0))
a.emit(movs_imm(3, 0x31))
a.emit(strb_imm(3, 0, 1))
a.emit(adds_imm8(0, 2))
a.b('fn_term')
a.label('fn_oct_pos')
a.emit(subs_imm8(2, 1))
a.emit(adds_imm8(2, 0x30))
a.emit(strb_imm(2, 0, 0))
a.emit(adds_imm8(0, 1))
a.label('fn_term')
a.emit(movs_imm(3, 0))
a.emit(strb_imm(3, 0, 0))
a.emit(pop([4], pc=True))

a.label('otf_make_step_title')
a.emit(push([4, 5, 6], lr=True))
a.emit(adds_imm3(4, 0, 1))
a.emit(movs_reg(5, 1))
a.ldr_lit(6, 'po_ram')
a.emit(adds_imm8(6, ST_TITLE_BUF))
a.emit(movs_reg(0, 6))
a.ldr_lit(1, 'po_str_step_sp')
a.bl('otf_fmt_cstr')
a.emit(movs_reg(1, 4))
a.bl('otf_fmt_u8')
a.emit(movs_imm(2, 0x20))
a.emit(strb_imm(2, 0, 0))
a.emit(adds_imm8(0, 1))
a.emit(movs_reg(1, 5))
a.bl('otf_fmt_cstr')
a.emit(movs_reg(0, 6))
a.emit(pop([4, 5, 6], pc=True))

a.label('otf_show_knob_expr')
a.emit(push([4, 5, 6], lr=True))
a.emit(movs_reg(4, 0))
a.emit(movs_reg(5, 1))
a.ldr_lit(1, 'po_str_mode')
a.bl('otf_make_step_title')
a.emit(movs_reg(6, 0))

a.emit(movs_imm(0, 0))
a.emit(cmp_imm(5, 15))
a.b_cond('ls', 'ke_got_idx')
a.emit(movs_imm(0, 1))
a.emit(cmp_imm(5, 31))
a.b_cond('ls', 'ke_got_idx')
a.emit(movs_imm(0, 2))
a.emit(cmp_imm(5, 68))
a.b_cond('ls', 'ke_got_idx')
a.emit(movs_imm(0, 3))
a.emit(cmp_imm(5, 80))
a.b_cond('ls', 'ke_got_idx')
a.emit(movs_imm(0, 4))
a.emit(cmp_imm(5, 92))
a.b_cond('ls', 'ke_got_idx')
a.emit(movs_imm(0, 5))
a.emit(cmp_imm(5, 104))
a.b_cond('ls', 'ke_got_idx')
a.emit(movs_imm(0, 6))
a.emit(cmp_imm(5, 115))
a.b_cond('ls', 'ke_got_idx')
a.emit(movs_imm(0, 7))

a.label('ke_got_idx')
a.ldr_lit(4, 'po_ram')
a.emit(adds_imm8(4, ST_VAL_BUF))
a.ldr_lit(1, 'po_tbl_kmodes')
a.emit(lsls_imm(0, 0, 4))
a.emit(adds_reg(1, 1, 0))
a.emit(movs_reg(0, 4))
a.bl('otf_fmt_cstr')
a.emit(movs_reg(1, 5))
a.bl('otf_fmt_u8')
a.emit(movs_imm(2, 0x29))
a.emit(strb_imm(2, 0, 0))
a.emit(movs_imm(2, 0))
a.emit(strb_imm(2, 0, 1))

a.emit(movs_reg(0, 6))
a.emit(movs_reg(1, 4))
a.bl('otf_show_param')
a.emit(pop([4, 5, 6], pc=True))

a.label('otf_show_note_vel_popup')
a.emit(push([4, 5, 6], lr=True))
a.emit(movs_reg(4, 0))
a.emit(movs_reg(5, 2))
a.ldr_lit(6, 'po_ram')
a.emit(adds_imm8(6, ST_VAL_BUF))
a.emit(movs_reg(0, 6))
a.bl('otf_fmt_note')
a.emit(movs_imm(2, 0x20))
a.emit(strb_imm(2, 0, 0))
a.emit(strb_imm(2, 0, 1))
a.emit(movs_imm(2, 0x76))
a.emit(strb_imm(2, 0, 2))
a.emit(adds_imm8(0, 3))
a.emit(movs_reg(1, 5))
a.bl('otf_fmt_u8')
a.emit(movs_reg(0, 4))
a.emit(movs_reg(1, 6))
a.bl('otf_show_param')
a.emit(pop([4, 5, 6], pc=True))

# Literal Pool 2A (OLED Engine)
a.align4()
a.label('po_ram');         a.u32(OTF_RAM)
a.label('po_disp_mgr');    a.u32(0x20000898)
a.label('po_disp_arp_id'); a.u32(0x20000B26)
a.label('po_arp_ui_ctx');  a.u32(0x20004FCC)
a.label('po_clear_fn');    a.u32(0x0800DC01)
a.label('po_hdr_fn');      a.u32(0x080208D5)
a.label('po_setpos_fn');   a.u32(0x0800DC39)
a.label('po_text_fn');     a.u32(0x080104F5)
a.label('po_flush_fn');    a.u32(0x08010465)
a.label('po_timed_fn');    a.u32(0x080106B1)
a.label('po_set_arp_ui');  a.u32(0x080202E3)
a.label('po_show_popup');  a.u32(0x08020521)
a.label('po_render_cb');   a.u32_thumb('otf_render_param_cb')
a.label('po_note_names');  a.u32('str_note_names')
a.label('po_str_step_sp'); a.u32('str_step_sp')
a.label('po_str_mode');    a.u32('str_s_mode')
a.label('po_tbl_kmodes');  a.u32('tbl_knob_modes')

# ==============================================================================
# ISLAND 2B: RGB Pad Renderer (OTF Bank A 8-Step + Transport Pad 5/6 LEDs!)
# ==============================================================================

a.label('otf_is_led_override_active')
a.emit(push([4], lr=True))
a.ldr_lit(3, 'p2_arp_params')
a.emit(ldrh_imm(2, 3, 2))
a.emit(cmp_imm(2, 5))
a.b_cond('ne', 'led_ovr_no')

a.ldr_lit(0, 'p2_shift_obj')
a.emit(movs_imm(1, 0x16))
a.ldr_lit(2, 'p2_check_btn')
a.emit(blx(2))
a.emit(cmp_imm(0, 0))
a.b_cond('ne', 'led_ovr_no')

a.ldr_lit(4, 'p2_work_mem')
a.emit(movs_reg(0, 4))
a.emit(movs_imm(1, 3))
a.ldr_lit(2, 'p2_get_mode')
a.emit(blx(2))
a.emit(cmp_imm(0, 0))          # Pad Bank A (0) ONLY!
a.b_cond('ne', 'led_ovr_no')

a.emit(movs_reg(0, 4))
a.emit(movs_imm(1, 0x19))
a.ldr_lit(2, 'p2_get_sleep')
a.emit(blx(2))
a.emit(cmp_imm(0, 0))
a.b_cond('ne', 'led_ovr_no')

a.emit(movs_reg(0, 4))
a.emit(movs_imm(1, 0x29))
a.ldr_lit(2, 'p2_orig_cce0')
a.emit(blx(2))
a.emit(cmp_imm(0, 0))
a.b_cond('ne', 'led_ovr_no')

a.bl('ensure_otf_init')
a.bl('otf_arm_mode5_once')
a.emit(movs_imm(0, 1))
a.emit(pop([4], pc=True))
a.label('led_ovr_no')
a.emit(movs_imm(0, 0))
a.emit(pop([4], pc=True))

a.label('otf_is_transport_pad_led_active')
a.emit(push([4, 5], lr=True))
a.ldr_lit(0, 'p2_shift_obj')
a.emit(movs_imm(1, 0x16))
a.ldr_lit(2, 'p2_check_btn')
a.emit(blx(2))
a.emit(cmp_imm(0, 0))
a.b_cond('ne', 'tr_led_no')

a.ldr_lit(4, 'p2_work_mem')
a.emit(movs_reg(0, 4))
a.emit(movs_imm(1, 3))
a.ldr_lit(2, 'p2_get_mode')
a.emit(blx(2))
a.emit(cmp_imm(0, 2))
a.b_cond('eq', 'tr_led_no')
a.emit(movs_reg(5, 0))

a.emit(movs_reg(0, 4))
a.emit(movs_imm(1, 0x19))
a.ldr_lit(2, 'p2_get_sleep')
a.emit(blx(2))
a.emit(cmp_imm(0, 0))
a.b_cond('ne', 'tr_led_no')

a.emit(movs_reg(0, 4))
a.emit(movs_imm(1, 0x29))
a.ldr_lit(2, 'p2_orig_cce0')
a.emit(blx(2))
a.emit(cmp_imm(0, 0))
a.b_cond('ne', 'tr_led_no')

a.emit(cmp_imm(5, 0))
a.b_cond('ne', 'tr_led_yes')
a.ldr_lit(3, 'p2_arp_params')
a.emit(ldrh_imm(2, 3, 2))
a.emit(cmp_imm(2, 5))
a.b_cond('eq', 'tr_led_no')
a.label('tr_led_yes')
a.emit(movs_imm(0, 1))
a.emit(pop([4, 5], pc=True))
a.label('tr_led_no')
a.emit(movs_imm(0, 0))
a.emit(pop([4, 5], pc=True))

a.label('otf_compute_transport_rgb')
a.emit(cmp_imm(0, 4))
a.b_cond('ne', 'tr_rgb_pad6')
a.emit(movs_imm(2, 52))
a.emit(strb_imm(2, 1, 0))
a.emit(movs_imm(2, 0))
a.emit(strb_imm(2, 1, 1))
a.emit(movs_imm(2, 2))
a.emit(strb_imm(2, 1, 2))
a.emit(bx(14))
a.label('tr_rgb_pad6')
a.ldr_lit(2, 'p2_otf_ram')
a.emit(ldrb_imm(3, 2, ST_MAGIC))
a.emit(cmp_imm(3, 0xA7))
a.b_cond('ne', 'tr_rgb_stopped')
a.emit(ldrb_imm(3, 2, ST_PLAYING))
a.emit(cmp_imm(3, 0))
a.b_cond('eq', 'tr_rgb_stopped')
a.emit(movs_imm(2, 16))
a.emit(strb_imm(2, 1, 0))
a.emit(movs_imm(2, 126))
a.emit(strb_imm(2, 1, 1))
a.emit(movs_imm(2, 16))
a.emit(strb_imm(2, 1, 2))
a.emit(bx(14))
a.label('tr_rgb_stopped')
a.emit(movs_imm(2, 0))
a.emit(strb_imm(2, 1, 0))
a.emit(movs_imm(2, 38))
a.emit(strb_imm(2, 1, 1))
a.emit(movs_imm(2, 8))
a.emit(strb_imm(2, 1, 2))
a.emit(bx(14))

a.label('otf_compute_pad_rgb')
a.emit(push([4, 5, 6, 7], lr=True))
a.emit(movs_reg(4, 0))
a.emit(movs_reg(5, 1))
a.ldr_lit(6, 'p2_otf_ram')
a.emit(movs_imm(7, 1))
a.emit(lsls_reg(7, 4))

a.emit(ldrb_imm(1, 6, 1))
a.emit(tst_reg(1, 7))
a.b_cond('eq', 'rgb_not_held')
a.emit(movs_imm(0, 124))
a.emit(movs_imm(1, 90))
a.emit(movs_imm(2, 0))
a.b('rgb_store')

a.label('rgb_not_held')
a.ldr_lit(2, 'p2_knobs_base')
a.emit(lsls_imm(3, 4, 1))
a.emit(ldrsh_reg(3, 2, 3))

a.ldr_lit(2, 'p2_arp_handler')
a.emit(movs_imm(1, 0x4A))
a.emit(ldrb_reg(1, 2, 1))
a.emit(cmp_imm(1, 0))
a.b_cond('eq', 'rgb_not_playing')
a.emit(movs_imm(1, 0xCF))
a.emit(ldrb_reg(1, 2, 1))
a.emit(cmp_imm(1, 0))
a.b_cond('eq', 'rgb_not_playing')
a.emit(ldrb_imm(1, 6, 5))
a.emit(cmp_reg(1, 4))
a.b_cond('ne', 'rgb_not_playing')

a.emit(ldrb_imm(1, 6, 3))
a.emit(tst_reg(1, 7))
a.b_cond('ne', 'rgb_play_muted')
a.emit(cmp_imm(3, 15))
a.b_cond('le', 'rgb_play_muted')
a.emit(movs_imm(0, 16))
a.emit(movs_imm(1, 126))
a.emit(movs_imm(2, 16))
a.b('rgb_store')

a.label('rgb_play_muted')
a.emit(movs_imm(0, 90))
a.emit(movs_imm(1, 0))
a.emit(movs_imm(2, 14))
a.b('rgb_store')

a.label('rgb_not_playing')
a.emit(ldrb_imm(1, 6, 3))
a.emit(tst_reg(1, 7))
a.b_cond('eq', 'rgb_check_knob')
a.emit(movs_imm(0, 18))
a.emit(movs_imm(1, 0))
a.emit(movs_imm(2, 0))
a.b('rgb_store')

a.label('rgb_check_knob')
a.emit(cmp_imm(3, 15))
a.b_cond('gt', 'rgb_k_sub')
a.emit(movs_imm(0, 0))
a.emit(movs_imm(1, 0))
a.emit(movs_imm(2, 0))
a.b('rgb_store')

a.label('rgb_k_sub')
a.emit(cmp_imm(3, 31))
a.b_cond('gt', 'rgb_k_norm')
a.emit(movs_imm(0, 0))
a.emit(movs_imm(1, 6))
a.emit(movs_imm(2, 40))
a.b('rgb_store')

a.label('rgb_k_norm')
a.emit(cmp_imm(3, 68))
a.b_cond('gt', 'rgb_k_oct')
a.emit(movs_imm(0, 0))
a.emit(movs_imm(1, 24))
a.emit(movs_imm(2, 32))
a.b('rgb_store')

a.label('rgb_k_oct')
a.emit(cmp_imm(3, 80))
a.b_cond('gt', 'rgb_k_r2')
a.emit(movs_imm(0, 38))
a.emit(movs_imm(1, 12))
a.emit(movs_imm(2, 0))
a.b('rgb_store')

a.label('rgb_k_r2')
a.emit(cmp_imm(3, 92))
a.b_cond('gt', 'rgb_k_r3')
a.emit(movs_imm(0, 20))
a.emit(movs_imm(1, 0))
a.emit(movs_imm(2, 42))
a.b('rgb_store')

a.label('rgb_k_r3')
a.emit(cmp_imm(3, 104))
a.b_cond('gt', 'rgb_k_r4')
a.emit(movs_imm(0, 36))
a.emit(movs_imm(1, 0))
a.emit(movs_imm(2, 34))
a.b('rgb_store')

a.label('rgb_k_r4')
a.emit(cmp_imm(3, 115))
a.b_cond('gt', 'rgb_k_rnd')
a.emit(movs_imm(0, 48))
a.emit(movs_imm(1, 0))
a.emit(movs_imm(2, 18))
a.b('rgb_store')

a.label('rgb_k_rnd')
a.emit(movs_imm(0, 24))
a.emit(movs_imm(1, 28))
a.emit(movs_imm(2, 28))

a.label('rgb_store')
a.emit(strb_imm(0, 5, 0))
a.emit(strb_imm(1, 5, 1))
a.emit(strb_imm(2, 5, 2))
a.emit(pop([4, 5, 6, 7], pc=True))

a.label('otf_refresh_pads')
a.emit(push([4, 5, 6], lr=True))
a.emit(sub_sp(8))
a.ldr_lit(5, 'p2_led_mgr_if')
a.ldr_lit(6, 'p2_set_led_rgb')

a.bl('otf_is_led_override_active')
a.emit(cmp_imm(0, 0))
a.b_cond('eq', 'ref_chk_tr')

a.emit(movs_imm(4, 0))
a.label('refresh_pads_loop')
a.emit(movs_reg(0, 4))
a.emit(add_r_sp(1, 0))
a.bl('otf_compute_pad_rgb')
a.emit(movs_reg(0, 5))
a.emit(adds_imm3(1, 4, 4))
a.emit(add_r_sp(2, 0))
a.emit(blx(6))
a.emit(adds_imm8(4, 1))
a.emit(cmp_imm(4, 8))
a.b_cond('lo', 'refresh_pads_loop')
a.b('refresh_pads_done')

a.label('ref_chk_tr')
a.bl('otf_is_transport_pad_led_active')
a.emit(cmp_imm(0, 0))
a.b_cond('eq', 'refresh_pads_done')

a.emit(movs_imm(0, 4))
a.emit(add_r_sp(1, 0))
a.bl('otf_compute_transport_rgb')
a.emit(movs_reg(0, 5))
a.emit(movs_imm(1, 8))
a.emit(add_r_sp(2, 0))
a.emit(blx(6))

a.emit(movs_imm(0, 5))
a.emit(add_r_sp(1, 0))
a.bl('otf_compute_transport_rgb')
a.emit(movs_reg(0, 5))
a.emit(movs_imm(1, 9))
a.emit(add_r_sp(2, 0))
a.emit(blx(6))

a.label('refresh_pads_done')
a.emit(add_sp(8))
a.emit(pop([4, 5, 6], pc=True))

a.label('otf_set_led_rgb_hook')
a.emit(push([4, 5, 6], lr=True))
a.emit(sub_sp(8))
a.emit(movs_reg(4, 0))
a.emit(movs_reg(5, 1))
a.emit(movs_reg(6, 2))

a.emit(subs_imm3(3, 5, 4))
a.emit(cmp_imm(3, 7))
a.b_cond('hi', 'led_hook_pass')

a.bl('otf_is_led_override_active')
a.emit(cmp_imm(0, 0))
a.b_cond('eq', 'led_chk_tr')
a.emit(subs_imm3(0, 5, 4))
a.emit(add_r_sp(1, 0))
a.bl('otf_compute_pad_rgb')
a.emit(add_r_sp(6, 0))
a.b('led_hook_pass')

a.label('led_chk_tr')
a.emit(cmp_imm(5, 8))
a.b_cond('eq', 'led_do_tr')
a.emit(cmp_imm(5, 9))
a.b_cond('ne', 'led_hook_pass')
a.label('led_do_tr')
a.bl('otf_is_transport_pad_led_active')
a.emit(cmp_imm(0, 0))
a.b_cond('eq', 'led_hook_pass')
a.emit(subs_imm3(0, 5, 4))
a.emit(add_r_sp(1, 0))
a.bl('otf_compute_transport_rgb')
a.emit(add_r_sp(6, 0))

a.label('led_hook_pass')
a.emit(movs_reg(0, 4))
a.emit(movs_reg(1, 5))
a.emit(movs_reg(2, 6))
a.ldr_lit(3, 'p2_set_led_rgb')
a.emit(blx(3))
a.emit(add_sp(8))
a.emit(pop([4, 5, 6], pc=True))

# Literal Pool 2B
a.align4()
a.label('p2_otf_ram');     a.u32(OTF_RAM)
a.label('p2_knobs_base');  a.u32(0x2000129C)
a.label('p2_arp_params');  a.u32(0x2000122A)
a.label('p2_arp_handler'); a.u32(0x20005944)
a.label('p2_work_mem');    a.u32(0x20000EB8)
a.label('p2_orig_cce0');   a.u32(0x0800CCE1)
a.label('p2_get_mode');    a.u32(0x0800CE15)
a.label('p2_get_sleep');   a.u32(0x0800CE31)
a.label('p2_shift_obj');   a.u32(0x20000B5C)
a.label('p2_check_btn');   a.u32(0x0800A7B9)
a.label('p2_led_mgr_if');  a.u32(0x200007CC)
a.label('p2_set_led_rgb'); a.u32(0x0800E955)

# ==============================================================================
# ISLAND 2C: Pad Events (Shift-less Pad 5/6 + OTF Bank A Step Pads) & Key Entry
# ==============================================================================

a.label('otf_on_pad_event')
a.emit(push([4, 5, 6, 7], lr=True))
a.ldr_lit(3, 'p2c_orig_cce0')
a.emit(blx(3))
a.emit(cmp_imm(0, 1))
a.b_cond('eq', 'pad_ret_vegas')
a.emit(cmp_imm(0, 0))
a.b_cond('ne', 'pad_ret_0')

a.emit(ldrh_imm(5, 4, 2))
a.emit(subs_imm8(5, 0x1E))
a.emit(cmp_imm(5, 7))
a.b_cond('hi', 'pad_ret_0')

a.emit(movs_imm(6, 1))
a.emit(lsls_reg(6, 5))

# 1. Shift (0x16) held -> Master Play/Stop everywhere!
a.ldr_lit(0, 'p2c_shift_obj')
a.emit(movs_imm(1, 0x16))
a.ldr_lit(2, 'p2c_check_btn')
a.emit(blx(2))
a.emit(cmp_imm(0, 0))
a.b_cond('eq', 'pad_no_shift')

a.emit(ldrb_imm(3, 4, 0))
a.emit(cmp_imm(3, 0))
a.b_cond('ne', 'pad_ret_0')
a.emit(cmp_imm(5, 5))
a.b_cond('ne', 'check_shift_stop')
a.bl('otf_transport_play')
a.b('pad_ret_0')
a.label('check_shift_stop')
a.emit(cmp_imm(5, 4))
a.b_cond('ne', 'pad_ret_0')
a.bl('otf_transport_stop')
a.b('pad_ret_0')

# 2. Shift NOT held -> check pad_mode (0=Bank A, 1=Bank B, 2=DAW)
a.label('pad_no_shift')
a.ldr_lit(0, 'p2c_work_mem')
a.emit(movs_imm(1, 3))
a.ldr_lit(2, 'p2c_get_mode')
a.emit(blx(2))
a.emit(cmp_imm(0, 2))
a.b_cond('eq', 'pad_ret_0')

a.emit(cmp_imm(0, 0))
a.b_cond('ne', 'pad_shiftless_tr')
a.ldr_lit(2, 'p2c_arp_params')
a.emit(ldrh_imm(1, 2, 2))
a.emit(cmp_imm(1, 5))
a.b_cond('eq', 'pad_otf_bank_a')

# --- Shift-less Transport (Normal Presets + Pad Bank B!) ---
a.label('pad_shiftless_tr')
a.emit(ldrb_imm(3, 4, 0))
a.emit(cmp_imm(3, 1))
a.b_cond('ne', 'pad_tr_chk')
a.ldr_lit(7, 'p2c_otf_ram')
a.emit(ldrb_imm(1, 7, ST_MAGIC))
a.emit(cmp_imm(1, 0xA7))
a.b_cond('ne', 'pad_tr_chk')
a.emit(ldrb_imm(1, 7, ST_PAD_HELD))
a.emit(bics_reg(1, 6))
a.emit(strb_imm(1, 7, ST_PAD_HELD))
a.emit(ldrb_imm(1, 7, ST_PAD_USED))
a.emit(bics_reg(1, 6))
a.emit(strb_imm(1, 7, ST_PAD_USED))

a.label('pad_tr_chk')
a.emit(cmp_imm(5, 5))          # Pad 6 = START!
a.b_cond('ne', 'pad_tr_chk5')
a.emit(ldrb_imm(3, 4, 0))
a.emit(cmp_imm(3, 0))
a.b_cond('ne', 'pad_consume_no_led')
a.bl('otf_transport_play')
a.b('pad_consume_no_led')

a.label('pad_tr_chk5')
a.emit(cmp_imm(5, 4))          # Pad 5 = STOP!
a.b_cond('ne', 'pad_ret_0')
a.emit(ldrb_imm(3, 4, 0))
a.emit(cmp_imm(3, 0))
a.b_cond('ne', 'pad_consume_no_led')
a.bl('otf_transport_stop')
a.b('pad_consume_no_led')

# --- OTF 8-Step Mode on Pad Bank A ---
a.label('pad_otf_bank_a')
a.bl('ensure_otf_init')
a.emit(movs_reg(7, 0))

a.emit(ldrb_imm(3, 4, 0))
a.emit(cmp_imm(3, 1))
a.b_cond('ne', 'pad_otf_not_rel')

a.emit(ldrb_imm(1, 7, ST_PAD_HELD))
a.emit(tst_reg(1, 6))
a.b_cond('eq', 'pad_consume_no_led')
a.emit(bics_reg(1, 6))
a.emit(strb_imm(1, 7, ST_PAD_HELD))

a.emit(ldrb_imm(2, 7, ST_PAD_USED))
a.emit(tst_reg(2, 6))
a.b_cond('ne', 'pad_was_used')

a.emit(ldrb_imm(3, 7, ST_MUTE_MASK))
a.emit(eors_reg(3, 6))
a.emit(strb_imm(3, 7, ST_MUTE_MASK))
a.emit(movs_reg(4, 3))
a.emit(ands_reg(4, 6))         # r4 != 0 if muted

a.emit(movs_reg(0, 5))
a.ldr_lit(1, 'p2c_str_s_mute')
a.bl('otf_make_step_title')
a.emit(cmp_imm(4, 0))
a.b_cond('eq', 'pad_mute_act')
a.ldr_lit(1, 'p2c_str_muted')
a.b('pad_mute_show')
a.label('pad_mute_act')
a.ldr_lit(1, 'p2c_str_active')
a.label('pad_mute_show')
a.bl('otf_show_param')
a.emit(ldrb_imm(2, 7, ST_PAD_USED))

a.label('pad_was_used')
a.emit(bics_reg(2, 6))
a.emit(strb_imm(2, 7, ST_PAD_USED))
a.b('pad_consume')

a.label('pad_otf_not_rel')
a.emit(cmp_imm(3, 0))
a.b_cond('ne', 'pad_consume_no_led')

a.emit(ldrb_imm(1, 7, ST_PAD_HELD))
a.emit(orrs_reg(1, 6))
a.emit(strb_imm(1, 7, ST_PAD_HELD))
a.emit(ldrb_imm(2, 7, ST_PAD_USED))
a.emit(bics_reg(2, 6))
a.emit(strb_imm(2, 7, ST_PAD_USED))

a.label('pad_consume')
a.bl('otf_refresh_pads')
a.label('pad_consume_no_led')
a.emit(pop([4, 5, 6, 7], pc=False))
a.emit(pop([3], pc=False))
a.ldr_lit(3, 'p2c_pad_exit')
a.emit(bx(3))

a.label('pad_ret_vegas')
a.emit(movs_imm(0, 1))
a.emit(pop([4, 5, 6, 7], pc=True))

a.label('pad_ret_0')
a.emit(movs_imm(0, 0))
a.emit(pop([4, 5, 6, 7], pc=True))

# Hook: otf_on_key_press (0x0800E2EE)
a.label('otf_on_key_press')
a.emit(push([4, 5, 6, 7], lr=True))
a.ldr_lit(3, 'p2c_orig_cce0')
a.emit(blx(3))
a.emit(movs_reg(7, 0))

a.ldr_lit(2, 'p2c_arp_params')
a.emit(ldrh_imm(1, 2, 2))
a.emit(cmp_imm(1, 5))
a.b_cond('ne', 'key_normal')

a.bl('ensure_otf_init')
a.emit(movs_reg(5, 0))
a.emit(strb_imm(7, 5, 25))

a.emit(ldrb_imm(6, 5, 1))
a.ldr_lit(2, 'p2c_arp_params')
a.emit(ldrh_imm(1, 2, 0))
a.emit(cmp_imm(1, 0))
a.b_cond('ne', 'arp_is_active')
a.emit(cmp_imm(6, 0))
a.b_cond('eq', 'key_normal')
a.emit(movs_imm(1, 1))
a.emit(strh_imm(1, 2, 0))

a.label('arp_is_active')
a.ldr_lit(3, 'p2c_arp_handler')
a.emit(movs_imm(2, 0x4A))
a.emit(movs_imm(1, 1))
a.emit(strb_reg(1, 3, 2))
a.emit(str_sp(1, 28))
a.emit(movs_imm(1, 0))
a.emit(str_sp(1, 8))

a.emit(ldr_sp(1, 20))
a.emit(mov_hi(2, 11))
a.emit(adds_reg(1, 1, 2))
a.emit(uxtb(1, 1))
a.emit(movs_reg(3, 7))
a.emit(adds_imm8(3, 4))
a.emit(movs_imm(2, 12))
a.emit(muls_reg(3, 2))
a.emit(adds_reg(1, 1, 3))
a.emit(uxtb(1, 1))             # r1 = K

a.emit(mov_hi(2, 8))
a.emit(ldrb_imm(2, 2, 1))      # r2 = V

a.emit(ldrb_imm(6, 5, 1))
a.emit(cmp_imm(6, 0))
a.b_cond('ne', 'pad_step_lock')

a.emit(movs_imm(3, 0x71))
a.emit(ldrsb_reg(3, 4, 3))
a.emit(cmp_imm(3, 0))
a.b_cond('gt', 'multi_key_entry')

a.emit(strb_imm(1, 5, 24))
# Show "Root Transpose" / "C4  (60)"
a.emit(push([4]))
a.emit(movs_reg(4, 1))
a.emit(movs_reg(0, 5))
a.emit(adds_imm8(0, ST_VAL_BUF))
a.emit(movs_reg(6, 0))
a.bl('otf_fmt_note')
a.emit(movs_imm(2, 0x20))
a.emit(strb_imm(2, 0, 0))
a.emit(strb_imm(2, 0, 1))
a.emit(movs_imm(2, 0x28))
a.emit(strb_imm(2, 0, 2))
a.emit(adds_imm8(0, 3))
a.emit(movs_reg(1, 4))
a.bl('otf_fmt_u8')
a.emit(movs_imm(2, 0x29))
a.emit(strb_imm(2, 0, 0))
a.emit(movs_imm(2, 0))
a.emit(strb_imm(2, 0, 1))
a.ldr_lit(0, 'p2c_t_root')
a.emit(movs_reg(1, 6))
a.bl('otf_show_param')
a.emit(pop([4]))
a.b('check_seq_running')

a.label('multi_key_entry')
a.emit(cmp_imm(3, 7))
a.b_cond('gt', 'check_seq_running')
a.emit(cmp_imm(3, 1))
a.b_cond('ne', 'not_second_key')
a.emit(movs_imm(0, 0))
a.emit(strb_imm(0, 5, 8))
a.label('not_second_key')
a.emit(push([1, 2, 3, 4]))
a.emit(ldrb_imm(0, 5, 24))
a.emit(subs_reg(1, 1, 0))
a.emit(adds_reg(0, 5, 3))
a.emit(strb_imm(1, 0, 8))
a.emit(strb_imm(2, 0, 16))
a.emit(pop([1, 2, 3, 4]))
a.emit(push([1, 2, 4]))
a.emit(movs_reg(0, 3))
a.ldr_lit(1, 'p2c_str_s_note')
a.bl('otf_make_step_title')
a.emit(pop([1, 2, 4]))
a.emit(push([4]))
a.bl('otf_show_note_vel_popup')
a.emit(pop([4]))
a.b('check_seq_running')

a.label('pad_step_lock')
a.emit(push([1, 2, 4]))        # save K, V, KeyHandler*
a.emit(ldrb_imm(0, 5, 24))
a.emit(subs_reg(1, 1, 0))

a.emit(ldrb_imm(0, 5, 2))
a.emit(orrs_reg(0, 6))
a.emit(strb_imm(0, 5, 2))

a.emit(ldrb_imm(0, 5, 3))
a.emit(bics_reg(0, 6))
a.emit(strb_imm(0, 5, 3))

a.emit(movs_imm(0, 0))
a.emit(movs_imm(4, 0))
a.label('prog_step_loop')
a.emit(movs_imm(3, 1))
a.emit(lsls_reg(3, 0))
a.emit(tst_reg(6, 3))
a.b_cond('eq', 'prog_next_step')

a.emit(movs_reg(4, 0))
a.emit(adds_reg(3, 5, 0))
a.emit(strb_imm(1, 3, 8))
a.emit(strb_imm(2, 3, 16))

a.ldr_lit(3, 'p2c_knobs_base')
a.emit(lsls_imm(7, 0, 1))
a.emit(ldrsh_reg(7, 3, 7))
a.emit(cmp_imm(7, 16))
a.b_cond('ge', 'prog_next_step')
a.emit(lsls_imm(7, 0, 1))
a.emit(movs_imm(6, 64))
a.emit(strh_reg(6, 3, 7))
a.emit(ldrb_imm(6, 5, 1))

a.label('prog_next_step')
a.emit(adds_imm8(0, 1))
a.emit(cmp_imm(0, 8))
a.b_cond('lo', 'prog_step_loop')

a.emit(subs_imm3(3, 6, 1))
a.emit(tst_reg(6, 3))
a.b_cond('ne', 'pk_multi_t')
a.emit(movs_reg(0, 4))
a.ldr_lit(1, 'p2c_str_s_note')
a.bl('otf_make_step_title')
a.b('pk_do_pop')
a.label('pk_multi_t')
a.ldr_lit(0, 'p2c_t_multinote')
a.label('pk_do_pop')
a.emit(pop([1, 2, 4]))
a.emit(push([4]))
a.bl('otf_show_note_vel_popup')
a.emit(pop([4]))

a.label('check_seq_running')
a.emit(ldrb_imm(7, 5, 25))
a.emit(sxtb(7, 7))
a.bl('otf_refresh_pads')
a.ldr_lit(3, 'p2c_arp_handler')
a.emit(movs_imm(0, 0xCF))
a.emit(ldrb_reg(3, 3, 0))
a.emit(cmp_imm(3, 0))
a.b_cond('eq', 'key_normal')

a.emit(pop([4, 5, 6, 7], pc=False))
a.emit(movs_imm(2, 0x71))
a.emit(ldrb_reg(3, 4, 2))
a.emit(adds_imm8(3, 1))
a.emit(strb_reg(3, 4, 2))
a.emit(pop([3], pc=False))
a.ldr_lit(3, 'p2c_key_exit')
a.emit(bx(3))

a.label('key_normal')
a.emit(movs_reg(0, 7))
a.emit(pop([4, 5, 6, 7], pc=True))

a.label('otf_on_key_release')
a.ldr_lit(3, 'p2c_arp_params')
a.emit(ldrh_imm(2, 3, 0))
a.emit(cmp_imm(2, 0))
a.b_cond('eq', 'rel_normal')
a.emit(ldrh_imm(2, 3, 2))
a.emit(cmp_imm(2, 5))
a.b_cond('ne', 'rel_normal')
a.emit(movs_imm(0, 1))
a.emit(bx(14))
a.label('rel_normal')
a.ldr_lit(3, 'p2c_orig_cce0')
a.emit(bx(3))

# Literal Pool 2C
a.align4()
a.label('p2c_otf_ram');     a.u32(OTF_RAM)
a.label('p2c_knobs_base');  a.u32(0x2000129C)
a.label('p2c_arp_params');  a.u32(0x2000122A)
a.label('p2c_arp_handler'); a.u32(0x20005944)
a.label('p2c_work_mem');    a.u32(0x20000EB8)
a.label('p2c_orig_cce0');   a.u32(0x0800CCE1)
a.label('p2c_get_mode');    a.u32(0x0800CE15)
a.label('p2c_shift_obj');   a.u32(0x20000B5C)
a.label('p2c_check_btn');   a.u32(0x0800A7B9)
a.label('p2c_pad_exit');    a.u32(0x08013107)
a.label('p2c_key_exit');    a.u32(0x0800E5D1)
a.label('p2c_str_s_mute');  a.u32('str_s_mute')
a.label('p2c_str_muted');   a.u32('str_muted')
a.label('p2c_str_active');  a.u32('str_active')
a.label('p2c_str_s_note');  a.u32('str_s_note')
a.label('p2c_t_root');      a.u32('str_t_root')
a.label('p2c_t_multinote'); a.u32('str_t_multinote')

# ==============================================================================
# ISLAND 3: Master MIDI Start/Stop + 24 PPQN Clock + Control/Combo OLED Hooks
# ==============================================================================

a.label('otf_send_realtime_byte')
a.emit(push([4], lr=True))
a.emit(sub_sp(8))
a.emit(add_r_sp(2, 0))
a.emit(strb_imm(0, 2, 0))
a.emit(movs_imm(3, 0))
a.emit(strb_imm(3, 2, 1))
a.emit(strb_imm(3, 2, 2))
a.emit(movs_reg(1, 2))
a.ldr_lit(3, 'p3_midi_send3')
a.emit(blx(3))
a.emit(add_sp(8))
a.emit(pop([4], pc=True))

a.label('otf_get_micros')
a.emit(push([4], lr=True))
a.ldr_lit(2, 'p3_clock_gen')
a.emit(ldr_imm(0, 2, 8))
a.emit(ldr_imm(3, 2, 12))
a.emit(blx(3))
a.emit(pop([4], pc=True))

a.label('otf_transport_play')
a.emit(push([4, 5, 6], lr=True))
a.emit(sub_sp(24))
a.bl('ensure_otf_init')
a.emit(movs_reg(4, 0))

a.bl('otf_get_micros')
a.emit(str_imm(0, 4, 28))
a.emit(movs_imm(1, 0))
a.emit(str_imm(1, 4, 32))
a.emit(strb_imm(1, 4, 4))
a.emit(strb_imm(1, 4, 5))
a.emit(movs_imm(1, 1))
a.emit(strb_imm(1, 4, 26))
a.emit(strb_imm(1, 4, 27))

a.ldr_lit(5, 'p3_arp_handler')
a.emit(movs_imm(2, 0x8D))
a.emit(lsls_imm(2, 2, 1))
a.emit(strb_reg(1, 5, 2))

a.ldr_lit(5, 'p3_clock_gen')
a.ldr_lit(6, 'p3_clk_state')
a.emit(ldrb_imm(2, 6, 0))
a.emit(cmp_imm(2, 0))
a.b_cond('ne', 'play_send_midi')
a.ldr_lit(6, 'p3_clk_running')
a.emit(ldrb_imm(2, 6, 0))
a.emit(cmp_imm(2, 0))
a.b_cond('eq', 'play_send_midi')

a.emit(add_r_sp(0, 0))
a.emit(movs_imm(1, 0))
a.emit(movs_imm(2, 20))
a.ldr_lit(3, 'p3_memset')
a.emit(blx(3))
a.emit(add_r_sp(1, 0))
a.emit(movs_imm(2, 5))
a.emit(strb_imm(2, 1, 15))
a.emit(strb_imm(2, 1, 17))
a.emit(movs_reg(0, 5))
a.ldr_lit(3, 'p3_clk_on_ev')
a.emit(blx(3))

a.emit(add_r_sp(0, 0))
a.emit(movs_imm(1, 0))
a.emit(movs_imm(2, 20))
a.ldr_lit(3, 'p3_memset')
a.emit(blx(3))
a.emit(add_r_sp(1, 0))
a.emit(movs_imm(2, 1))
a.emit(strb_imm(2, 1, 15))
a.emit(movs_imm(2, 5))
a.emit(strb_imm(2, 1, 17))
a.emit(movs_reg(0, 5))
a.ldr_lit(3, 'p3_clk_on_ev')
a.emit(blx(3))

a.bl('otf_get_micros')
a.emit(str_imm(0, 4, 28))

a.label('play_send_midi')
a.emit(movs_imm(0, 0xFA))
a.bl('otf_send_realtime_byte')
a.emit(movs_imm(0, 0xF8))
a.bl('otf_send_realtime_byte')
a.bl('otf_refresh_pads')
a.ldr_lit(0, 'p3_t_transp')
a.ldr_lit(1, 'p3_v_play')
a.bl('otf_show_param')
a.emit(add_sp(24))
a.emit(pop([4, 5, 6], pc=True))

a.label('otf_transport_stop')
a.emit(push([4, 5], lr=True))
a.bl('ensure_otf_init')
a.emit(movs_reg(4, 0))
a.emit(ldrb_imm(1, 4, 27))
a.emit(movs_imm(2, 0))
a.emit(cmp_imm(1, 0))
a.b_cond('eq', 'stop_release_clk')
a.emit(strb_imm(2, 4, 27))
a.ldr_lit(5, 'p3_v_stop_clk')
a.b('stop_send_fc')
a.label('stop_release_clk')
a.emit(strb_imm(2, 4, 26))
a.ldr_lit(5, 'p3_v_stop_free')
a.label('stop_send_fc')
a.emit(movs_imm(0, 0xFC))
a.bl('otf_send_realtime_byte')
a.bl('otf_refresh_pads')
a.ldr_lit(0, 'p3_t_transp')
a.emit(movs_reg(1, 5))
a.bl('otf_show_param')
a.emit(pop([4, 5], pc=True))

a.label('otf_master_clock_tick')
a.emit(push([4, 5, 6], lr=True))
a.ldr_lit(3, 'p3_arp_tick')
a.emit(blx(3))

a.ldr_lit(4, 'p3_otf_ram')
a.emit(ldrb_imm(1, 4, 0))
a.emit(cmp_imm(1, 0xA7))
a.b_cond('ne', 'clk_tick_exit')
a.emit(ldrb_imm(1, 4, 26))
a.emit(cmp_imm(1, 0))
a.b_cond('eq', 'clk_tick_exit')

a.bl('otf_get_micros')
a.emit(ldr_imm(5, 4, 28))
a.emit(str_imm(0, 4, 28))

a.ldr_lit(2, 'p3_clk_state')
a.emit(ldrb_imm(2, 2, 0))
a.emit(cmp_imm(2, 0))
a.b_cond('eq', 'clk_internal_ok')
a.emit(movs_imm(2, 0))
a.emit(str_imm(2, 4, 32))
a.b('clk_tick_exit')

a.label('clk_internal_ok')
a.emit(subs_reg(5, 0, 5))
a.ldr_lit(3, 'p3_max_dt_us')
a.emit(cmp_reg(5, 3))
a.b_cond('ls', 'clk_dt_ok')
a.emit(movs_reg(5, 3))
a.label('clk_dt_ok')

a.ldr_lit(2, 'p3_centi_bpm')
a.emit(ldrh_imm(1, 2, 0))
a.ldr_lit(3, 'p3_min_cbpm')
a.emit(cmp_reg(1, 3))
a.b_cond('hs', 'cbpm_min_ok')
a.ldr_lit(1, 'p3_def_cbpm')
a.label('cbpm_min_ok')
a.ldr_lit(3, 'p3_max_cbpm')
a.emit(cmp_reg(1, 3))
a.b_cond('ls', 'cbpm_max_ok')
a.emit(movs_reg(1, 3))
a.label('cbpm_max_ok')

a.emit(muls_reg(5, 1))
a.emit(ldr_imm(6, 4, 32))
a.emit(adds_reg(6, 6, 5))

a.label('clk_emit_loop')
a.ldr_lit(3, 'p3_f8_thresh')
a.emit(cmp_reg(6, 3))
a.b_cond('lo', 'clk_save_exit')
a.emit(subs_reg(6, 3, 3) if False else subs_reg(6, 6, 3))
a.emit(str_imm(6, 4, 32))
a.emit(movs_imm(0, 0xF8))
a.bl('otf_send_realtime_byte')
a.b('clk_emit_loop')

a.label('clk_save_exit')
a.emit(str_imm(6, 4, 32))
a.label('clk_tick_exit')
a.emit(pop([4, 5, 6], pc=True))

# Literal Pool 3
a.align4()
a.label('p3_otf_ram');     a.u32(OTF_RAM)
a.label('p3_clock_gen');   a.u32(0x2000566C)
a.label('p3_clk_state');   a.u32(0x20005844)
a.label('p3_clk_running'); a.u32(0x2000586D)
a.label('p3_centi_bpm');   a.u32(0x20005870)
a.label('p3_arp_handler'); a.u32(0x20005944)
a.label('p3_midi_send3');  a.u32(0x0800DCF5)
a.label('p3_arp_tick');    a.u32(0x08027385)
a.label('p3_clk_on_ev');   a.u32(0x08029349)
a.label('p3_memset');      a.u32(0x0802D1A3)
a.label('p3_max_dt_us');   a.u32(50000)
a.label('p3_min_cbpm');    a.u32(2000)
a.label('p3_def_cbpm');    a.u32(12000)
a.label('p3_max_cbpm');    a.u32(30000)
a.label('p3_f8_thresh');   a.u32(250000000)
a.label('p3_t_transp');    a.u32('str_t_transport')
a.label('p3_v_play');      a.u32('str_v_play')
a.label('p3_v_stop_clk');  a.u32('str_v_stop_clk')
a.label('p3_v_stop_free'); a.u32('str_v_stop_free')

# ==============================================================================
# ISLAND 4: Black Knob BPM + Knobs 1-8 / Faders 1-4 2-Line OLED + Click Step 1
# ==============================================================================

a.label('otf_control_event_hook')
a.emit(cmp_imm(1, 0x0C))
a.b_cond('lo', 'fw1_fast_pass')
a.emit(cmp_imm(1, 0x14))
a.b_cond('ls', 'fw1_ctrl_enter')
a.emit(cmp_imm(1, 0x1A))
a.b_cond('lo', 'fw1_fast_pass')
a.emit(cmp_imm(1, 0x1D))
a.b_cond('ls', 'fw1_ctrl_enter')
a.label('fw1_fast_pass')
a.ldr_lit(3, 'p4_orig_on_ctrl')
a.emit(bx(3))

a.label('fw1_ctrl_enter')
a.emit(push([4, 5, 6, 7], lr=True))
a.emit(movs_reg(4, 0))         # ControlHandler*
a.emit(movs_reg(5, 1))         # phys_id
a.emit(movs_reg(6, 2))         # val_or_delta

# 1. Check DAW Pad Mode (pad_mode == 2 -> passthrough untouched)
a.ldr_lit(7, 'p4_work_mem')
a.emit(movs_reg(0, 7))
a.emit(movs_imm(1, 3))
a.ldr_lit(3, 'p4_get_mode')
a.emit(blx(3))
a.emit(cmp_imm(0, 2))
a.b_cond('eq', 'fw1_ctrl_passthrough')

# 2. Shift (0x16) held -> Smart Synth CC Engine + 2-Line Parameter/Value OLED!
a.ldr_lit(0, 'p4_shift_obj')
a.emit(movs_imm(1, 0x16))
a.ldr_lit(3, 'p4_check_btn')
a.emit(blx(3))
a.emit(cmp_imm(0, 0))
a.b_cond('eq', 'fw1_no_shift')
a.emit(cmp_imm(5, 0x0C))
a.b_cond('eq', 'fw1_ctrl_passthrough')
a.b('fw1_chk_synth_cc')

# 3. Unshifted: Check Home screen (0x29 == 0)
a.label('fw1_no_shift')
a.emit(movs_reg(0, 7))
a.emit(movs_imm(1, 0x29))
a.ldr_lit(3, 'p4_orig_cce0')
a.emit(blx(3))
a.emit(cmp_imm(0, 0))
a.b_cond('ne', 'fw1_ctrl_passthrough')

# 4. Black Main Knob (0x0C) -> Live BPM across ALL presets!
a.emit(cmp_imm(5, 0x0C))
a.b_cond('ne', 'fw1_chk_otf_ctrl')

a.emit(adds_imm3(7, 4, 4))
a.emit(movs_reg(0, 7))
a.emit(movs_reg(1, 6))
a.ldr_lit(3, 'p4_enc_accum')
a.emit(blx(3))
a.emit(movs_imm(2, 0))
a.emit(ldrsh_reg(6, 7, 2))
a.emit(cmp_imm(6, 1))
a.b_cond('gt', 'fw1_have_detent')
a.emit(adds_imm3(2, 6, 1))
a.b_cond('lt', 'fw1_have_detent')
a.emit(movs_imm(0, 1))
a.emit(pop([4, 5, 6, 7], pc=True))

a.label('fw1_have_detent')
a.emit(lsrs_imm(2, 6, 31))
a.emit(adds_reg(6, 6, 2))
a.emit(asrs_imm(6, 6, 1))
a.emit(movs_imm(2, 0))
a.emit(strh_imm(2, 7, 0))

a.ldr_lit(7, 'p4_work_mem')
a.emit(movs_reg(0, 7))
a.emit(movs_imm(1, 6))
a.ldr_lit(3, 'p4_get_arp_p')
a.emit(blx(3))
a.emit(cmp_imm(0, 2))
a.b_cond('eq', 'fw1_just_popup')

a.emit(movs_reg(0, 7))
a.emit(movs_imm(1, 5))
a.ldr_lit(3, 'p4_get_arp_p')
a.emit(blx(3))
a.emit(adds_reg(6, 0, 6))
a.emit(cmp_imm(6, 0))
a.b_cond('ge', 'fw1_rate_min_ok')
a.emit(movs_imm(6, 0))
a.label('fw1_rate_min_ok')
a.emit(cmp_imm(6, 240))
a.b_cond('le', 'fw1_rate_max_ok')
a.emit(movs_imm(6, 240))
a.label('fw1_rate_max_ok')

a.emit(movs_reg(0, 7))
a.emit(movs_imm(1, 5))
a.emit(sxth(2, 6))
a.ldr_lit(3, 'p4_set_arp_p')
a.emit(blx(3))

a.label('fw1_just_popup')
a.emit(movs_imm(0, 0x12))
a.bl('otf_show_arp_popup')
a.emit(movs_imm(0, 1))
a.emit(pop([4, 5, 6, 7], pc=True))

# 5. Knobs 1-8 (0x0D..0x14) & Faders 1-4 (0x1A..0x1D) in OTF Mode vs Standalone Presets
a.label('fw1_chk_otf_ctrl')
a.ldr_lit(2, 'p4_arp_params')
a.emit(ldrh_imm(2, 2, 2))
a.emit(cmp_imm(2, 5))
a.b_cond('ne', 'fw1_chk_synth_cc')

a.bl('ensure_otf_init')
a.bl('otf_arm_mode5_once')
a.emit(cmp_imm(5, 0x14))
a.b_cond('hi', 'fw1_otf_faders')

# --- Knobs 1-8 in OTF Mode: direct detent accumulation (independent of MCC Relative/Absolute!) ---
a.emit(movs_reg(3, 5))
a.emit(subs_imm8(3, 0x0C))
a.emit(lsls_imm(0, 3, 1))
a.emit(adds_reg(0, 0, 3))
a.emit(lsls_imm(0, 0, 2))
a.emit(adds_reg(7, 4, 0))
a.emit(adds_imm3(7, 7, 4))
a.emit(movs_reg(0, 7))
a.emit(movs_reg(1, 6))
a.ldr_lit(3, 'p4_enc_accum')
a.emit(blx(3))
a.emit(movs_imm(2, 0))
a.emit(ldrsh_reg(6, 7, 2))
a.emit(cmp_imm(6, 1))
a.b_cond('gt', 'fw1_otf_k_det')
a.emit(adds_imm3(2, 6, 1))
a.b_cond('lt', 'fw1_otf_k_det')
a.emit(movs_imm(0, 1))
a.emit(pop([4, 5, 6, 7], pc=True))

a.label('fw1_otf_k_det')
a.emit(lsrs_imm(2, 6, 31))
a.emit(adds_reg(6, 6, 2))
a.emit(asrs_imm(6, 6, 1))
a.emit(movs_imm(2, 0))
a.emit(strh_imm(2, 7, 0))

a.emit(movs_reg(7, 5))
a.emit(subs_imm8(7, 0x0D))     # r7 = s (0..7)
a.ldr_lit(2, 'p4_knobs_base')
a.emit(lsls_imm(3, 7, 1))
a.emit(ldrsh_reg(4, 2, 3))
a.emit(lsls_imm(1, 6, 1))
a.emit(adds_reg(1, 1, 6))      # delta * 3
a.emit(adds_reg(4, 4, 1))
a.emit(cmp_imm(4, 0))
a.b_cond('ge', 'fw1_ok_min')
a.emit(movs_imm(4, 0))
a.label('fw1_ok_min')
a.emit(cmp_imm(4, 127))
a.b_cond('le', 'fw1_ok_max')
a.emit(movs_imm(4, 127))
a.label('fw1_ok_max')
a.emit(strh_reg(4, 2, 3))

a.bl('otf_refresh_pads')
a.emit(movs_reg(0, 7))         # step 0..7
a.emit(movs_reg(1, 4))         # knob_val 0..127
a.bl('otf_show_knob_expr')
a.emit(movs_imm(0, 1))
a.emit(pop([4, 5, 6, 7], pc=True))

# --- Faders 1-4 in OTF Mode ---
a.label('fw1_otf_faders')
a.emit(cmp_imm(5, 0x1D))
a.b_cond('eq', 'fw1_chk_synth_cc')

a.emit(movs_imm(2, 0x7F))
a.emit(ands_reg(6, 2))         # r6 = 0..127
a.ldr_lit(2, 'p4_faders_base')
a.emit(movs_reg(3, 5))
a.emit(subs_imm8(3, 0x1A))
a.emit(lsls_imm(3, 3, 1))
a.emit(strh_reg(6, 2, 3))      # update 0x200012AE[0..2] directly!

a.ldr_lit(7, 'p4_otf_ram')
a.emit(cmp_imm(5, 0x1A))
a.b_cond('ne', 'fw1_f2')
a.emit(lsrs_imm(0, 6, 4))      # 0..7 Scale
a.emit(movs_imm(2, ST_PREV_F1))
a.emit(ldrb_reg(1, 7, 2))
a.emit(cmp_reg(0, 1))
a.b_cond('eq', 'fw1_ret1')
a.emit(strb_reg(0, 7, 2))
a.ldr_lit(1, 'p4_v_scales')
a.emit(lsls_imm(0, 0, 4))
a.emit(adds_reg(1, 1, 0))
a.ldr_lit(0, 'p4_t_scale')
a.bl('otf_show_param')
a.b('fw1_ret1')

a.label('fw1_f2')
a.emit(cmp_imm(5, 0x1B))
a.b_cond('ne', 'fw1_f3')
a.emit(lsrs_imm(0, 6, 4))      # 0..7 Chain
a.emit(movs_imm(2, ST_PREV_F2))
a.emit(ldrb_reg(1, 7, 2))
a.emit(cmp_reg(0, 1))
a.b_cond('eq', 'fw1_ret1')
a.emit(strb_reg(0, 7, 2))
a.ldr_lit(1, 'p4_v_chains')
a.emit(lsls_imm(0, 0, 4))
a.emit(adds_reg(1, 1, 0))
a.ldr_lit(0, 'p4_t_dir')
a.bl('otf_show_param')
a.b('fw1_ret1')

a.label('fw1_f3')
a.emit(movs_imm(0, 16))
a.emit(cmp_imm(6, 16))
a.b_cond('lo', 'fw1_f3_got')
a.emit(cmp_imm(6, 112))
a.b_cond('hs', 'fw1_f3_got')
a.emit(lsrs_imm(0, 6, 4))
a.emit(adds_imm8(0, 1))        # 2..7
a.label('fw1_f3_got')
a.emit(movs_imm(2, ST_PREV_F3))
a.emit(ldrb_reg(1, 7, 2))
a.emit(cmp_reg(0, 1))
a.b_cond('eq', 'fw1_ret1')
a.emit(strb_reg(0, 7, 2))

a.emit(cmp_imm(0, 16))
a.b_cond('ne', 'fw1_f3_num')
a.ldr_lit(0, 'p4_t_len')
a.ldr_lit(1, 'p4_str_full_chn')
a.bl('otf_show_param')
a.b('fw1_ret1')

a.label('fw1_f3_num')
a.emit(movs_reg(5, 0))
a.emit(adds_imm8(7, ST_VAL_BUF))
a.emit(movs_reg(0, 7))
a.emit(movs_reg(1, 5))
a.bl('otf_fmt_u8')
a.ldr_lit(1, 'p4_str_steps')
a.bl('otf_fmt_cstr')
a.ldr_lit(0, 'p4_t_len')
a.emit(movs_reg(1, 7))
a.bl('otf_show_param')

a.label('fw1_ret1')
a.emit(movs_imm(0, 1))
a.emit(pop([4, 5, 6, 7], pc=True))

# Gate check before Smart Synth CC Engine (passes DAW / Analog Lab V through untouched)
a.label('fw1_chk_synth_cc')
a.ldr_lit(7, 'p4_work_mem')
a.emit(movs_reg(0, 7))
a.emit(movs_imm(1, 1))
a.ldr_lit(3, 'p4_get_mode')
a.emit(blx(3))
a.emit(cmp_imm(0, 0))
a.b_cond('eq', 'fw1_ctrl_passthrough')
a.emit(cmp_imm(0, 1))
a.b_cond('ne', 'fw1_csc_chk_daw')
a.emit(movs_reg(0, 7))
a.emit(movs_imm(1, 0x2B))
a.ldr_lit(3, 'p4_orig_cce0')
a.emit(blx(3))
a.emit(cmp_imm(0, 0))
a.b_cond('ne', 'fw1_ctrl_passthrough')

a.label('fw1_csc_chk_daw')
a.ldr_lit(2, 'p4_arp_params')
a.emit(ldrh_imm(2, 2, 2))
a.emit(cmp_imm(2, 5))
a.b_cond('eq', 'fw1_csc_go')
a.emit(movs_reg(0, 7))
a.emit(movs_imm(1, 0x2A))
a.ldr_lit(3, 'p4_orig_cce0')
a.emit(blx(3))
a.emit(cmp_imm(0, 0))
a.b_cond('ne', 'fw1_ctrl_passthrough')

a.label('fw1_csc_go')
a.emit(movs_reg(0, 4))
a.emit(movs_reg(1, 5))
a.emit(movs_reg(2, 6))
a.bl('otf_handle_synth_cc')
a.emit(pop([4, 5, 6, 7], pc=True))

a.label('fw1_ctrl_passthrough')
a.emit(movs_reg(0, 4))
a.emit(movs_reg(1, 5))
a.emit(movs_reg(2, 6))
a.ldr_lit(3, 'p4_orig_on_ctrl')
a.emit(blx(3))
a.emit(pop([4, 5, 6, 7], pc=True))

# Hook: otf_combo_event_hook (0x08012D38: Black Main Knob Click -> Step 1 Reset + 2-Line OLED)
a.label('otf_combo_event_hook')
a.emit(cmp_imm(1, 12))
a.b_cond('eq', 'fw1_main_click')
a.ldr_lit(3, 'p4_orig_on_combo')
a.emit(bx(3))

a.label('fw1_main_click')
a.ldr_lit(2, 'p4_arp_params')
a.emit(ldrh_imm(2, 2, 2))
a.emit(cmp_imm(2, 5))
a.b_cond('eq', 'fw1_do_reset_step1')
a.ldr_lit(3, 'p4_orig_on_combo')
a.emit(bx(3))

a.label('fw1_do_reset_step1')
a.emit(push([4], lr=True))
a.bl('ensure_otf_init')
a.emit(movs_imm(1, 0))
a.emit(strb_imm(1, 0, 4))
a.emit(strb_imm(1, 0, 5))
a.ldr_lit(2, 'p4_arp_handler')
a.emit(movs_imm(3, 0x8D))
a.emit(lsls_imm(3, 3, 1))
a.emit(movs_imm(1, 1))
a.emit(strb_reg(1, 2, 3))
a.bl('otf_refresh_pads')

a.ldr_lit(0, 'p4_t_sync')
a.ldr_lit(1, 'p4_str_step1')
a.bl('otf_show_param')
a.emit(movs_imm(0, 1))
a.emit(pop([4], pc=True))

# Literal Pool 4
a.align4()
a.label('p4_otf_ram');      a.u32(OTF_RAM)
a.label('p4_orig_on_ctrl'); a.u32(0x08023719)
a.label('p4_orig_on_combo');a.u32(0x08023F81)
a.label('p4_shift_obj');    a.u32(0x20000B5C)
a.label('p4_check_btn');    a.u32(0x0800A7B9)
a.label('p4_enc_accum');    a.u32(0x08024EC1)
a.label('p4_work_mem');     a.u32(0x20000EB8)
a.label('p4_orig_cce0');    a.u32(0x0800CCE1)
a.label('p4_get_mode');     a.u32(0x0800CE15)
a.label('p4_get_arp_p');    a.u32(0x0800DC29)
a.label('p4_set_arp_p');    a.u32(0x08021241)
a.label('p4_knobs_base');   a.u32(0x2000129C)
a.label('p4_faders_base');  a.u32(0x200012AE)
a.label('p4_arp_params');   a.u32(0x2000122A)
a.label('p4_arp_handler');  a.u32(0x20005944)
a.label('p4_t_scale');      a.u32('str_t_scale')
a.label('p4_v_scales');     a.u32('tbl_str_scales')
a.label('p4_t_dir');        a.u32('str_t_dir')
a.label('p4_v_chains');     a.u32('tbl_str_chains')
a.label('p4_t_len');        a.u32('str_t_looplen')
a.label('p4_str_full_chn'); a.u32('str_full_chn')
a.label('p4_str_steps');    a.u32('str_steps_sfx')
a.label('p4_t_sync');       a.u32('str_t_sync')
a.label('p4_str_step1');    a.u32('str_step1')

# ==============================================================================
# ISLAND 4B: Smart Synth MIDI CC Engine + 2-Line Parameter Name & Value OLED
# ==============================================================================

a.label('otf_send_cc_3b')
a.emit(push([4], lr=True))
a.emit(sub_sp(8))
a.emit(movs_imm(3, 0x0F))
a.emit(ands_reg(0, 3))
a.emit(movs_imm(3, 0xB0))
a.emit(orrs_reg(0, 3))
a.emit(add_r_sp(4, 0))
a.emit(strb_imm(0, 4, 0))
a.emit(movs_imm(3, 0x7F))
a.emit(ands_reg(1, 3))
a.emit(strb_imm(1, 4, 1))
a.emit(ands_reg(2, 3))
a.emit(strb_imm(2, 4, 2))
a.emit(movs_reg(1, 4))
a.ldr_lit(3, 'p4b_midi_send3')
a.emit(blx(3))
a.emit(add_sp(8))
a.emit(pop([4], pc=True))

a.label('otf_show_cc_popup')
a.emit(push([4, 5, 6, 7], lr=True))
a.emit(sub_sp(8))
a.emit(str_sp(2, 0))
a.emit(str_sp(3, 4))
a.emit(movs_reg(4, 0))
a.emit(movs_reg(5, 1))
a.ldr_lit(6, 'p4b_ram')
a.emit(adds_imm8(6, ST_TITLE_BUF))

a.emit(ldr_sp(0, 0))
a.emit(cmp_imm(0, 13))
a.b_cond('ne', 'fw1_scc_scan')
a.emit(cmp_imm(5, 1))
a.b_cond('lo', 'fw1_scc_scan')
a.emit(cmp_imm(5, 5))
a.b_cond('hi', 'fw1_scc_scan')
a.emit(movs_reg(0, 6))
a.ldr_lit(1, 'p4b_str_rc505')
a.bl('otf_fmt_cstr')
a.emit(movs_reg(1, 5))
a.bl('otf_fmt_u8')
a.b('fw1_scc_app_cc')

a.label('fw1_scc_scan')
a.ldr_lit(7, 'p4b_tbl_cc')
a.label('fw1_scc_loop')
a.emit(ldrb_imm(0, 7, 0))
a.emit(cmp_imm(0, 0xFF))
a.b_cond('eq', 'fw1_scc_fb')
a.emit(cmp_reg(0, 5))
a.b_cond('eq', 'fw1_scc_hit')
a.emit(adds_imm8(7, 12))
a.b('fw1_scc_loop')

a.label('fw1_scc_hit')
a.emit(movs_reg(0, 6))
a.emit(adds_imm3(1, 7, 1))
a.bl('otf_fmt_cstr')
a.b('fw1_scc_app_cc')

a.label('fw1_scc_fb')
a.emit(movs_reg(0, 6))
a.emit(cmp_imm(4, 0x14))
a.b_cond('hi', 'fw1_scc_fdr')
a.ldr_lit(1, 'p4b_str_knob_sp')
a.bl('otf_fmt_cstr')
a.emit(movs_reg(1, 4))
a.emit(subs_imm8(1, 0x0C))
a.bl('otf_fmt_u8')
a.b('fw1_scc_app_cc')

a.label('fw1_scc_fdr')
a.ldr_lit(1, 'p4b_str_fader_sp')
a.bl('otf_fmt_cstr')
a.emit(movs_reg(1, 4))
a.emit(subs_imm8(1, 0x19))
a.bl('otf_fmt_u8')

a.label('fw1_scc_app_cc')
a.ldr_lit(1, 'p4b_str_cc_lp')
a.bl('otf_fmt_cstr')
a.emit(movs_reg(1, 5))
a.bl('otf_fmt_u8')
a.emit(movs_imm(2, 0x29))
a.emit(strb_imm(2, 0, 0))
a.emit(movs_imm(2, 0))
a.emit(strb_imm(2, 0, 1))

a.ldr_lit(7, 'p4b_ram')
a.emit(adds_imm8(7, ST_VAL_BUF))
a.emit(movs_reg(0, 7))
a.emit(ldr_sp(1, 4))
a.bl('otf_fmt_u8')
a.ldr_lit(1, 'p4b_str_ch_lp')
a.bl('otf_fmt_cstr')
a.emit(ldr_sp(1, 0))
a.emit(adds_imm8(1, 1))
a.bl('otf_fmt_u8')
a.emit(movs_imm(2, 0x29))
a.emit(strb_imm(2, 0, 0))
a.emit(movs_imm(2, 0))
a.emit(strb_imm(2, 0, 1))

a.emit(movs_reg(0, 6))
a.emit(movs_reg(1, 7))
a.bl('otf_show_param')
a.emit(add_sp(8))
a.emit(pop([4, 5, 6, 7], pc=True))

a.label('otf_handle_synth_cc')
a.emit(push([4, 5, 6, 7], lr=True))
a.emit(movs_reg(4, 0))
a.emit(movs_reg(5, 1))
a.emit(movs_reg(6, 2))

a.emit(cmp_imm(5, 0x14))
a.b_cond('hi', 'fw1_hsc_fdr')

a.emit(movs_reg(3, 5))
a.emit(subs_imm8(3, 0x0C))
a.emit(lsls_imm(0, 3, 1))
a.emit(adds_reg(0, 0, 3))
a.emit(lsls_imm(0, 0, 2))
a.emit(adds_reg(7, 4, 0))
a.emit(adds_imm3(7, 7, 4))
a.emit(movs_reg(0, 7))
a.emit(movs_reg(1, 6))
a.ldr_lit(3, 'p4b_enc_accum')
a.emit(blx(3))
a.emit(movs_imm(2, 0))
a.emit(ldrsh_reg(6, 7, 2))
a.emit(cmp_imm(6, 1))
a.b_cond('gt', 'fw1_hsc_kdet')
a.emit(adds_imm3(2, 6, 1))
a.b_cond('lt', 'fw1_hsc_kdet')
a.b('fw1_hsc_ret1')

a.label('fw1_hsc_kdet')
a.emit(lsrs_imm(2, 6, 31))
a.emit(adds_reg(6, 6, 2))
a.emit(asrs_imm(6, 6, 1))
a.emit(movs_imm(2, 0))
a.emit(strh_imm(2, 7, 0))

a.bl('ensure_otf_init')
a.emit(adds_imm8(0, ST_SHIFT_CC))
a.emit(movs_reg(2, 5))
a.emit(subs_imm8(2, 0x0D))
a.emit(ldrb_reg(7, 0, 2))
a.emit(lsls_imm(1, 6, 1))
a.emit(adds_reg(7, 7, 1))
a.emit(cmp_imm(7, 0))
a.b_cond('ge', 'fw1_hsc_kmin')
a.emit(movs_imm(7, 0))
a.label('fw1_hsc_kmin')
a.emit(cmp_imm(7, 127))
a.b_cond('le', 'fw1_hsc_kmax')
a.emit(movs_imm(7, 127))
a.label('fw1_hsc_kmax')
a.emit(strb_reg(7, 0, 2))

a.ldr_lit(1, 'p4b_arp_params')
a.emit(ldrh_imm(1, 1, 2))
a.emit(cmp_imm(1, 5))
a.b_cond('eq', 'fw1_hsc_kcid')
a.ldr_lit(1, 'p4b_knobs_base')
a.emit(lsls_imm(2, 2, 1))
a.emit(strh_reg(7, 1, 2))

a.label('fw1_hsc_kcid')
a.emit(movs_reg(4, 5))
a.emit(subs_imm8(4, 6))
a.b('fw1_hsc_send')

a.label('fw1_hsc_fdr')
a.emit(movs_reg(7, 6))
a.emit(movs_imm(2, 0x7F))
a.emit(ands_reg(7, 2))
a.bl('ensure_otf_init')
a.emit(adds_imm8(0, ST_FADER_CC))
a.emit(movs_reg(2, 5))
a.emit(subs_imm8(2, 0x1A))
a.emit(ldrb_reg(1, 0, 2))
a.emit(cmp_reg(7, 1))
a.b_cond('eq', 'fw1_hsc_ret1')
a.emit(strb_reg(7, 0, 2))

a.emit(cmp_imm(2, 3))
a.b_cond('eq', 'fw1_hsc_fsync')
a.ldr_lit(1, 'p4b_arp_params')
a.emit(ldrh_imm(1, 1, 2))
a.emit(cmp_imm(1, 5))
a.b_cond('eq', 'fw1_hsc_fcid')
a.label('fw1_hsc_fsync')
a.ldr_lit(1, 'p4b_faders_base')
a.emit(lsls_imm(2, 2, 1))
a.emit(strh_reg(7, 1, 2))

a.label('fw1_hsc_fcid')
a.emit(movs_reg(4, 5))
a.emit(subs_imm8(4, 10))

a.label('fw1_hsc_send')
a.ldr_lit(0, 'p4b_work_mem')
a.emit(movs_imm(1, 1))
a.ldr_lit(3, 'p4b_get_mode')
a.emit(blx(3))
a.emit(uxth(1, 0))
a.emit(movs_reg(0, 4))
a.emit(movs_imm(2, 0))
a.ldr_lit(3, 'p4b_get_cc')
a.emit(blx(3))
a.emit(movs_imm(3, 0x7F))
a.emit(ands_reg(0, 3))
a.emit(movs_reg(4, 0))

a.emit(movs_reg(0, 5))
a.emit(movs_imm(1, 0))
a.ldr_lit(3, 'p4b_get_ch')
a.emit(blx(3))
a.emit(movs_imm(3, 0x0F))
a.emit(ands_reg(0, 3))
a.emit(movs_reg(6, 0))

a.emit(movs_reg(0, 6))
a.emit(movs_reg(1, 4))
a.emit(movs_reg(2, 7))
a.bl('otf_send_cc_3b')

a.emit(movs_reg(0, 5))
a.emit(movs_reg(1, 4))
a.emit(movs_reg(2, 6))
a.emit(movs_reg(3, 7))
a.bl('otf_show_cc_popup')

a.label('fw1_hsc_ret1')
a.emit(movs_imm(0, 1))
a.emit(pop([4, 5, 6, 7], pc=True))

# Literal Pool 4B
a.align4()
a.label('p4b_ram');            a.u32(OTF_RAM)
a.label('p4b_work_mem');       a.u32(0x20000EB8)
a.label('p4b_arp_params');     a.u32(0x2000122A)
a.label('p4b_knobs_base');     a.u32(0x2000129C)
a.label('p4b_faders_base');    a.u32(0x200012AE)
a.label('p4b_midi_send3');     a.u32(0x0800DCF5)
a.label('p4b_get_mode');       a.u32(0x0800CE15)
a.label('p4b_enc_accum');      a.u32(0x08024EC1)
a.label('p4b_get_cc');         a.u32(0x08025D2D)
a.label('p4b_get_ch');         a.u32(0x08026041)
a.label('p4b_tbl_cc');         a.u32('tbl_cc_names')
a.label('p4b_str_rc505');      a.u32('str_rc505_t')
a.label('p4b_str_knob_sp');    a.u32('str_knob_sp')
a.label('p4b_str_fader_sp');   a.u32('str_fader_sp')
a.label('p4b_str_cc_lp');      a.u32('str_cc_lp')
a.label('p4b_str_ch_lp');      a.u32('str_ch_lp')

# ==============================================================================
# Read-Only 2-Line OLED Strings & Lookup Tables
# ==============================================================================
def pad16(s):
    b = s.encode('ascii') + b'\x00'
    assert len(b) <= 16, f"String too long ({len(b)}): {s}"
    return b + b'\x00' * (16 - len(b))

def cstr(s):
    return s.encode('ascii') + b'\x00'

a.align4()
a.label('str_note_names');  a.raw_bytes(b'C C#D D#E F F#G G#A A#B ')
a.label('str_step_sp');     a.raw_bytes(cstr("Step "))
a.label('str_s_mode');      a.raw_bytes(cstr("Mode"))
a.label('str_s_mute');      a.raw_bytes(cstr("Mute"))
a.label('str_s_note');      a.raw_bytes(cstr("Note"))
a.label('str_steps_sfx');   a.raw_bytes(cstr(" Steps"))
a.label('str_rc505_t');     a.raw_bytes(cstr("RC505 T"))
a.label('str_knob_sp');     a.raw_bytes(cstr("Knob "))
a.label('str_fader_sp');    a.raw_bytes(cstr("Fader "))
a.label('str_cc_lp');       a.raw_bytes(cstr(" (CC"))
a.label('str_ch_lp');       a.raw_bytes(cstr("  (Ch "))

a.label('str_t_transport'); a.raw_bytes(cstr("Master Transport"))
a.label('str_t_root');      a.raw_bytes(cstr("Root Transpose"))
a.label('str_t_multinote'); a.raw_bytes(cstr("Multi-Step Note"))
a.label('str_t_scale');     a.raw_bytes(cstr("Scale Quantizer"))
a.label('str_t_dir');       a.raw_bytes(cstr("Play Direction"))
a.label('str_t_looplen');   a.raw_bytes(cstr("Active Loop Len"))
a.label('str_t_sync');      a.raw_bytes(cstr("Sequencer Sync"))

a.label('str_v_play');      a.raw_bytes(cstr("START (Play)"))
a.label('str_v_stop_clk');  a.raw_bytes(cstr("STOP (Clk ON)"))
a.label('str_v_stop_free'); a.raw_bytes(cstr("STOP (Free)"))
a.label('str_muted');       a.raw_bytes(cstr("MUTED"))
a.label('str_active');      a.raw_bytes(cstr("ACTIVE"))
a.label('str_full_chn');    a.raw_bytes(cstr("8 Stp (Full)"))
a.label('str_step1');       a.raw_bytes(cstr("-> Step 1"))

a.align4()
a.label('tbl_knob_modes')
a.raw_bytes(b''.join(pad16(s) for s in [
    "Skip (", "Sub-Oct (", "Normal (", "Oct+Acc (",
    "Ratch 2x (", "Ratch 3x (", "Ratch 4x (", "Random ("
]))

a.label('tbl_str_scales')
a.raw_bytes(b''.join(pad16(s) for s in [
    "Chromatic", "Major", "Natural Min", "Minor Pent",
    "Dorian", "Phryg Hicaz", "Harmonic Min", "Acid Blues"
]))

a.label('tbl_str_chains')
a.raw_bytes(b''.join(pad16(s) for s in [
    "1-8 Linear", "1-4 Loop A", "5-8 Loop B", "Chain AAAB",
    "Chain ABBA", "A-B-A-revB", "A-revA-B-rB", "Ping-Pong"
]))

def cc_entry(cc_num, name):
    b = name.encode('ascii') + b'\x00'
    assert len(b) <= 11, f"CC name too long ({len(b)}): {name}"
    return bytes([cc_num]) + b + b'\x00' * (11 - len(b))

a.align4()
a.label('tbl_cc_names')
a.raw_bytes(b''.join(cc_entry(c, n) for c, n in [
    (1,  "ModWheel"),
    (2,  "Breath"),
    (5,  "PortaTime"),
    (7,  "Volume"),
    (8,  "Balance"),
    (10, "Pan"),
    (11, "Express"),
    (64, "Sustain"),
    (65, "Porta Sw"),
    (70, "SoundVar"),
    (71, "Resonance"),
    (72, "Release"),
    (73, "Attack"),
    (74, "Cutoff"),
    (75, "Decay"),
    (76, "Vib Rate"),
    (77, "Vib Depth"),
    (78, "Vib Delay"),
    (79, "Flt Env"),
    (84, "PortaCtrl"),
    (91, "Reverb"),
    (93, "Chorus"),
    (94, "Delay"),
    (95, "Phaser"),
]) + b'\xFF\x00\x00\x00')

a.align4()
a.label('default_steps'); a.raw_bytes(default_steps_bytes)
a.label('scale_table');   a.raw_bytes(bytes(scale_table_bytes))
a.label('chain_table');   a.raw_bytes(chain_table_bytes)
a.align4()

patch_bytes, labels = a.build()
print(f"FW1 (OTF Live 8-Step) patch size: {len(patch_bytes)} bytes at 0x{PATCH_BASE:08x}..0x{PATCH_BASE+len(patch_bytes):08x}")

# ==============================================================================
# Pack & 100% Capstone Verify -> minilab-3_Firmware_Update_1.2.0_OTF_Live_8Step.mnl3
# ==============================================================================
HERE        = os.path.dirname(os.path.abspath(__file__))
backup_path = os.path.join(HERE, 'minilab-3_Firmware_Update_1.2.0_FACTORY_BACKUP.mnl3')
out_path    = os.path.join(HERE, 'minilab-3_Firmware_Update_1.2.0_OTF_Live_8Step.mnl3')

def encode_bl(src_addr, dst_addr):
    offset = dst_addr - (src_addr + 4)
    assert -16777216 <= offset <= 16777214 and (offset & 1) == 0
    S = (offset >> 24) & 1
    I1 = (offset >> 23) & 1
    I2 = (offset >> 22) & 1
    imm10 = (offset >> 12) & 0x3FF
    imm11 = (offset >> 1) & 0x7FF
    J1 = (~(I1 ^ S)) & 1
    J2 = (~(I2 ^ S)) & 1
    hw1 = 0xF000 | (S << 10) | imm10
    hw2 = 0xD000 | (J1 << 13) | (J2 << 11) | imm11
    return struct.pack('<HH', hw1, hw2)

def update_arturia_dfu_header(header_bytes, payload_bytes):
    hdr = bytearray(header_bytes)
    struct.pack_into('<I', hdr, 6, len(payload_bytes))
    hdr[0x0A] = (-sum(payload_bytes)) & 0xFF
    hdr[0x3F] = (-sum(hdr[:63])) & 0xFF
    return bytes(hdr)

with zipfile.ZipFile(backup_path, 'r') as zin:
    info_json = zin.read('info.json')
    fw1_raw = zin.read('MiniLab3_fw_1__fw1_2_0_1466__2024_12_16.bin')
    fw2_raw = zin.read('MiniLab3_fw_2__fw1_2_0_1037__2024_12_16.bin')

BASE = 0x08008800
fw1_hdr = fw1_raw[:64]
fw1_pay = bytearray(fw1_raw[64:])
orig_end_addr = BASE + len(fw1_pay)
fw1_pay.extend(b'\xFF' * (PATCH_BASE - orig_end_addr))
fw1_pay.extend(patch_bytes)
new_end_addr = BASE + len(fw1_pay)
print(f"FW1 new end addr: 0x{new_end_addr:08x} (< 0x0803A800, margin = {0x0803A800 - new_end_addr} bytes)")
assert new_end_addr < 0x0803A800
assert (len(fw1_pay) % 4) == 0

hooks = [
    (0x08027EAC, labels['otf_arp_event_dispatch'],   'otf_arp_event_dispatch'),
    (0x08027EC4, labels['otf_advance_step'],         'otf_advance_step'),
    (0x08027ECE, labels['otf_get_current_note'],     'otf_get_current_note'),
    (0x08027ED6, labels['otf_get_current_velocity'], 'otf_get_current_velocity'),
    (0x0802808A, labels['otf_arp_stop_hook'],        'otf_arp_stop_hook'),
    (0x08028B1C, labels['otf_note_player_ratchet'],  'otf_note_player_ratchet'),
    (0x0801179A, labels['otf_filter_midi_cc'],       'otf_filter_midi_cc'),
    (0x080130DE, labels['otf_on_pad_event'],         'otf_on_pad_event'),
    (0x0800E2EE, labels['otf_on_key_press'],         'otf_on_key_press'),
    (0x0800E720, labels['otf_on_key_release'],       'otf_on_key_release'),
    (0x0800EA42, labels['otf_set_led_rgb_hook'],     'otf_set_led_rgb_hook_refresh'),
    (0x08013264, labels['otf_set_led_rgb_hook'],     'otf_set_led_rgb_hook_shift'),
    (0x0802A4DE, labels['otf_master_clock_tick'],    'otf_master_clock_tick'),
    (0x080124CE, labels['otf_control_event_hook'],   'otf_control_event_hook'),
    (0x08012D38, labels['otf_combo_event_hook'],     'otf_combo_event_hook'),
]
for src_addr, dst_addr, name in hooks:
    off = src_addr - BASE
    fw1_pay[off:off+4] = encode_bl(src_addr, dst_addr)

pop_map_off = 0x08020370 - BASE
assert struct.unpack_from('<H', fw1_pay, pop_map_off)[0] == 0x202E
struct.pack_into('<H', fw1_pay, pop_map_off, 0xE000)

order_off = fw1_pay.find(b'\x05\x00Order\x00')
assert order_off != -1
fw1_pay[order_off:order_off+10] = b'\x05\x00OTF Seq\x00'

preset_replacements = [
    (b'User 1\x00', b'OTFSeq\x00'),
    (b'User 2\x00', b'SH-4d \x00'),
    (b'User 3\x00', b'RC-505\x00'),
    (b'User 4\x00', b'uKORG \x00'),
    (b'User 5\x00', b'K2000R\x00'),
]
for old_s, new_s in preset_replacements:
    idx = fw1_pay.find(old_s)
    if idx != -1:
        fw1_pay[idx:idx+len(new_s)] = new_s

new_fw1_hdr = update_arturia_dfu_header(fw1_hdr, fw1_pay)
new_fw1_bin = new_fw1_hdr + bytes(fw1_pay)
assert (sum(new_fw1_bin[:64]) & 0xFF) == 0
assert ((sum(new_fw1_bin[64:]) + new_fw1_bin[0x0A]) & 0xFF) == 0

md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
def verify_code_range(name, start_addr, end_addr):
    chunk = bytes(fw1_pay[start_addr-BASE:end_addr-BASE])
    insns = list(md.disasm(chunk, start_addr))
    decoded_len = sum(i.size for i in insns)
    assert decoded_len == len(chunk), f"Gap in {name}: {decoded_len}/{len(chunk)}"
    print(f"Verified {name:28s}: {len(insns):4d} insns ({decoded_len:4d} bytes, 0 errors).")

verify_code_range("ControlRouter Hook",         0x080124C8, 0x080124D6)
verify_code_range("ComboRouter Hook",           0x08012D34, 0x08012D40)
verify_code_range("Home Arp Popup Patch",       0x0802035C, 0x08020388)
verify_code_range("Island 1A (Init/Advance)",   PATCH_BASE, labels['p1_otf_ram'])
verify_code_range("Island 1B (Note/Vel/CC)",    labels['otf_get_current_note'], labels['p1b_otf_ram'])
verify_code_range("Island 2A (2-Line OLED)",    labels['otf_render_param_cb'], labels['po_ram'])
verify_code_range("Island 2B (RGB + Transport)",labels['otf_is_led_override_active'], labels['p2_otf_ram'])
verify_code_range("Island 2C (Pads & Keys)",    labels['otf_on_pad_event'], labels['p2c_otf_ram'])
verify_code_range("Island 3 (Master Clock)",    labels['otf_send_realtime_byte'], labels['p3_otf_ram'])
verify_code_range("Island 4 (BPM/Knobs/Faders)",labels['otf_control_event_hook'], labels['p4_otf_ram'])
verify_code_range("Island 4B (Synth CC/OLED)",  labels['otf_send_cc_3b'], labels['p4b_ram'])

fw2_hdr = fw2_raw[:64]
fw2_pay = bytearray(fw2_raw[64:])
idx_order_fw2 = fw2_pay.find(b'\x05\x00Order\x00')
if idx_order_fw2 != -1:
    fw2_pay[idx_order_fw2:idx_order_fw2+10] = b'\x05\x00OTF Seq\x00'
for old_s, new_s in preset_replacements:
    idx = fw2_pay.find(old_s)
    if idx != -1:
        fw2_pay[idx:idx+len(new_s)] = new_s
new_fw2_bin = update_arturia_dfu_header(fw2_hdr, fw2_pay) + bytes(fw2_pay)
assert (sum(new_fw2_bin[:64]) & 0xFF) == 0
assert ((sum(new_fw2_bin[64:]) + new_fw2_bin[0x0A]) & 0xFF) == 0

with zipfile.ZipFile(out_path, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
    zout.writestr('info.json', info_json)
    zout.writestr('MiniLab3_fw_1__fw1_2_0_1466__2024_12_16.bin', new_fw1_bin)
    zout.writestr('MiniLab3_fw_2__fw1_2_0_1037__2024_12_16.bin', new_fw2_bin)

print(f"\nSUCCESS -> {out_path} ({os.path.getsize(out_path)} bytes)")
