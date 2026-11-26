# Arturia MiniLab 3 — `OTF 64s` Adım Adım Tam Donanım Test Rehberi

**Test Edilen Firmware:** [minilab-3_Firmware_Update_1.2.0_OTF_Pro_64Step.mnl3](file:///c:/Users/orkun/.gemini/antigravity/scratch/dawless_project/minilab3_otf/minilab-3_Firmware_Update_1.2.0_OTF_Pro_64Step.mnl3)  
**Hedef Kurulum:** `MiniLab 3 (5-Pin MIDI Out)` → `Roland SH-4d` → `Donner B1` → `Boss RC-505mkII` → `Donner D1` *(veya tek bir synth / DAW MIDI monitörü ile de birebir uygulanabilir)*

> [!TIP]
> Testlere başlamadan önce **MIDI Control Center** uygulamasını kapat. Böylece USB-MIDI portu serbest kalır ve MiniLab 3 tam performans modunda çalışır.

---

## Faz 0 — Ön Hazırlık (`1 Dakika`)

- [ ] **0.1 Bağlantı:** MiniLab 3'ün USB güç/veri kablosunu ve **5-Pin MIDI Out** kablosunu `Roland SH-4d` girişine tak *(veya test edeceğin synth'i aç)*.
- [ ] **0.2 Hedef Ses:** İlk testleri net duymak için **Roland SH-4d Part 1 (MIDI Ch 1)** üzerinde kısa/belirgin bir synth veya pluck sesi seç (`Shift + Sol En Alt Do [C]` tuşuna basarak MiniLab 3'ün **MIDI Ch 1**'de olduğundan emin ol).
- [ ] **0.3 Özel Preset İsimleri Kontrolü:** **`Shift` basılı tutarken `Pad 2` (`Prog`)** tuşuna basılı tut ve **Siyah Ana Knob**'u yavaşça çevir.
  - **Beklenen OLED:** Fabrika `User 1..5` isimleri yerine sırasıyla **`OTF64s`**, **`SH-4d`**, **`RC-505`**, **`uKORG`**, **`K2000R`** isimlerini görmelisin. **`OTF64s`** üzerinde bırak.

---

## Faz 1 — `OTF 64s` Modunu Açma & Kapatma

- [ ] **1.1 `OTF 64s` Moduna Giriş:** **`Shift` + `Pad 1` (`Arp`)** basılı tutarak Arpeggiator menüsünü aç ve **`Knob 1` (`Mode`)**'i en sağa çevir.
  - **Beklenen OLED:** `Order` yerine **`OTF 64s`** yazmalı.
  - **Siyah Ana Knob**'a bir kez tıklayarak (veya `Shift`'i bırakarak) ana ekrana dön.
- [ ] **1.2 Otomatik Başlangıç (`Slot 1`):** Klavyeden orta **`Do (C4)`** tuşuna bir kez bas.
  - **Beklenen Sonuç:** `OTF 64s` seçildiği anda Arp motoru otomatik devreye girdiği için 8 adımlı hazır başlangıç groove'u (`Slot 1`) çalmaya başlar; `Pad Bank A`'da **Parlak Zümrüt Yeşili** adım ışığı (`Playhead`) `Pad 1 → Pad 8` arasında akar.
- [ ] **1.3 Normal Klavyeye Anlık Dönüş (`Arp ON/OFF`):** **`Shift` + `Pad 1` (`Arp`)** tuşuna kısa bas-bırak yap.
  - **Beklenen Sonuç:** Sequencer durur ve klavye normal polifonik MIDI klavye olarak çalar. Tekrar **`Shift` + `Pad 1`** yaptığında `OTF 64s` kaldığı yerden geri gelir.

---

## Faz 2 — Master Start / Stop (`Pad 5 & 6`), Canlı BPM & Transpose

- [ ] **2.1 `Pad Bank B` Shift'siz Transport LED Kontrolü:** **`Shift` + `Pad 3`** ile **`Pad Bank B`**'ye geç.
  - **Beklenen Pad LED:** **`Pad 5` Kırmızı** (Stop), **`Pad 6` Yeşil** (Start/Hazır) yanmalı.
