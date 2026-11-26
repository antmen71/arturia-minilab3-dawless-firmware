# Arturia MiniLab 3 — `OTF 64s` (Pro 64-Step Groovebox) Kullanım Kılavuzu

**Firmware Dosyası:** `minilab-3_Firmware_Update_1.2.0_OTF_Pro_64Step.mnl3`  
**Aktif Zincir:** `MiniLab 3 (5-Pin MIDI Out)` → `Roland SH-4d` → `Donner B1` → `Boss RC-505mkII` → `Donner D1`

---

## 1. `OTF 64s` Modunu Açma, Kapatma & Hedef Cihaz Seçimi

1. **Preset Seçimi:** `Shift + Pad 2` basılı tutarken **Siyah Ana Knob** ile **`OTF64s`** (`User 1`) presetini seç *(veya herhangi bir User presette de açabilirsin)*.
2. **Sequencer Modunu Seçme:** `Shift + Pad 1 (Arp)` basılı tutarken **`Knob 1 (Mode)`** ile **`OTF 64s`** moduna getir.
   - `OTF 64s` seçildiği anda Arpeggiator/Sequencer otomatik olarak aktifleşir (`Arp ON`).
   - Klavyeden bir tuşa bastığında (veya `Start` verdiğinde) 64-step sequencer çalışmaya başlar.
3. **Sequencer Aç / Kapat (Normal Klavyeye Dönme):** `Shift + Pad 1 (Arp)` tuşuna tek bas-bırak yaparak sequencer'ı anında kapatıp normal klavyeye dönebilir veya tekrar açabilirsin.
4. **Pad Bank A / B Geçişi:** `Shift + Pad 3` ile **`Pad Bank A`** *(Adım 1–8 kontrolü)* ve **`Pad Bank B`** *(Shift'siz `Pad 5 = Stop` / `Pad 6 = Start` ve performans pad'leri)* arasında geçiş yaparsın.
5. **Hızlı MIDI Kanalı Değiştirme (`Shift + Klavye Tuşu`):**
   - `Ch 1–4`: **Roland SH-4d** Synth Part 1–4 | `Ch 5`: **SH-4d** Ritim | `Ch 6`: **Donner B1** *(303 Bass)* | `Ch 10`: **Donner D1** | `Ch 14`: **Boss RC-505mkII** Kontrol (`RX CTL`).

---

## 2. Master Start / Stop & BPM Kontrolü

