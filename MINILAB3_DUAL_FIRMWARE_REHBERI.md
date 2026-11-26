# Arturia MiniLab 3 — Çift Özel Firmware Kullanım Kılavuzu (`Live 8-Step` & `Pro 64-Step`)

Stüdyo kurulumundaki aktif 5'li zincir (**MiniLab 3 $\rightarrow$ Roland SH-4d $\rightarrow$ Donner B1 $\rightarrow$ Boss RC-505mkII $\rightarrow$ Donner D1**) için iki ayrı bağımsız `.mnl3` firmware paketi **2-Satırlı OLED Parametre Ekranı (İsim + Değer)** ve **Shift'siz Doğrudan `Pad 5 = Stop` / `Pad 6 = Start`** özellikleriyle güncellenmiş ve %100 ARM Thumb disassembly + DFU checksum doğrulamasından geçirilmiştir:

1. **Firmware 1 — `OTF Live 8-Step`:** [minilab-3_Firmware_Update_1.2.0_OTF_Live_8Step.mnl3](file:///c:/Users/orkun/.gemini/antigravity/scratch/dawless_project/minilab3_otf/minilab-3_Firmware_Update_1.2.0_OTF_Live_8Step.mnl3) *(OLED Mod Adı: **`OTF Seq`**)*
2. **Firmware 2 — `OTF Pro 64-Step Groovebox`:** [minilab-3_Firmware_Update_1.2.0_OTF_Pro_64Step.mnl3](file:///c:/Users/orkun/.gemini/antigravity/scratch/dawless_project/minilab3_otf/minilab-3_Firmware_Update_1.2.0_OTF_Pro_64Step.mnl3) *(OLED Mod Adı: **`OTF 64s`** — MCC önbelleğine hazır yüklendi)*
3. **Orijinal Fabrika Yedeği:** [minilab-3_Firmware_Update_1.2.0_FACTORY_BACKUP.mnl3](file:///c:/Users/orkun/.gemini/antigravity/scratch/dawless_project/minilab3_otf/minilab-3_Firmware_Update_1.2.0_FACTORY_BACKUP.mnl3)

> [!TIP]
> **Hangi Firmware Yüklü Olduğunu Anlama:** `Shift + Pad 1 (Arp)` menüsünde `Mode` parametresine baktığında **FW1** yüklüyse **`OTF Seq`**, **FW2** yüklüyse **`OTF 64s`** yazar. Ayrıca User 1 preset adı FW1'de `OTFSeq`, FW2'de `OTF64s` olarak görünür.

---

## 1. İki Firmware'de Ortak Olan Ana Sahne Özellikleri

### A. Shift'siz Doğrudan `Pad 5 = STOP` & `Pad 6 = START` (+ Canlı Transport LED'leri)

Artık `Shift` tuşuna basılı tutmana gerek kalmadan **tek parmakla** tüm MIDI zincirini (`SH-4d`, `Donner B1`, `RC-505mkII`, `Donner D1`) başlatıp durdurabilirsin:

| Aktif Preset / Pad Bankası | `Pad 5` Davranışı & LED Rengi | `Pad 6` Davranışı & LED Rengi | Diğer Pad'ler (`1–4` ve `7–8`) |
| :--- | :--- | :--- | :--- |
| **Normal Preset'ler** (`SH-4d`, `RC-505`, `uKORG`, `K2000R`, `Arturia`) — **Bank A & Bank B** | **Doğrudan STOP (`0xFC`)**<br>*(Sabit Kırmızı LED)* | **Doğrudan START (`0xFA` + `24 PPQN` Clock)**<br>*(Beklemede Yeşil / Çalarken Parlak Zümrüt Yeşili LED)* | Normal MIDI Nota / CC / Program Change gönderir *(Pad 5 ve 6 yanlışlıkla nota tetiklemez)* |
| **`OTF` Sequencer Modu** — **`Pad Bank B`** *(`Shift + Pad 3` ile Bank B seçiliyken)* | **Doğrudan STOP (`0xFC`)**<br>*(Sabit Kırmızı LED)* | **Doğrudan START (`0xFA` + `24 PPQN` Clock)**<br>*(Yeşil / Parlak Zümrüt Yeşili LED)* | Bank B normal kontrolleri |
| **`OTF` Sequencer Modu** — **`Pad Bank A`** | **Step 5** *(Mute / Nota Kilitleme / Sayfa 5)* | **Step 6** *(Mute / Nota Kilitleme / Sayfa 6)* | **Step 1–8** tam OTF Sequencer kontrolü *(İstersen `Shift + Pad 5 / 6` burada da çalışır)* |

> [!NOTE]
> **Çift Kademeli Akıllı STOP (`Pad 5`):** Çalarken **1. basışta** `0xFC (Stop)` gönderir ancak `24 PPQN` saat sinyalini (`0xF8`) arka planda sıcak tutar (`STOP (Clk ON)`). Durmuş haldeyken **2. basışta** `0xF8` saat sinyalini tamamen keserek (`STOP (Free)`) SH-4d ve RC-505mkII'nin `AUTO` modda kendi iç saatlerine dönmesine izin verir.

### B. Siyah Ana Knob = Canlı Master BPM & Step 1 Hizalama

| Fiziksel Kontrol | İşlevi | OLED Ekran (`Üst Başlık` / **`Alt Değer`**) |
| :--- | :--- | :--- |
| **Siyah Ana Knob Çevirme** *(Tek el, tüm presetlerde)* | **Canlı Master BPM (`30 – 270 BPM`)** | Orijinal Arturia grafik barlı `Rate` / **`120 BPM`** ekranı *(5-pin MIDI `0xF8` hızını ve dahili sequencer'ı anında günceller)* |
| **Siyah Ana Knob Tek Tık** *(OTF modunda)* | **Anında 1. Adıma Sıfırla (`Step 1 Reset`)** | `Sequencer Sync` / **`-> Step 1`** |
| **`Shift` + Siyah Ana Knob** *(Çevir / Tıkla)* | **Orijinal Fabrika İşlevi** | Preset seçimi ve Arp menü gezintisi %100 orijinal haliyle korunmuştur |

### C. 2-Satırlı OLED Parametre Ekranı (`Parametre İsmi` + `Değer`)

Her iki firmware'de de Arturia'nın yerleşik OLED grafik motoru kullanılarak dokunduğun **her kontrolde** üstte ters renkli başlık şeridinde **Parametre İsmi**, altta büyük kalın fontla **Anlık Değer** (ve nota/pitch işlemlerinde o adımın gerçek duyulan notası) gösterilir:

| Kontrol / İşlem | Üst Şerit (Parametre İsmi) | Alt Satır (Büyük Değer Örneği) |
| :--- | :--- | :--- |
| **`Pad 6` / `Pad 5` (Start / Stop)** | `Master Transport` | **`START (Play)`** / **`STOP (Clk ON)`** / **`STOP (Free)`** |
| **`Knob 1–8` (Adım İfadesi)** | `Step 1 Mode` .. `Step 64 Mode` | **`Skip (0)`**, **`Sub-Oct (24)`**, **`Normal (64)`**, **`Oct+Acc (75)`**, **`Ratch 3x (98)`**, **`Random (122)`** |
| **`Pad 1–8` Tek Tık (Mute / Unmute)** | `Step 1 Mute` .. `Step 64 Mute` | **`MUTED`** / **`ACTIVE`** |
| **`Pad 1–8` + Klavye Tuşu (Nota Kilidi)** | `Step 5 Note` *(Çoklu pad ise: `Multi-Step Note`)* | **`D#3  v112`** *(Nota adı + Velocity)* |
| **Klavyeden Tek Tuş (Root Transpose)** | `Root Transpose` | **`C4  (60)`** |
| **`Fader 1` (Gam / Makam)** | `Scale Quantizer` | **`Chromatic`**, **`Natural Min`**, **`Phryg Hicaz`**, **`Acid Blues`** vb. |
| **`Fader 2` (Yön / Bar Zinciri)** | `Play Direction` | **`Forward`**, **`Page Loop`**, **`Ping-Pong`**, **`Chain AAAB`** vb. |
| **`Fader 3` (Döngü Uzunluğu)** | `Active Loop Len` | **`16 Steps`** *(veya tam uzunlukta: **`Full (16)`** / **`8 Stp (Full)`**)* |
| **`Shift` + `Knob 1–8` / `Fader 1–4`** *(veya Normal Presetlerde doğrudan Knob/Fader)* | **Akıllı Parametre Adı + `(CC#)`**<br>Örn: `Cutoff (CC74)`, `Resonance (CC71)`, `RC505 T1 (CC1)`, `Knob 1 (CC21)`, `Fader 4 (CC17)` | **`68  (Ch 1)`** *(MCC'de Relative kalsa bile her zaman gerçek `0–127` Absolute CC gönderir ve değeri + MIDI kanalını gösterir!)* |

---

## 2. Firmware 1 (`OTF Live 8-Step`) — Hızlı Canlı Performans Özeti

Sıfır sayfa ve sıfır menü mantığıyla **8 fiziksel Knob = 8 fiziksel Adım** doğrudan bağlıdır:
- **Nota Girişi:** Tek tuş = `Root Transpose` | Çoklu tuş basılı tutarak sırayla basma = `Step 1–8 Note` yazma | **`Pad 1–8` basılı tut + Tuş** = O adıma nota ve velocity kilitleme.
- **`Pad 1–8` (`Pad Bank A`):** Tek dokunuşla Adım Mute / Unmute (`MUTED` / `ACTIVE`). **`Pad Bank B`**'ye geçtiğinde ise `Pad 5 = STOP` ve `Pad 6 = START` doğrudan elinin altındadır.
- **`Knob 1–8` (`Step 1..8 Mode`):** `0–15` Skip | `16–31` Sub-Octave (`-12`) | `32–68` Normal | `69–80` Octave Up + Accent (`+12`, Vel 127) | `81–92` Ratchet 2x | `93–104` Ratchet 3x | `105–115` Ratchet 4x | `116–127` Randomize.
- **`Fader 1–4`:** **F1** = `Scale Quantizer` (8 Makam/Gam) | **F2** = `Play Direction` (8 Stylophone Bar Zinciri) | **F3** = `Active Loop Len` (`8..2 Steps`) | **F4** = Serbest Canlı MIDI CC *(veya `Shift` basılı tutarak 8 Knob + 4 Fader'ın tamamıyla canlı MIDI CC!)*.

---

## 3. Firmware 2 (`OTF Pro 64-Step Groovebox`) — Tam Kontrol & OLED Matrisi

FW2, MiniLab 3'ün kullanılmayan dahili Flash alanında (`0x0803A800`, 4 KB) **cihaz kapansa bile silinmeyen 8 adet 64-step pattern hafızası**, **Sayfa Katlama (`Fold-Duplicate`)**, **Gerçek TB-303 Legato Slide / Tie** ve **2-Satırlı OLED Geri Bildirimi** sunar.

### A. 64 Adım Sayfa Yönetimi & Katlayarak Büyütme (`8 -> 16 -> 32 -> 64`)

| Kombinasyon | İşlev | OLED Üst Başlık | OLED Alt Değer |
| :--- | :--- | :--- | :--- |
| **`Hold` Basılı Tutma** | **Canlı 8-Sayfa RGB Haritası** *(Altın=Seçili, Yeşil=Çalan, Beyaz-Altın=İkisi birden, Camgöbeği=Aktif)* | — | *(Pad 1–8 üzerinde canlı gösterilir)* |
| **`Hold` + `Pad 1–8`** | **Sayfa 1–8 Seçimi (`1–8` .. `57–64`)** | `Active Edit Page` | **`Page 1 (1-8)`** .. **`Page 8 (57-64)`** |
| **`Hold` + `Oct +`** | **Fold-Duplicate (`8 -> 16 -> 32 -> 64`)** — Mevcut adımları tüm slide/knob verileriyle ikiye katlayıp kopyalar ve yeni yarıya geçer | `Fold-Duplicate` | **`-> 16 Steps`** / **`-> 32 Steps`** / **`-> 64 Steps`** |
| **`Hold` + `Oct -`** | **Uzunluğu Yarıya İndir (`64 -> 32 -> 16 -> 8`)** | `Pattern Length` | **`32 Steps`** / **`16 Steps`** / **`8 Steps`** |
| **`Hold` + Siyah Knob Tık** | **Auto Page-Follow (`ON / OFF`)** | `Auto Page Follow` | **`ON (Follow)`** / **`OFF (Locked)`** |

### B. Kalıcı Pattern Hafızası (8 Slot — Elektrik Kesilse Bile Silinmez)

Açılışta boş slotlar **4 hazır başlangıç groove'u** (*Slot 1: Classic 8-Step*, *Slot 2: 16-Step Donner B1 Acid Slide*, *Slot 3: 16-Step SH-4d Techno*, *Slot 4: 32-Step Arpeggio*) ile dolu gelir:

| Kombinasyon | İşlev | OLED Üst Başlık | OLED Alt Değer |
| :--- | :--- | :--- | :--- |
| **Siyah Knob Basılı Tut + `Pad 1–8`** | **Pattern Yükle (`Slot 1–8`)** | `Load Pattern` | **`Slot 1 Loaded`** .. **`Slot 8 Loaded`** |
| **`Hold` + Siyah Knob Basılı Tut + `Pad 1–8`** | **Kalıcı Flash'a Kaydet (`Slot 1–8`)** | `Save Pattern` | **`Slot 1 SAVED!`** .. **`Slot 8 SAVED!`** |
| **`Oct -` + `Oct +` (İkisine Birden Bas)** | **Anında Kayıtlı Haline Geri Dön (`Reload`)** | `Pattern Memory` | **`Slot Reloaded!`** |

### C. Gelişmiş Katmanlar (`Hold`, `Oct +/-`, `Siyah Knob`, `Shift`)

| Katman / Modifier | Kontrol | İşlev | OLED (`Üst Başlık` / **`Alt Değer`**) |
| :--- | :--- | :--- | :--- |
| **`Hold` Basılı Tutarken** | **`Knob 1–8`** | **Adım Olasılığı (`10%–99%`) & Gerçek 303 Slide/Tie (`>=108`)** *(Donner B1 ve SH-4d mono seslerde gerçek üst üste binen Legato Slide üretir; LED Asit Yeşili yanar)* | `Step X Prob/303` / **`Prob 75%`**, **`100% (Normal)`**, **`303 SLIDE ON`** |
| **`Hold` Basılı Tutarken** | **`Fader 1–3`** | **F1:** Gate Length \| **F2:** Swing `%50–%75` \| **F3:** Time Division (`1/4`..`1/32T`) | Orijinal Arturia Grafik `Gate` / `Swing` / `Time Div` Ekranları |
| **`Hold` Basılı Tutarken** | **`Fader 4` (En Üste İt)** | **Müzikal Sayfa Mutasyonu** *(Seçili sayfadaki 8 adımı gam içinde yeniler)* | `Page Generator` / **`Page Mutated!`** |
| **`Oct +` veya `Oct -` Basılı** | **`Knob 1–8`** | **Adım Başına Yarım Ses Pitch (`-24..+24`)** *(Klavyesiz melodi yazımı)* | `Step X Pitch` / **`+7st (G4)`**, **`-5st (G3)`** *(Gerçek duyulan notayla birlikte!)* |
| **`Oct +` veya `Oct -` Basılı** | **`Pad 1–8`** | **Adım Oktav Kaydırma (`-2..+2` Oktav)** | `Step X Octave` / **`+1 Oct (C5)`**, **`-1 Oct (C3)`** |
| **Siyah Knob Basılı Tutarken** | **Siyah Knob Çevir** | **Global Semitone Transpose (`-12..+12`)** *(64 adımın tamamını canlı transpoze eder)* | `Global Transpose` / **`+5 st`**, **`0 st`**, **`-3 st`** |
| **`Shift` Basılı Tutarken** | **`Knob 1–8` & `Fader 1–4`** | **Akıllı Canlı Synth MIDI CC (`0–127` Absolute)** *(Sequencer çalmaya devam ederken 8 Knob + 4 Fader doğrudan SH-4d / B1 / RC-505 filtre ve efektlerini kontrol eder; MCC'de Relative kalsa bile `"Knob.."` yazmaz!)* | `Cutoff (CC74)` / **`68  (Ch 1)`** *(veya `Knob 1 (CC21)` / **`68  (Ch 1)`**)* |

---

## 4. RGB Pad Renk Rehberi (`FW1` & `FW2`)

| Pad Rengi | Anlamı |
| :--- | :--- |
| **Sabit Kırmızı (`Pad 5`) / Yeşil (`Pad 6`)** | **Shift'siz Doğrudan STOP (`Pad 5`) ve START (`Pad 6`)** *(Normal presetlerde ve OTF modunda `Pad Bank B` seçiliyken aktif; çalarken `Pad 6` parlak zümrüt yeşili yanar)* |
| **Zümrüt Yeşili (Parlak)** | OTF modunda şu an çalan aktif adım (`Playhead`) |
| **Parlak Gül / Kırmızı** | Playhead şu an Mute edilmiş veya Skip olan bir adımın üzerinden geçiyor |
| **Altın Sarısı (Parlak)** | Basılı tutulan Pad (nota kilitlemeye hazır) veya `Hold` haritasında seçili sayfa |
| **Turkuaz / Camgöbeği** | Normal aktif adım (`Knob = 32–68`) |
| **Asit Limonu Yeşili (`FW2`)** | **Gerçek 303 Slide / Tie** açık olan adım (`Hold + Knob >= 108`) |
| **Derin Mavi** | Sub-Octave (`-1` oktav) adımı |
| **Kehribar / Turuncu** | Octave Up (`+1` oktav) + Accent (`Vel 127`) adımı |
| **Mor / Macenta / Pembe** | Ratchet `2x` (Mor) / `3x` (Macenta) / `4x` (Sıcak Pembe) |
| **Buz Beyazı / Nane** | Canlı Random (Rastgele gam içi nota) adımı |
| **Loş Kırmızı / Sönük** | Loş Kırmızı = Mute edilmiş adım \| Sönük = Skip (`Knob = 0–15`, döngüde atlanır) |

---

## 5. MIDI Control Center (MCC) ile Yükleme & Firmware Değiştirme

1. **Doğrudan MCC Üzerinden Seçerek Yükleme (En Pratik Yöntem):**
   - Cubase veya MIDI portunu kullanan diğer uygulamaların kapalı olduğundan emin ol.
   - **MIDI Control Center**'ı aç $\rightarrow$ **Firmware Revision: `1.2.0`** butonuna tıkla $\rightarrow$ **Upgrade**'e bas ve `minilab3_otf` klasöründen istediğin `.mnl3` dosyasını seç (`OTF_Pro_64Step.mnl3` zaten MCC önbelleğine de hazır kopyalandı).
   - Güncelleme bittiğinde Windows USB MIDI sürücüsü yenilenirken *"Failed to open the device"* uyarısı çıkarsa **OK** deyip USB kablosunu **1 kez çıkarıp takman** yeterlidir.
2. **Komut Satırı Seçici Script ([switch_mcc_firmware.py](file:///c:/Users/orkun/.gemini/antigravity/scratch/dawless_project/minilab3_otf/switch_mcc_firmware.py)):**
   ```powershell
   python switch_mcc_firmware.py pro64     # MCC önbelleğine FW2 (64-Step Groovebox) kopyalar
   python switch_mcc_firmware.py live8     # MCC önbelleğine FW1 (Live 8-Step) kopyalar
   python switch_mcc_firmware.py factory   # Orijinal Arturia 1.2.0 fabrika yazılımını kopyalar
   python switch_mcc_firmware.py status    # Şu an hangisinin seçili olduğunu gösterir
   ```