- [ ] **2.2 Tek Tuş Master START (`Pad 6`):** `Shift`'e **basmadan** doğrudan **`Pad 6`**'ya bas.
  - **Beklenen OLED:** Üst satır `Master Transport` / Alt satır **`START (Play)`**.
  - **Beklenen Sonuç:** `Pad 6` **Parlak Zümrüt Yeşili** yanar; hem 5-pin DIN hem USB üzerinden `0xFA (Start)` + `24 PPQN (0xF8)` saat sinyali gider (`SH-4d`, `B1`, `RC-505mkII`, `D1` aynı anda başlar) ve MiniLab 3 `Step 1`'den çalar.
- [ ] **2.3 Çift Kademeli Master STOP (`Pad 5`):**
  1. `Shift`'e basmadan **`Pad 5`**'e **1. kez** bas:
     - **Beklenen OLED:** `Master Transport` / **`STOP (Clk ON)`** *(Cihazlar durur ama `0xF8` saat sinyali kesilmez; `Pad 6` normal hazır yeşile döner)*.
  2. **`Pad 5`**'e **2. kez** bas:
     - **Beklenen OLED:** `Master Transport` / **`STOP (Free)`** *(`0xF8` saat sinyali de tamamen serbest bırakılır)*.
  3. Tekrar **`Pad 6`**'ya basarak müziği yeniden başlat, ardından **`Shift` + `Pad 3`** ile **`Pad Bank A`**'ya (8 adım görünümüne) geri dön *(Bank A'dayken de `Shift + Pad 6` = Start, `Shift + Pad 5` = Stop çalıştığını doğrula)*.
- [ ] **2.4 Siyah Ana Knob ile Canlı BPM (`30 – 270 BPM`):** Siyah Ana Knob'a **basmadan** sağa ve sola çevir.
  - **Beklenen OLED:** Grafik `Rate` ekranında BPM değeri **`30` ile `270`** arasında değişir; bağlı tüm cihazlar anında hızlanır/yavaşlar. Test için **`120 BPM`** civarına getir.
- [ ] **2.5 Anında 1. Adıma Hizalama (`Step 1 Reset`):** Sequencer ortalarda bir adımda çalarken **Siyah Ana Knob'a tek tıkla (bas-bırak)**.
  - **Beklenen OLED:** `Sequencer Sync` / **`-> Step 1`**.
  - **Beklenen Sonuç:** Playhead kesintisiz biçimde anında `Pad 1` (`Step 1`)'e atlar.
- [ ] **2.6 Global Semitone Transpose:** **Siyah Ana Knob'u basılı tutarak** sağa 5 tık çevir, sonra sola çevirip `0`'a geri getir.
  - **Beklenen OLED:** `Global Transpose` / **`+5 Semitones`** → **`0 Semitones`**. Tüm melodi bozulmadan yarım ses kayar.

---

## Faz 3 — Nota Yazma, Step Lock, Oktav & Adım Mute (`Pad Bank A`)

- [ ] **3.1 Kök Nota Değişimi (`Root Transpose`):** Hiçbir pad'e basmadan klavyeden **`Fa (F3)`** tuşuna, sonra tekrar **`Do (C4)`** tuşuna tek bas-bırak yap.
  - **Beklenen OLED:** `Root Transpose` / **`F3  (53)`** → **`C4  (60)`**. Tüm pattern yeni kök notaya taşınır.
- [ ] **3.2 Tek Adıma Nota Kilitleme (`Single Step Lock`):** **`Pad 3`'ü basılı tut** *(Pad 3 **Parlak Altın Sarısı** yanar)* ve klavyeden sertçe **`Sol (G4)`** tuşuna bas, sonra Pad 3'ü bırak.
  - **Beklenen OLED:** `Step 3 Note` / **`G4  v110`** *(tuş hızına göre `v` değeri değişir)*.
  - **Önemli Kontrol:** Pad 3'ü bıraktığında adım **Mute olmamalı**, yeni notayı çalmaya devam etmeli.
- [ ] **3.3 Çoklu Adıma Tek Seferde Nota Kilitleme (`Multi-Step Lock`):** **`Pad 1` ve `Pad 5`'i aynı anda basılı tut** *(ikisi de Altın Sarısı yanar)* ve klavyeden **`Do (C3)`** tuşuna bas.
  - **Beklenen OLED:** `Multi-Step Note` / **`C3  v...`**. Hem 1. hem 5. adıma aynı anda `C3` yazılır.
- [ ] **3.4 Klavyede Çoklu Tuş ile Sıralı Yazım:** Pad'lere dokunmadan klavyede **`Do (C4)`** tuşunu basılı tutarken sırayla **`Re`**, **`Mi`**, **`Sol`** tuşlarına bas.
  - **Beklenen OLED:** Sırasıyla `Step 2 Note`, `Step 3 Note`, `Step 4 Note` görünür ve adımlar sırayla güncellenir.
- [ ] **3.5 Klavyesiz Yarım Ses Perde (`Step Pitch`) & Adım Oktavı (`Step Octave`):**
  1. **`Oct +` basılı tut + `Knob 2`'yi sağa çevir:** OLED'de `Step 2 Pitch` / **`+7st (G4)`** gibi hem yarım ses farkı hem duyulan gerçek nota görünmeli.
  2. **`Oct +` basılı tut + `Pad 4`'e tıkla:** OLED'de `Step 4 Octave` / **`+1 Oct (...)`** görünmeli, Pad 4 **Kehribar/Turuncu** yanmalı. **`Oct -` + `Pad 4`** ile tekrar `0 Oct` yap *(ve `Oct+`/`Oct-` bıraktığında klavyenin genel oktavının kaymadığını doğrula)*.
- [ ] **3.6 Adım Susturma (`Mute / Unmute`):** **`Pad 2`**'ye tek dokun-bırak yap.
  - **Beklenen Sonuç:** OLED'de `Step 2 Mute` / **`MUTED`** yazar; Pad 2 **Loş Kırmızı** olur, yeşil playhead üzerinden geçerken **Parlak Kırmızı/Gül** yanar ve o adımda ses çıkmaz (ama ritim/sayım aksamaz). Tekrar **`Pad 2`**'ye dokun → **`ACTIVE`**.

---

## Faz 4 — `Knob 1–8` Adım İfade Modları & RGB Renk Testi

Sequencer çalarken sadece **`Knob 1`**'i (1. Adım) en soldan en sağa yavaşça çevirerek 8 ifade bölgesinin tamamını kontrol et:

| Test | `Knob 1` Aralığı | Beklenen OLED (`Step 1 Mode`) | Beklenen `Pad 1` Rengi | Beklenen Ses Davranışı |
| :---: | :---: | :--- | :--- | :--- |
| - [ ] **4.1** | `0 – 15` | **`Skip (0..15)`** | **Tam Sönük** | 1. adım tamamen **atlanır**; döngü 8 adımdan **7 adıma** düşer! |
| - [ ] **4.2** | `16 – 31` | **`Sub-Oct (16..31)`** | **Derin Mavi** | 1. adım `-1` oktav kalından çalar |
| - [ ] **4.3** | `32 – 68` | **`Normal (32..68)`** | **Turkuaz** | Normal nota ve yazılan velocity ile çalar |
| - [ ] **4.4** | `69 – 80` | **`Oct+Acc (69..80)`** | **Kehribar / Turuncu** | `+1` oktav tiz ve maksimum (`127`) vurguyla çalar |
| - [ ] **4.5** | `81 – 92` | **`Ratch 2x (81..92)`** | **Mor** | Tek adım içinde **2 hızlı vuruş** yapar |
| - [ ] **4.6** | `93 – 104` | **`Ratch 3x (93..104)`** | **Macenta** | Tek adım içinde **3 hızlı üçleme** yapar |
| - [ ] **4.7** | `105 – 115` | **`Ratch 4x (105..115)`** | **Sıcak Pembe** | Tek adım içinde **4 makineli vuruş** yapar |
| - [ ] **4.8** | `116 – 127` | **`Random (116..127)`** | **Buz Beyazı** | Her turda seçili gam içinden **rastgele yeni nota** üretir |

*(Test sonunda `Knob 8`'i `Random` [`120`]'de bırak, `Knob 1`'i `Normal` [`50`]'ye al — bir sonraki Gam testinde çok net duyacaksın).*

---

## Faz 5 — Doğrudan `Fader 1–4` Kontrolleri (Tuşsuz)

- [ ] **5.1 `Fader 1` — Gam / Makam Kuantizasyonu (`Scale Quantizer`):** `Fader 1`'i aşağıdan yukarı kademeli kaydır.
  - **Beklenen OLED:** `Scale Quantizer` başlığı altında sırasıyla **`Chromatic`** → **`Major`** → **`Natural Min`** → **`Minor Pent`** → **`Dorian`** → **`Phryg Hicaz`** → **`Harmonic Min`** → **`Acid Blues`**.
  - **Beklenen Ses:** Özellikle **`Phryg Hicaz`** ve **`Acid Blues`** seçtiğinde hem mevcut notaların hem `Knob 8`'deki `Random` adımın anında o makama/gama oturduğunu duy.
- [ ] **5.2 `Fader 2` — Çalma Yönü (`Play Direction`):** `Fader 2`'yi aşağıdan yukarı kaydır.
  - **Beklenen OLED & Hareket:** **`Forward`** → **`Page Loop`** *(sadece seçili 8 adımı döndürür)* → **`Ping-Pong`** *(1→8→1 sarkaç)* → **`Reverse`** *(8→1 ters)* → **`Chain AAAB`** → **`Chain ABBA`** → **`A-B-A-revB`** → **`A-revA-B-rB`**. Test bitince en alta (**`Forward`**) çek.
- [ ] **5.3 `Fader 3` — Canlı Döngü Kırpma (`Active Loop Len`):** `Fader 3`'ü ortaya doğru çek.
  - **Beklenen OLED:** `Active Loop Len` / **`5 Steps`** *(veya `3 Steps`, `6 Steps`)* — poliritmik kısa döngü oluşur. En alta (`0`) veya en üste (`127`) çektiğinde **`8 Steps`** tam uzunluğa döner.
- [ ] **5.4 `Fader 4` — Doğrudan Canlı Synth CC:** `Fader 4`'ü hareket ettir.
  - **Beklenen OLED:** `Shift`'e basmadan doğrudan 2 satırlı CC ekranı *(örn. `Fader 4 (CC17)` veya preset CC ismine göre `Cutoff (CC74)` / **`85  (Ch 1)`**)* görünür ve synth'e CC gider.

---

## Faz 6 — `Hold + Oct + / Oct -` (`Fold-Duplicate`), 64-Adım Sayfalar & Page-Follow

> [!IMPORTANT]
> Bu faz, son güncellemede düzeltilen **`Hold + Oct +`**, **`Hold + Oct -`** ve **`Hold + Siyah Knob Tık`** kontrollerini doğrular.

- [ ] **6.1 Canlı 8-Sayfa Haritası (`Hold` Basılı Tut):** **`Hold`** tuşunu basılı tut ve Pad 1–8'e bak *(Slot 1 şu an 8 adım uzunluğunda)*.
  - **Beklenen Pad LED:** **`Pad 1`** Parlak Altın/Beyaz-Altın *(aktif 1. sayfa)*, **`Pad 2–8`** ise uzunluk dışı olduğu için sönük olmalı.
- [ ] **6.2 `Hold + Oct +` ile `8 → 16 → 32 → 64` Katlama (`Fold-Duplicate`):** **`Hold` tuşunu hiç bırakmadan** **`Oct +`** tuşuna 3 kez bas:
  1. **1. Basış (`Hold + Oct +`):**
     - **OLED:** `Pattern Length` / **`Fold -> 16`**.
     - **Pad LED (`Hold` hala basılıyken):** `Pad 1` **Camgöbeği (Açık Mavi)** olur, **`Pad 2` Altın Sarısı** yanar *(otomatik 2. sayfaya geçtin ve ilk 8 adım 9–16'ya kopyalandı!)*.
  2. **2. Basış (`Hold + Oct +`):**
     - **OLED:** `Pattern Length` / **`Fold -> 32`**.
     - **Pad LED:** `Pad 1–4` aktif yanar (`Pad 3` Altın Sarısı, diğer aktif sayfalar Camgöbeği; çalan sayfa Yeşil akmaya başlar).
  3. **3. Basış (`Hold + Oct +`):**
     - **OLED:** `Pattern Length` / **`Fold -> 64`**.
     - **Pad LED:** **8 Pad'in tamamı** aktif yanar (`Pad 5` Altın Sarısı, diğerleri Camgöbeği, çalan sayfa Yeşil)!
  4. Şimdi **`Hold`** tuşunu bırak: Klavyenin Hold kilidi yanlışlıkla açılıp kapanmamalı, Pad'ler doğrudan 5. sayfanın (`Adım 33–40`) adımlarını göstermeli.
- [ ] **6.3 Sayfa Seçimi (`Hold + Pad 1–8`):** **`Hold` basılı tut + `Pad 2`**'ye bas.
  - **Beklenen OLED:** `Pattern Page` / **`P2 (9-16)`**. Bu sayfada `Pad 1 + Klavyeden yüksek bir nota (C5)` kilitle; çalarken 1. sayfada eski notayı, 2. sayfaya sıra geldiğinde yeni `C5` notasını duy!
- [ ] **6.4 Otomatik Sayfa Takibi (`Auto PageFollow`):** **`Hold` basılı tut + Siyah Ana Knob'a tek tıkla**.
  - **Beklenen OLED:** `Auto PageFollow` / **`ON (Follow)`**.
  - **Beklenen Görsel:** Sequencer `1 → 64` akarken sen hiçbir şeye dokunmadan Pad görünümü her 8 adımda bir otomatik olarak o an çalan sayfaya geçer! Tekrar **`Hold` + Siyah Knob Tık** yaparak **`OFF (Manual)`** modunu da doğrula.
- [ ] **6.5 `Hold + Oct -` ile Yarıya İndirme (`64 → 32 → 16 → 8`):** **`Hold` basılı tutarken `Oct -`** tuşuna arka arkaya 3 kez bas.
  - **Beklenen OLED:** Sırasıyla `Pattern Length` / **`Len -> 32`** → **`Len -> 16`** → **`Len -> 8`**. `Hold` basılıyken Camgöbeği sayfaların `8 → 4 → 2 → 1`'e indiğini gör.

---

## Faz 7 — Gerçek TB-303 Slide (`Donner B1`), Olasılık (`Prob`) & Dice Mutator

- [ ] **7.1 Donner B1 Kanalına Geçiş (İsteğe Bağlı):** Kurulumda Donner B1 bağlıysa **`Shift` + Klavyede soldan 6. tuş (`Fa / Ch 6`)** ile MIDI Kanal 6'ya geç *(veya SH-4d'de mono/portamento bir bass sesi seç)*.
- [ ] **7.2 Adım Olasılığı (`Probability %10–%99`):** **`Hold` basılı tut + `Knob 2`'yi sola** çevir.
  - **Beklenen OLED:** `Step 2 Prob/303` / **`Prob: 50%`** *(2. adım bazı turlarda çalar, bazı turlarda rastgele susar)*. Sağa `100` civarına getirince **`100% Trigger`** yazar.
- [ ] **7.3 Gerçek TB-303 Legato Slide (`>= 108`):** **`Hold` basılı tut + `Knob 2`'yi en sağa** çevir.
  - **Beklenen OLED:** `Step 2 Prob/303` / **`303 Slide ON`**.
  - **Beklenen Pad LED & Ses:** `Pad 2` **Asit Limonu Yeşili** yanar! `Step 2`'nin `Note Off` mesajı `Step 3`'ün `Note On` mesajından **sonraya** ertelendiği için Donner B1 (veya mono synth) kesintisiz gerçek 303 asit kayması (slide) yapar.
- [ ] **7.4 `Hold + Fader 1 / 2 / 3` (Gate, Swing, Time Div):** `Hold` basılı tutarken:
  - **`Fader 1`:** Grafik **`Gate`** ekranı açılır, notalar kısalır (`Staccato`) / uzar (`Tie`).
  - **`Fader 2`:** Grafik **`Swing`** ekranı açılır (`%50 – %75` groove sallanması).
  - **`Fader 3`:** Grafik **`Time Div`** ekranı açılır (`1/4`, `1/8`, `1/16`, `1/32` hız bölümü — test sonunda `1/16`'da bırak).
- [ ] **7.5 Dice Mutator (`Hold + Fader 4`):** `Fader 4`'ü ortaya/aşağıya indir, ardından **`Hold` basılı tutarken `Fader 4`'ü en tepeye (`>= 105`)** it.
  - **Beklenen OLED:** `Dice Mutator` / **`Page 1 Rolled`**.
  - **Beklenen Ses:** 1. adım kök notada sabit kalırken 2–8. adımlara yepyeni bir melodi dizilir!

---

## Faz 8 — 8 Kalıcı Flash Slotu (`Load`, `Reload`, `Save` & Güç Kesintisi Testi)

- [ ] **8.1 Canlı 8-Slot Haritası:** **Siyah Ana Knob'u basılı tut** ve Pad 1–8'e bak.
  - **Beklenen Pad LED:** O an çalan slot (`Pad 1`) **Parlak Zümrüt Yeşili**, diğer slotlar (`Pad 2–8`) **Yumuşak Mor** yanmalı.
- [ ] **8.2 Hazır 4 Başlangıç Groove'unu Dinleme (`Load`):** **Siyah Ana Knob basılıyken**:
  - **`Pad 2`**'ye bas → OLED: `Load Pattern` / **`Slot 2`** *(16 adımlı Donner B1 Acid Blues + 303 Slide groove'u)*.
  - **`Pad 3`**'e bas → OLED: `Load Pattern` / **`Slot 3`** *(16 adımlı SH-4d Minor Techno groove'u)*.
  - **`Pad 4`**'e bas → OLED: `Load Pattern` / **`Slot 4`** *(32 adımlı melodik arpej)*.