| Kontrol | Nerede Aktif? | İşlevi | OLED Ekran (`Üst` / **`Alt`**) |
| :--- | :--- | :--- | :--- |
| **`Pad 6`** *(Yeşil LED)* | Normal presetlerin tümünde (**Bank A & B**) ve `OTF 64s` modunda **`Pad Bank B`**'de **Shift'siz** *(Bank A'da: `Shift + Pad 6`)* | **Master START (`0xFA`) + `24 PPQN` Saat (`0xF8`)** başlatır ve sequencer'ı **1. adımdan** ateşler *(Çalarken Parlak Zümrüt Yeşili yanar)* | `Master Transport` / **`START (Play)`** |
| **`Pad 5`** *(Kırmızı LED)* | Normal presetlerin tümünde (**Bank A & B**) ve `OTF 64s` modunda **`Pad Bank B`**'de **Shift'siz** *(Bank A'da: `Shift + Pad 5`)* | **Akıllı Çift Kademeli STOP (`0xFC`):**<br>• **1. Basış:** Cihazları durdurur, `0xF8` saatini sıcak tutar.<br>• **2. Basış:** `0xF8` saat sinyalini tamamen keser (`Free`). | 1. Basış: `Master Transport` / **`STOP (Clk ON)`**<br>2. Basış: `Master Transport` / **`STOP (Free)`** |
| **Siyah Ana Knob Çevirme** | **Tüm presetlerde** *(Tek el, basmadan)* | **Canlı Master BPM (`30 – 270 BPM`)** — Hem dahili 64-step hızı hem 5-pin MIDI `0xF8` saatini anında değiştirir | Grafik `Rate` / **`120 BPM`** |
| **Siyah Ana Knob Tek Tık** | `OTF 64s` modunda | **Anında 1. Adıma Hizala (`Step 1 Reset`)** — Canlı mezür başı yakalamak için sayacı (ve varsa aktif Pattern Chain'i) `Step 1`'e çeker | `Sequencer Sync` / **`-> Step 1`** |
| **Siyah Ana Knob Basılı Tut + Çevir** | `OTF 64s` modunda | **Global Transpose (`-12 .. +12` yarım ses)** — 64 adımın tamamını tek hareketle transpoze eder | `Global Transpose` / **`+5 Semitones`** |

> **İpucu (`Donner D1` Step 1 Senkronu):** Zinciri durdurduktan sonra tekrar tam 1. adımdan başlatmadan önce D1 üzerindeki `[PLAY]` tuşuna iki kez (`Kapat -> Aç`) basıp ışığını hazır bırakman, ardından MiniLab 3'te `Pad 6`'ya basman yeterlidir.

---

## 3. Nota Yazma, Step Lock & Mute (`Pad Bank A`)

`OTF 64s` modunda **`Pad Bank A`** seçiliyken 8 Pad, o an seçili sayfadaki **8 adımı** temsil eder:

| İşlem | Nasıl Yapılır? | OLED Ekran (`Üst` / **`Alt`**) |
| :--- | :--- | :--- |
| **Kök Nota Değiştirme (`Root Transpose`)** | Pad'lere basmadan klavyeden **tek bir tuşa** bas *(Varsayılan kök: `C4 = 60`)* | `Root Transpose` / **`F3  (53)`** |
| **Hızlı Sıralı Nota Yazma** | Klavyede bir tuşu basılı tutarken sırayla **2. – 8. tuşlara** bas: aktif sayfadaki `Adım 1..8`'e sırayla nota + velocity yazar | `Step X Note` / **`D#4  v108`** |
| **Adıma Nota Kilitleme (`Step Lock`)** | **`Pad 1–8`** (tek veya birden fazla pad aynı anda!) **basılı tut + Klavyeden bir tuşa bas**: o adımlara notayı ve tuş hızını (velocity) kilitler, kapalıysa Mute/Skip'i açar | Tek adım: `Step 5 Note` / **`G3  v115`**<br>Çoklu adım: `Multi-Step Note` / **`G3  v115`** |
| **Klavyesiz Yarım Ses Pitch Yazma** | **`Oct +` veya `Oct -` basılı tut + `Knob 1–8` çevir**: o adımın perdesini `-24 .. +24` yarım ses kaydırır ve duyulan gerçek notayı gösterir | `Step X Pitch` / **`+7st (G4)`** |
| **Adım Oktav Kaydırma** | **`Oct +` veya `Oct -` basılı tut + `Pad 1–8` tıkla**: o adımı `-2 .. +2` oktav aralığında taşır | `Step X Octave` / **`+1 Oct (C5)`** |
| **Adım Susturma (`Mute / Unmute`)** | **`Pad 1–8` tek dokunuş (bas-bırak)**: adımı notayı silmeden susturur veya tekrar açar | `Step X Mute` / **`MUTED`** veya **`ACTIVE`** |

---

## 4. Doğrudan Kontroller (`Knob 1–8` & `Fader 1–4` — Hiçbir Tuşa Basmadan)

### A. `Knob 1–8` — Adım İfade Modu (`Step X Mode`)
Her knob, o anki sayfadaki ilgili adımın (`1–8`) çalış karakterini belirler:

| Knob Değeri | OLED Alt Satır | Müzikal Etkisi | Pad LED Rengi |
| :---: | :--- | :--- | :--- |
| **`0 – 15`** | **`Skip (0..15)`** | **Adımı Atla** — Bu adım döngüden çıkarılır *(aksak / kısalan ritimler için)* | Sönük (Kapalı) |
| **`16 – 31`** | **`Sub-Oct (16..31)`** | **`-1` Oktav Bas** — Adımı 1 oktav kalından çalar | Derin Mavi |
| **`32 – 68`** | **`Normal (32..68)`** | **Normal Adım** — Yazılan nota ve velocity ile çalar | Turkuaz *(303 Slide açıksa Asit Yeşili)* |
| **`69 – 80`** | **`Oct+Acc (69..80)`** | **`+1` Oktav + Accent** — 1 oktav tiz ve maksimum vuruşla (`Vel 127`) çalar | Kehribar / Turuncu |
| **`81 – 92`** | **`Ratch 2x (81..92)`** | **2x Ratchet** — Tek adım süresinde 2 hızlı vuruş | Mor |
| **`93 – 104`** | **`Ratch 3x (93..104)`** | **3x Ratchet** — Tek adım süresinde 3 hızlı vuruş | Macenta |
| **`105 – 115`** | **`Ratch 4x (105..115)`** | **4x Ratchet** — Tek adım süresinde 4 makineli vuruş | Sıcak Pembe |
| **`116 – 127`** | **`Random (116..127)`** | **Canlı Random** — Seçili gam/makam içinde her turda rastgele nota üretir | Buz Beyazı |

### B. `Fader 1–4` — Gam, Yön, Döngü Uzunluğu & Canlı CC

| Fader | OLED Üst Başlık | Değer Bölgeleri (`0 – 127`) |
| :--- | :--- | :--- |
| **`Fader 1`** | `Scale Quantizer` | `0–15` **Chromatic** \| `16–31` **Major** \| `32–47` **Natural Min** \| `48–63` **Minor Pent** \| `64–79` **Dorian** \| `80–95` **Phryg Hicaz** \| `96–111` **Harmonic Min** \| `112–127` **Acid Blues** |
| **`Fader 2`** | `Play Direction` | `0–15` **Forward** \| `16–31` **Page Loop** *(sadece seçili 8 adımı döndürür!)* \| `32–47` **Ping-Pong** \| `48–63` **Reverse** \| `64–79` **Chain AAAB** \| `80–95` **Chain ABBA** \| `96–111` **A-B-A-revB** \| `112–127` **A-revA-B-rB** |
| **`Fader 3`** | `Active Loop Len` | En alt (`0–15`) veya en üst (`112–127`): **Tam Pattern Uzunluğu (`8/16/32/64 Steps`)**.<br>Orta bölge (`16–111`): Döngüyü canlı olarak **`2 .. N Steps`** poliritmik uzunluğa kırpar. |
| **`Fader 4`** | *Akıllı Synth CC* | `Shift` gerektirmeden doğrudan atanmış MIDI CC gönderir *(Örn: `Cutoff (CC74)` / **`84  (Ch 1)`** veya `Fader 4 (CC17)`)*. |

---

## 5. 64-Adım Sayfa Yönetimi, Fold-Duplicate & 303 Slide (`Hold` Katmanı)

### A. Sayfa Seçimi & Pattern Büyütme / Küçültme
- **`Hold` Basılı Tut (Canlı 8-Sayfa Haritası):** Pad 1–8 anında 8 sayfayı (`1–8` .. `57–64`) gösterir:
  - **Altın Sarısı:** Seçili düzenleme sayfası
  - **Parlak Yeşil:** O an çalan sayfa *(İkisi aynı sayfaysa: **Parlak Beyaz-Altın**)*
  - **Camgöbeği (Açık Mavi):** Pattern uzunluğu içindeki diğer aktif sayfalar | **Sönük:** Uzunluk dışı sayfalar
- **`Hold` + `Pad 1–8`:** Düzenlenecek sayfayı seçer (`Pattern Page` / **`P1 (1-8)`** .. **`P8 (57-64)`**).
- **`Hold` + `Oct +` *(Fold-Duplicate)*:** Mevcut pattern'i tüm nota, ifade ve 303 slide ayarlarıyla ikiye katlayıp yeni yarıya kopyalar (**`8 -> 16 -> 32 -> 64`**) ve otomatik olarak yeni sayfaya geçer (`Pattern Length` / **`Fold -> 16`**, **`Fold -> 32`**, **`Fold -> 64`**).
- **`Hold` + `Oct -` *(Yarıya İndir)*:** Pattern uzunluğunu yarıya düşürür (**`64 -> 32 -> 16 -> 8`**) (`Pattern Length` / **`Len -> 32`**, **`Len -> 16`**, **`Len -> 8`**).
- **`Hold` + Siyah Knob Tek Tık:** **Auto Page-Follow** açar/kapatır (`Auto PageFollow` / **`ON (Follow)`** veya **`OFF (Manual)`**).

### B. `Hold` + Knob / Fader İkincil Kontrolleri

| Kombinasyon | İşlev | OLED Ekran (`Üst` / **`Alt`**) |
| :--- | :--- | :--- |
| **`Hold` + `Knob 1–8`** | **Adım Olasılığı (`%10–%99`) & Gerçek TB-303 Slide (`>=108`):**<br>• `0–99`: Tetiklenme olasılığı (`Prob: 10%` .. `Prob: 99%`)<br>• `100–107`: Normal %100 tetikleme (`100% Trigger`)<br>• `108–127`: **Gerçek 303 Legato Slide / Tie (`303 Slide ON`)** — Donner B1 ve SH-4d mono seslerde notaları birbirine kaydırarak bağlar *(LED Asit Yeşili yanar)* | `Step X Prob/303` / **`Prob: 75%`**, **`100% Trigger`**, **`303 Slide ON`** |
| **`Hold` + `Fader 1`** | **Gate Length** *(Nota uzunluğu)* | Grafik `Gate` ekranı |
| **`Hold` + `Fader 2`** | **Swing (`%50 – %75`)** | Grafik `Swing` ekranı |
| **`Hold` + `Fader 3`** | **Time Division (`1/4` .. `1/32T`)** | Grafik `Time Div` ekranı |
| **`Hold` + `Fader 4`** *(Alt/ortadan en tepeye `>=105` it)* | **Dice Mutator (Sayfa Melodi Üretici):** Seçili sayfadaki 8 adımı (1. adımı kök notada koruyarak) yeni bir melodiyle değiştirir | `Dice Mutator` / **`Page X Rolled`** |

---

## 6. Kalıcı Hafıza (`8 Pattern Slotu`) & Pattern Chain (Arka Arkaya Çaldırma)

MiniLab 3'ün dahili Flash belleğinde **8 adet tam 64-step pattern** saklanır ve istenirse **16 halkaya kadar arka arkaya zincirlenerek (`Pattern Chain`)** otomatik çaldırılabilir:

| İşlem | Tuş Kombinasyonu | OLED Ekran (`Üst` / **`Alt`**) |
| :--- | :--- | :--- |
| **Tek Pattern Yükle (`Load`)** | **Siyah Ana Knob Basılı Tut + Tek `Pad 1–8`** *(Varsa aktif zinciri kapatır, sadece seçilen slotu döngüye alır)* | `Load Pattern` / **`Slot 1`** .. **`Slot 8`** |
| **Patternleri Arka Arkaya Zincirle (`Pattern Chain`)** | **Siyah Ana Knob Basılı Tutarken Sırayla Birden Fazla Pad'e Bas** *(16 halkaya kadar; aynı slota üst üste de basabilirsin — örn. `Pad 1 -> Pad 1 -> Pad 2 -> Pad 3`)* | `Pattern Chain` / **`1>1>2>3 (4)`** |
| **Kalıcı Kaydet (`Save to Flash`)** | **`Hold` + Siyah Ana Knob Basılı Tut + `Pad 1–8`** | `Save to Flash` / **`Slot 1 Saved`** .. **`Slot 8 Saved`** |
| **Anında Kayıtlı Haline Dön (`Reload`)** | **`Oct -` + `Oct +` (İkisine Aynı Anda Bas)** *(Canlı doğaçlama/mutasyon ve transpose sonrası tek hamlede kayıtlı pattern'e geri döner)* | `Reload Pattern` / **`Slot X Reset`** |

- **Canlı 8-Slot & Zincir Haritası (`Siyah Ana Knob` Basılı Tutulduğunda):**
  - **Parlak Zümrüt Yeşili:** O an çalan aktif Pattern Slotu *(Zincir ilerledikçe yeşil ışık sıradaki slota otomatik atlar)*
  - **Parlak Altın Sarısı:** Aktif `Pattern Chain` (zincir) içindeki diğer slotlar
  - **Yumuşak Mor:** Diğer kullanılabilir slotlar (`Slot 1–8`)
- **Zincir Senkronu:** Her pattern kendi uzunluğu (`8/16/32/64` adım) tamamlandığı anda kesintisiz bir sonraki slota geçer. `Pad 6 (START)`, harici `MIDI Start (0xFA)` veya **Siyah Knob Tek Tık (`Step 1 Reset`)** verildiğinde zincir otomatik olarak **1. halkadan** başlar.

**Hazır Başlangıç Groove'ları** *(Üzerine kendi kaydını yazana kadar)*:
- **Slot 1:** 8-Step Klasik Groove (`Chromatic`)
- **Slot 2:** 16-Step Donner B1 Acid Bassline (`Acid Blues`, gerçek 303 Slide adımlarıyla)
- **Slot 3:** 16-Step SH-4d Minor Techno (`Natural Min`, Sub-Oct & Ratchet adımlarıyla)
- **Slot 4:** 32-Step Melodik Arpej (`Natural Min`, 303 Slide + Ratchet adımlarıyla)

---

## 7. `Shift` Katmanı — Canlı Synth MIDI CC Kontrolü (`SH-4d`, `B1`, `RC-505mkII`)

Sequencer arka planda çalmaya devam ederken **`Shift` basılı tutarak** 8 Knob ve 4 Fader'ın tamamıyla cihazlarının filtre, zarf ve efektlerini canlı kontrol edebilirsin:

- **`Shift` + `Knob 1–8` / `Fader 1–4`:**
  - MCC'de knoblar `Relative` kalsa bile her zaman pürüzsüz **`0 – 127` Absolute MIDI CC** üretir ve hem **5-pin DIN MIDI Out** hem **USB MIDI Out** üzerinden gönderir.
  - **OLED 1. Satır (Başlık):** Atanan CC numarasına göre akıllı parametre ismi gösterir:  
    `Cutoff (CC74)`, `Resonance (CC71)`, `Attack (CC73)`, `Decay (CC75)`, `Release (CC72)`, `Reverb (CC91)`, `Chorus (CC93)`, `Delay (CC94)`, `ModWheel (CC1)`, `Volume (CC7)`, `Pan (CC10)`, Ch 14'te `RC505 T1 (CC1)`..`RC505 T5 (CC5)` veya özel CC'lerde tam `Knob 1 (CC21)` / `Fader 4 (CC17)`.
  - **OLED 2. Satır (Değer):** Anlık `0–127` değer ve hedef MIDI kanalı — örn. **`68  (Ch 1)`**.

---

## 8. Hızlı RGB Pad Renk Özeti (`Pad Bank A` — Adım Görünümü)

| Renk | Anlamı |
| :--- | :--- |
| **Parlak Zümrüt Yeşili** | O an çalan aktif adım (`Playhead`) |
| **Parlak Kırmızı / Gül** | Playhead şu an Mute veya Skip olan bir adımın üzerinde |
| **Parlak Altın Sarısı** | Basılı tutulan Pad *(Step Lock için klavyeden nota bekliyor)* |
| **Turkuaz** | Normal aktif adım (`Knob = 32–68`) |
| **Asit Limonu Yeşili** | **303 Slide / Tie** açık olan adım (`Hold + Knob >= 108`) |
| **Derin Mavi** | `-1` Oktav (`Sub-Oct` veya `Oct-` kaydırılmış adım) |
| **Kehribar / Turuncu** | `+1` Oktav + Accent (`Oct+Acc` veya `Oct+` kaydırılmış adım) |
- **Mor / Macenta / Pembe** | Ratchet `2x` (Mor) / `3x` (Macenta) / `4x` (Pembe) |
| **Buz Beyazı** | Canlı Random (Rastgele gam içi nota) |
| **Loş Kırmızı / Tam Sönük** | Loş Kırmızı = **Mute** edilmiş adım \| Tam Sönük = **Skip** (`Knob = 0–15`) |

---

## 9. `Pad Bank B` — Dawless Riser & Drop Performans Deck (`Shift + Pad 3`)

`OTF 64s` ve `Pattern Chain` arka planda kesintisiz çalmaya devam ederken **`Shift + Pad 3`** ile **`Pad Bank B`**'ye geçtiğinde 8 Pad ve **Modulation Şeridi**, tüm donanım zincirini tek elden yöneten bir **Riser & Drop Masasına** dönüşür:

| `Pad Bank B` Kontrolü | LED Rengi | Görevi & Çoklu Donanım MIDI Etkisi | OLED Göstergesi |
| :--- | :--- | :--- | :--- |
| **`Pad 1` (Basılı Tut)** | Camgöbeği → Beyaz Flaş | **Hızlanan Drum Roll (`Donner D1` Ch 10):** `SD (38)` + `HC (39)` vuruşlarını saate kilitli olarak `1/8 -> 1/16 -> 1/32 -> 1/64` hızlandırır ve Velocity'yi `68 -> 125` yükseltir *(Mod şeridiyle de anında hızlandırılabilir)*. | `Drum Roll (D1)` / **`1/8 -> 1/64`** |
| **`Pad 2` (Tek Tık)**<br>*(veya `Hold + Pad 2`)* | Kehribar → Altın Nabız | **4-Bar Auto-Riser** *(`Hold + Pad 2` = **8-Bar**)* — Eller serbest otomatik yükselme:<br>• **`SH-4d` (Ch 1–4):** Orijinal `Cutoff (CC74)` → `127` & `Reverb (CC91)` → `110` tarar<br>• **`RC-505mkII` (Ch 14):** `CC80 = 127` (`INPUT FX ON`) açar ve `CC81` (`INPUT FX CONTROL`) `0 -> 127` tarar<br>• Son mezürde otomatik `D1` `1/16 -> 1/64` Snare+Clap Roll ekler ve **Beat 1.1'de otomatik DROP yapar!** *(İptal için tekrar tıkla)*. | `Auto-Riser 4B` / **`DROP IN: 4.4` .. `1.1`** |
| **`Pad 3` (Basılı Tut)**<br>*(veya `Hold + Pad 3`)* | Elektrik Moru → Gökyüzü | **Synth Pitch Rise** (`0 -> +8160` 14-bit Pitch Bend + `CC1` Modülasyon).<br>**`Hold + Pad 3`:** **Tape-Stop Dive** (`0 -> -8172` plak/bant freni). Bırakınca anında `0` merkeze döner. | `Synth Riser` / **`Pitch Rise UP`**<br>`Tape-Stop FX` / **`Pitch DIVE`** |
| **`Pad 4` (Basılı Tut)** | Macenta Flaş | **Pre-Drop Vacuum (Mute Kill):** Basılı tutulduğu sürece `OTF 64s` notalarını ve uzayan akorları (`Ch 1–4` & `Ch 6` `CC123`) bıçak gibi keser; bırakınca groove anında geri girer. | `Pre-Drop Gate` / **`VACUUM MUTE`** |
| **`Pad 5`** | Kırmızı | **Master STOP (`0xFC`)** *(Aktif riser/roll varsa güvenli biçimde orijinal değerlere sıfırlar)* | `Master Transport` / **`STOP`** |
| **`Pad 6`** | Yeşil | **Master START (`0xFA` + `24 PPQN`)** | `Master Transport` / **`START (Play)`** |
| **`Pad 7` (Bas / Tık)**<br>*(veya `Hold + Pad 7`)* | Altın Sarısı | **`Donner D1` Uplifter / FX Sample Tetikleyici (Ch 10):**<br>• Tek basış: **`SMP1` (`Note 60`)** \| `Hold + Pad 7`: **`SMP3` (`Note 64`)** | `D1 FX Trigger` / **`SMP1 Uplifter`** |
| **`Pad 8` (Tek Tık)** | Ateş Turuncusu → Beyaz Patlama | **THE DROP! (Anında Orijinal Değerlere Dönüş + Impact):** `< 1 ms` içinde tüm `SH-4d` (`Ch 1–4`) ve `RC-505mkII` (`Ch 14`) parametrelerini **riser öncesi orijinal değerlerine** döndürür, sequencer + `Pattern Chain`'i **`Step 1`**'e hizalar ve **`Donner D1` Crash (`49`) + Impact (`SMP2 = 62`)** ateşler! | `Riser & Drop` / **`>>> DROP! <<<`** |
| **`Modulation Şeridi`** *(Bank B'de)* | — | **Manuel Macro Riser (`%0 – %100`):** Parmağını yukarı kaydırarak çoklu cihaz (`SH-4d` + `RC-505mkII`) gerilimini kendi hızında yükselt; tepe noktasında **`Pad 8` (`DROP`)**'a vurarak her şeyi orijinal sese geri oturt! | `Manual Riser` / **`Tension: 78%`** |

> **Boss RC-505mkII (`MIDI Ch 14`) Önerilen Assign Ayarı:**
> - **Assign A:** `Source = #CC 80`, `Mode = MOMENT`, `Target = INPUT FX ON/OFF` *(Örn. Input FX olarak HPF veya Reverb seçili)*
> - **Assign B:** `Source = #CC 81`, `Mode = MOMENT`, `Target = INPUT FX CONTROL`
> - **Orijinal Değer Hafızası:** `Shift + Knob` veya `Fader` ile `SH-4d` (`Ch 1–4` `CC74 / CC91`) veya `RC-505` (`Ch 14` `CC81`) üzerinde yaptığın her ayar otomatik olarak yeni **"Orijinal Değer"** kabul edilir; Drop anında her zaman senin bıraktığın gerçek değere geri döner!
