# Arturia MiniLab 3 (`OTF 64s`) — Tuş Kombinasyonları Hızlı Özeti (Cheat Sheet)

**Firmware:** [minilab-3_Firmware_Update_1.2.0_OTF_Pro_64Step.mnl3](file:///c:/Users/orkun/.gemini/antigravity/scratch/dawless_project/minilab3_otf/minilab-3_Firmware_Update_1.2.0_OTF_Pro_64Step.mnl3)  
**Aktif Kurulum:** `MiniLab 3` → `Roland SH-4d (Ch 1–5)` → `Donner B1 (Ch 6)` → `Boss RC-505mkII (Ch 14/16)` → `Donner D1 (Ch 10)`

---

## 1. Doğrudan Kontroller (Hiçbir Tuşa Basılı Tutmadan)

| Fiziksel Kontrol | Ne Kontrol Eder? | OLED Göstergesi (`Üst` / **`Alt`**) |
| :--- | :--- | :--- |
| **Siyah Ana Knob Çevir** | **Canlı Master BPM (`30 – 270 BPM`)** *(Tüm presetlerde aktif)* | Grafik `Rate` / **`120 BPM`** |
| **Siyah Ana Knob Tek Tık** | **Step 1 Reset** — Sayacı ve aktif Pattern Chain'i anında `1. Adım`'a hizalar | `Sequencer Sync` / **`-> Step 1`** |
| **`Pad 6`** *(Bank B & normal presetler)* | **Master START (`0xFA`) + `24 PPQN` Clock (`0xF8`)** başlatır | `Master Transport` / **`START (Play)`** |
| **`Pad 5`** *(Bank B & normal presetler)* | **Master STOP (`0xFC`)** — 1. basış saati açık tutar, 2. basış saati keser | 1: **`STOP (Clk ON)`** \| 2: **`STOP (Free)`** |
| **Klavyeden Tek Tuş** | **Root Transpose** — Tüm pattern'in kök notasını değiştirir | `Root Transpose` / **`F3  (53)`** |
| **Klavye 1. Tuş Basılı + 2.–8. Tuş** | Aktif sayfadaki `Adım 2..8`'e sırayla nota + velocity yazar | `Step X Note` / **`D#4  v108`** |
| **`Pad 1–8` Basılı Tut + Klavye Tuşu** | **Step Lock** — Seçili tek veya çoklu adıma nota + velocity kilitler | `Step X Note` / `Multi-Step Note` |
| **`Pad 1–8` Tek Tık** *(Bank A)* | **Step Mute / Unmute** — İlgili adımı susturur veya açar | `Step X Mute` / **`MUTED`** · **`ACTIVE`** |
| **`Knob 1–8`** | **Adım İfade Modu:** `0–15` Skip · `16–31` Sub-Oct · `32–68` Normal · `69–80` Oct+Acc · `81–92` Ratch 2x · `93–104` Ratch 3x · `105–115` Ratch 4x · `116–127` Random | `Step X Mode` / **`Ratch 3x (96)`** |
| **`Fader 1`** | **Scale Quantizer** — `Chromatic`, `Major`, `Natural Min`, `Minor Pent`, `Dorian`, `Phryg Hicaz`, `Harmonic Min`, `Acid Blues` | `Scale Quantizer` / **`Phryg Hicaz`** |
| **`Fader 2`** | **Play Direction** — `Forward`, `Page Loop`, `Ping-Pong`, `Reverse`, `Chain AAAB`, `Chain ABBA`, `A-B-A-revB`, `A-revA-B-rB` | `Play Direction` / **`Ping-Pong`** |
| **`Fader 3`** | **Active Loop Len** — Orta bölgede `2..N` poliritmik adım kırpma; en alt/üstte tam pattern uzunluğu | `Active Loop Len` / **`5 Steps`** |
| **`Fader 4`** | **Doğrudan Synth MIDI CC** — `Shift` gerektirmeden hedef cihaza canlı CC gönderir | `<Param> (CC#)` / **`84  (Ch 1)`** |

---

## 2. `Siyah Ana Knob` Basılı Tut + ... (Hafıza, Pattern Chain & Transpose)

| Kombinasyon | Ne Kontrol Eder? | OLED Göstergesi (`Üst` / **`Alt`**) |
| :--- | :--- | :--- |
| **Sadece Basılı Tut** | Pad 1–8'de **Canlı 8-Slot & Zincir LED Haritası** gösterir *(Yeşil: Çalan slot, Altın: Zincirdeki slot, Mor: Boşta)* | — |
| **Basılı Tut + Sağa/Sola Çevir** | **Global Transpose** — 64 adımın tamamını `-12 .. +12` yarım ses kaydırır | `Global Transpose` / **`+5 Semitones`** |
| **Basılı Tut + Tek `Pad 1–8`** | **Load Pattern** — `Slot 1–8` yükler *(varsa aktif zinciri kapatıp tek slota döner)* | `Load Pattern` / **`Slot 1` .. `Slot 8`** |
| **Basılı Tut + Sırayla Çoklu `Pad 1–8`** | **Pattern Chain** — `16` halkaya kadar patternleri arka arkaya otomatik çaldırır *(aynı slota üst üste basılabilir)* | `Pattern Chain` / **`1>2>3>4 (4)`** |
| **`Hold` + Siyah Knob + `Pad 1–8`** | **Save to Flash** — Mevcut 64-step pattern'i kalıcı Flash belleğe (`Slot 1–8`) kaydeder | `Save to Flash` / **`Slot X Saved`** |

---

## 3. `Hold` Basılı Tut + ... (64-Adım Sayfalar, Uzunluk, 303 Slide & Groove)

| Kombinasyon | Ne Kontrol Eder? | OLED Göstergesi (`Üst` / **`Alt`**) |
| :--- | :--- | :--- |
| **Sadece `Hold` Basılı Tut** | Pad 1–8'de **Canlı 8-Sayfa Haritası (`P1–P8`)** gösterir *(Altın: Seçili, Yeşil: Çalan, Camgöbeği: Uzunluk içi aktif sayfa)* | — |
| **`Hold` + `Pad 1–8`** | Düzenlenecek 8 adımlık sayfayı seçer (`Adım 1–8` .. `Adım 57–64`) | `Pattern Page` / **`P1 (1-8)` .. `P8 (57-64)`** |
| **`Hold` + `Oct +`** | **Fold-Duplicate** — Mevcut pattern'i tüm verileriyle ikiye katlayıp yeni yarıya kopyalar (`8 -> 16 -> 32 -> 64`) | `Pattern Length` / **`Fold -> 16 / 32 / 64`** |
| **`Hold` + `Oct -`** | **Halve Length** — Pattern uzunluğunu yarıya indirir (`64 -> 32 -> 16 -> 8`) | `Pattern Length` / **`Len -> 32 / 16 / 8`** |
| **`Hold` + Siyah Knob Tek Tık** | **Auto Page-Follow** — Çalarken Pad ekranının aktif sayfayı otomatik takip etmesini açar/kapatır | `Auto PageFollow` / **`ON` · `OFF`** |
| **`Hold` + `Knob 1–8`** | `0–99`: **Tetiklenme Olasılığı (`%10–%99`)** · `100–107`: **`%100`** · `108–127`: **Gerçek TB-303 Legato Slide (`ON`)** | `Step X Prob/303` / **`303 Slide ON`** |
| **`Hold` + `Fader 1`** | **Gate Length** *(Nota basılı kalma süresi / Tie)* | Grafik `Gate` ekranı |
| **`Hold` + `Fader 2`** | **Swing** *(`%50 – %75` groove sallanması)* | Grafik `Swing` ekranı |
| **`Hold` + `Fader 3`** | **Time Division** *(`1/4`, `1/8`, `1/16`, `1/32` hız bölümü)* | Grafik `Time Div` ekranı |
| **`Hold` + `Fader 4`** *(Tepeye `>=105` it)* | **Dice Mutator** — Seçili sayfadaki 8 adıma (1. adımı kök notada koruyarak) yeni melodi üretir | `Dice Mutator` / **`Page X Rolled`** |

---

## 4. `Oct +` / `Oct -` Kombinasyonları (Adım Perdesi & Anında Sıfırlama)

| Kombinasyon | Ne Kontrol Eder? | OLED Göstergesi (`Üst` / **`Alt`**) |
| :--- | :--- | :--- |
| **`Oct +` veya `Oct -` + `Pad 1–8`** | İlgili adımın oktavını kaydırır (`-2 .. +2` oktav) | `Step X Octave` / **`+1 Oct (C5)`** |
| **`Oct +` veya `Oct -` + `Knob 1–8`** | Klavyeye dokunmadan adıma yarım ses perde yazar (`-24 .. +24` yarım ses) | `Step X Pitch` / **`+7st (G4)`** |
| **`Oct -` + `Oct +` (Aynı Anda Bas)** | **Instant Reload** — Üzerinde doğaçlama yapılan pattern'i ve transpose'u anında kayıtlı temiz haline döndürür | `Reload Pattern` / **`Slot X Reset`** |

---

## 5. `Shift` Basılı Tut + ... (Canlı Synth MIDI CC, Mod & Sistem)

| Kombinasyon | Ne Kontrol Eder? | OLED Göstergesi (`Üst` / **`Alt`**) |
| :--- | :--- | :--- |
| **`Shift` + `Knob 1–8` / `Fader 1–4`** | Sequencer çalarken hedef synth'e **`0–127` MIDI CC** gönderir *(Ch 14 CC1–5'te otomatik `RC505 T1..T5` yazar)* | `Cutoff (CC74)` / **`72  (Ch 1)`** |
| **`Shift` + `Pad 6` / `Pad 5`** | `Pad Bank A` içindeyken de Master **START** (`Pad 6`) ve **STOP** (`Pad 5`) gönderir | `Master Transport` / **`START` · `STOP`** |
| **`Shift` + `Pad 1` (Tek Tık)** | `OTF 64s` Sequencer'ı anında **Açar / Kapatır** *(normal polifonik klavyeye döner)* | `Arp ON` / `Arp OFF` |
| **`Shift` + `Pad 1` (Basılı) + `Knob 1`** | Arpeggiator menüsünden **`OTF 64s`** modunu seçer | `Mode` / **`OTF 64s`** |
| **`Shift` + `Pad 2` (Basılı) + Siyah Knob** | Donanım presetini değiştirir (`OTF64s`, `SH-4d`, `RC-505`, `uKORG`, `K2000R`) | Preset seçim ekranı |
| **`Shift` + `Pad 3`** | **`Pad Bank A`** *(8 Adım Kontrolü)* ↔ **`Pad Bank B`** *(Shift'siz Stop/Start & Pad)* geçişi yapar | `Pad Bank A` / `Pad Bank B` |
| **`Shift` + Klavye Tuşu (`1–16`)** | Aktif MIDI kanalını seçer (`Ch 1–5` SH-4d, `Ch 6` B1, `Ch 10` D1, `Ch 14` RC-505mkII) | `MIDI Ch 1..16` |

---

## 6. `Pad Bank B` — Dawless Riser & Drop Performans Deck (`Shift + Pad 3`)

| Kontrol (`Pad Bank B`) | Ne Kontrol Eder? | OLED Göstergesi (`Üst` / **`Alt`**) |
| :--- | :--- | :--- |
| **`Pad 1` (Basılı Tut)** | **Accelerating Drum Roll** — `D1` Ch 10 `SD (38)` + `HC (39)` (`1/8 -> 1/16 -> 1/32 -> 1/64`) | `Drum Roll (D1)` / **`1/8 -> 1/64`** |
| **`Pad 2` (Tek Tık)** / `Hold + Pad 2` | **4-Bar / 8-Bar Auto-Riser** — `SH-4d` Ch 1–4 `CC74/91` + `RC-505` Ch 14 `CC80/81` + Son Bar Roll + **Beat 1.1 Auto-Drop** | `Auto-Riser 4B` / **`DROP IN: 4.4..1.1`** |
| **`Pad 3` (Basılı Tut)** / `Hold + Pad 3` | **Synth Pitch Rise** (`0 -> +8160` PB + `CC1`) \| `Hold`: **Tape-Stop Dive** (`0 -> -8172` PB) | `Synth Riser` / **`Pitch Rise UP`** |
| **`Pad 4` (Basılı Tut)** | **Pre-Drop Vacuum Gate** — Geçici tam sessizlik (`OTF 64s` Rest + `CC123` kesme) | `Pre-Drop Gate` / **`VACUUM MUTE`** |
| **`Pad 5` / `Pad 6`** | **Master STOP** (`Pad 5`) / **Master START** (`Pad 6`) | `Master Transport` |
| **`Pad 7` (Tık)** / `Hold + Pad 7` | **`Donner D1` Uplifter / FX** (`Ch 10`: `SMP1 = Note 60` \| `Hold`: `SMP3 = Note 64`) | `D1 FX Trigger` / **`SMP1 Uplifter`** |
| **`Pad 8` (Tek Tık)** | **THE DROP!** — Tüm `SH-4d` & `RC-505` CC'lerini **orijinal değerlerine** döndürür + `Step 1` + `D1` Crash (`49`) & Impact (`62`) | `Riser & Drop` / **`>>> DROP! <<<`** |
| **`Modulation Şeridi`** | **Manual Macro Riser (`%0–%100`)** — Parmağınla `SH-4d` + `RC-505` gerilimini canlı sür | `Manual Riser` / **`Tension: 78%`** |

---

## 7. Pad RGB Renk Anahtarı (`Pad Bank A` — Adım Görünümü)

- **Zümrüt Yeşili:** Çalan adım (`Playhead`) | **Parlak Kırmızı/Gül:** Playhead susturulmuş/atlanan adımda | **Altın Sarısı:** Basılı tutulan Pad (`Step Lock`)
- **Turkuaz:** Normal | **Asit Yeşili:** `303 Slide ON` | **Derin Mavi:** `-1 Oct` (`Sub-Oct`) | **Kehribar/Turuncu:** `+1 Oct + Accent`
- **Mor / Macenta / Pembe:** `Ratchet 2x / 3x / 4x` | **Buz Beyazı:** `Random` | **Loş Kırmızı:** `Mute` | **Sönük:** `Skip`