- [ ] **8.3 Anında Kayıtlı Haline Geri Dönüş (`Oct -` + `Oct +` Reload):** `Slot 2` çalarken birkaç pad'i Mute et ve Siyah Knob'a basıp çevirerek `+7` Transpose yap (pattern'i iyice boz). Ardından **`Oct -` ve `Oct +` tuşlarına aynı anda bas**.
  - **Beklenen OLED:** `Reload Pattern` / **`Slot 2 Reset`**.
  - **Beklenen Sonuç:** Transpose `0`'lanır ve `Slot 2` anında tertemiz kayıtlı haline döner *(klavye oktavı da kaymaz)*.
- [ ] **8.4 Kalıcı Flash Kaydı (`Save to Flash`):** `Slot 2` üzerinde `Pad 1 + Klavyeden yüksek bir nota` ile belirgin bir değişiklik yap, ardından **`Hold` + Siyah Ana Knob ikisini birden basılı tutarak `Pad 5`**'e bas.
  - **Beklenen OLED:** `Save to Flash` / **`Slot 5 Saved`**.
  - **Parmak Bırakma Sırası Testi:** Önce Siyah Knob'u, sonra `Hold`'u bırak — `Auto PageFollow` yanlışlıkla tetiklenmemeli.
- [ ] **8.5 Güç Kesintisi (Kalıcılık) Testi:**
  1. `Siyah Knob + Pad 1` ile `Slot 1`'e geç.
  2. MiniLab 3'ün **USB kablosunu çıkar** (cihaz tamamen kapansın), 3 saniye bekle ve **tekrar tak**.
  3. `OTF 64s` moduna girip **`Siyah Ana Knob + Pad 5`** yap (`Load Pattern` / **`Slot 5`**).
  - **Beklenen Sonuç:** Az önce `Slot 5`'e kaydettiğin pattern STM32 dahili Flash belleğinden birebir geri gelmeli!

---

## Faz 9 — Yeni Özellik: Pattern Chain (Patternleri Arka Arkaya Çaldırma)

- [ ] **9.1 4'lü Pattern Zinciri Kurma (`1>2>3>4`):** **Siyah Ana Knob'u basılı tut** ve parmağını Siyah Knob'dan **hiç kaldırmadan** sırayla **`Pad 1` → `Pad 2` → `Pad 3` → `Pad 4`**'e bas.
  - **Beklenen OLED:**
    - `Pad 1`'e bastığında: `Load Pattern` / **`Slot 1`**
    - `Pad 2`'ye bastığında: `Pattern Chain` / **`1>2 (2)`**
    - `Pad 3`'e bastığında: `Pattern Chain` / **`1>2>3 (3)`**
    - `Pad 4`'e bastığında: `Pattern Chain` / **`1>2>3>4 (4)`**
- [ ] **9.2 Canlı Zincir Takibi (Görsel & İşitsel):** Zincir çalarken **Siyah Ana Knob'u tekrar sadece basılı tut** (hiçbir pad'e basmadan izle):
  - **Beklenen Pad LED:** O an çalan slot **Parlak Zümrüt Yeşili**, zincirdeki diğer 3 slot **Parlak Altın Sarısı**, zincir dışındaki `Pad 5–8` **Yumuşak Mor** yanmalı.
  - **Beklenen Geçiş:** `Slot 1` (8 adım) bittiği anda yeşil ışık **otomatik olarak `Pad 2`'ye** (16 adım) atlamalı, ardından `Pad 3` (16 adım) → `Pad 4` (32 adım) → tekrar `Pad 1` döngüsüne kesintisiz girmeli!
- [ ] **9.3 Tekrarlı / Fill Zinciri (`AAAB` Yapısı):** **Siyah Ana Knob basılı tutarken** sırayla **`Pad 1` → `Pad 1` → `Pad 1` → `Pad 2`**'ye bas.
  - **Beklenen OLED:** `Pattern Chain` / **`1>1>1>2 (4)`** *(3 kez üst üste Slot 1 çalıp 4. turda Slot 2'yi fill olarak çalar!)*.
- [ ] **9.4 Zinciri Baştan Hizalama (`Step 1` & `START` Senkronu):** Zincir `Slot 2` üzerinde çalarken **Siyah Ana Knob'a tek tıkla** *(veya `Shift + Pad 6` START ver)*.
  - **Beklenen Sonuç:** Sadece adım sayacı değil, **Pattern Chain de anında 1. halkaya (`Slot 1`, `Step 1`)** sıfırlanmalı!
- [ ] **9.5 Zincirden Çıkıp Tek Slota Dönme:** **Siyah Ana Knob basılı tut + sadece tek `Pad 2`**'ye basıp bırak.
  - **Beklenen OLED:** `Load Pattern` / **`Slot 2`**. Zincir kapanır (`Altın Sarısı` zincir ışıkları söner) ve sadece `Slot 2` sonsuz döngüde çalar.

---

## Faz 10 — `Shift` Katmanı Akıllı Synth MIDI CC & 2-Satır OLED Ekranı

- [ ] **10.1 `Shift + Knob 1–8` Parametre İsmi + Değer Testi:** Sequencer arka planda çalmaya devam ederken **`Shift` basılı tut** ve **`Knob 1`..`Knob 8`**'i çevir.
  - **Beklenen OLED:** Eski tek satır `"Knob.."` yerine;
    - **1. Satır (Başlık):** Preset'teki CC numarasına göre tam parametre adı — örn. **`Cutoff (CC74)`**, **`Resonance (CC71)`**, **`Knob 1 (CC...)`**.
    - **2. Satır (Değer):** **`0` – `127`** arası pürüzsüz değer ve hedef kanal — örn. **`72  (Ch 1)`**.
  - **Beklenen Ses:** Sequencer ritmi hiç bozulmadan SH-4d / B1 filtresi veya efektleri canlı açılıp kapanır.
- [ ] **10.2 `Shift + Fader 1–4` Testi:** **`Shift` basılı tutarken `Fader 1–4`**'ü hareket ettir.
  - **Beklenen OLED:** `OTF 64s` içindeyken Fader 1–3 gam/yön değiştirmek yerine doğrudan Synth MIDI CC gönderir ve OLED'de isim + `0..127 (Ch X)` değerini gösterir.
- [ ] **10.3 Boss RC-505mkII Özel Başlık Testi (`MIDI Ch 14`):** **`Shift` + Klavyede 14. tuş (`Ch 14`)** seçiliyken *(veya `RC-505` presetinde CC 1–5 atanmış bir kontrolü çevirdiğinde)*:
  - **Beklenen OLED:** `CC1..CC5` için otomatik olarak **`RC505 T1 (CC1)`** .. **`RC505 T5 (CC5)`** / **`127  (Ch 14)`** başlığını gösterir.

---

## Faz 11 — Tam 5-Cihazlı Canlı Sahne Senkron Testi (`Final Check`)

Tüm 5-pin DIN zinciri (`MiniLab 3` → `SH-4d` → `B1` → `RC-505mkII` → `D1`) açıkken:

- [ ] **11.1 Durdurma & D1 Hazırlığı:** `Pad Bank B`'de **`Pad 5` (STOP)**'a bas, ardından **Donner D1** üzerindeki `[PLAY]` tuşuna iki kez (`Kapat → Aç`) basarak D1'i 1. adıma kur.
- [ ] **11.2 Tek Tuş Sahne Ateşleme:** MiniLab 3'te **`Pad 6` (START)**'a bas.
  - **Beklenen Final Sonuç:** MiniLab 3 (`Pattern Chain` 1. halkası, `Step 1`), **Roland SH-4d**, **Donner B1**, **Boss RC-505mkII** ve **Donner D1** milimetrik olarak aynı vuruşta başlar; **Siyah Ana Knob** ile BPM'i değiştirdiğinde 5 cihazın tamamı tek vücut halinde hızlanıp yavaşlar!

---

## Faz 12 — `Pad Bank B`: Dawless Riser & Drop Performans Deck Testi

- [ ] **12.1 Boss RC-505mkII (`Ch 14`) 2-Assign Kurulumu *(İsteğe Bağlı)*:**
  - `Assign 1`: `Source = #CC 80` (`Mode = MOMENT`) → `Target = INPUT FX ON/OFF` *(Input FX = Filter HPF veya Reverb)*
  - `Assign 2`: `Source = #CC 81` (`Mode = MOMENT`) → `Target = INPUT FX CONTROL`
- [ ] **12.2 Orijinal Değer Belirleme & `Pad Bank B`'ye Geçiş:**
  - `OTF 64s` çalarken `Shift + Knob` ile `SH-4d` Cutoff (`CC74`) değerini örn. **`45`** civarına kıs (bu artık senin **Orijinal Değerin** oldu).
  - **`Shift + Pad 3`** ile **`Pad Bank B`**'ye geç: 8 Pad'in farklı performans renklerinde (Camgöbeği, Kehribar, Mor, Macenta, Kırmızı, Yeşil, Altın, Ateş Turuncusu) yandığını ve sequencer'ın arka planda çalmaya devam ettiğini doğrula.
- [ ] **12.3 `Modulation Şeridi` + `Pad 8` (`THE DROP!`) Testi:**
  - Parmağını **Modulation Şeridi** üzerinde yukarı kaydır (`0% → 100%`): OLED'de `Manual Riser` / **`Tension: XX%`** yazmalı, `SH-4d` filtresi (`45 → 127`) + Reverb'ü ve `RC-505` Input FX'i açılmalı.
  - Gerilim tepedeyken **`Pad 8`**'e vur: OLED'de **`>>> DROP! <<<`** yazmalı, `Pad 8` beyaz patlamalı, `SH-4d` filtresi anında **`45`** orijinal değerine dönmeli, `RC-505` Input FX kapanmalı, `OTF 64s` `Step 1`'e oturmalı ve `Donner D1` üzerinde **Crash (`49`) + Impact (`SMP2 = 62`)** patlamalı!
- [ ] **12.4 `Pad 1` — Hızlanan Drum Roll (`D1` Ch 10):** **`Pad 1`'i 2 mezür basılı tut**: OLED `Drum Roll (D1)` / **`1/8 -> 1/64`** göstermeli, `D1` Snare (`38`) + Clap (`39`) vuruşları otomatik hızlanıp güçlenmeli *(basılı tutarken Mod Şeridini ittiğinde anında `1/64` buzz'a geçtiğini de dene)*.
- [ ] **12.5 `Pad 2` — 4-Bar / 8-Bar Eller Serbest Auto-Riser:** **`Pad 2`**'ye tek tıkla:
  - OLED'de her vuruşta **`DROP IN: 4.4 → 4.3 → ... → 1.1`** geri sayımını ve `Pad 2`'nin altın nabız atışını izle; 4. mezürde otomatik `D1` Snare Roll girmeli ve `1.1` bittiği anda elini sürmeden **otomatik DROP** gerçekleşmeli! *(`Hold + Pad 2` ile `8.4` sekiz mezür başlangıcını ve tekrar `Pad 2`'ye basarak `Cancelled` iptalini de doğrula)*.
- [ ] **12.6 `Pad 3` — Synth Pitch Rise & Tape-Stop Dive:**
  - **`Pad 3` basılı tut:** Aktif synth kanalında perde ve modülasyon yukarı tırmanmalı (`Pitch Rise UP`), bırakınca anında akorda (`0`) dönmeli.
  - **`Hold + Pad 3` basılı tut:** Plak freni gibi hızla aşağı çakılmalı (`Pitch DIVE`), bırakınca anında düzelmeli.
- [ ] **12.7 `Pad 4` (`Vacuum Mute`) & `Pad 7` (`D1 Uplifter`):**
  - **`Pad 4` basılı tut:** `OTF 64s` ve uzayan akorlar anında bıçak gibi susmalı (`VACUUM MUTE`), bırakınca groove geri girmeli (`GROOVE ON`).
  - **`Pad 7` tıkla** *(ve `Hold + Pad 7`)*: `Donner D1` üzerinde **`SMP1 (Note 60)`** ve **`SMP3 (Note 64)`** FX sample'larının tetiklendiğini doğrula.
