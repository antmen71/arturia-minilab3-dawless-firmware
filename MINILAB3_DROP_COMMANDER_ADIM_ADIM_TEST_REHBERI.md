# Arturia MiniLab 3 — `FW3: Dawless Kick, Riser & Drop Commander` Adım Adım Test Rehberi

**Test Edilen Firmware:** [minilab-3_Firmware_Update_1.2.0_Dawless_Drop_Commander.mnl3](file:///c:/Users/orkun/.gemini/antigravity/scratch/dawless_project/minilab3_otf/minilab-3_Firmware_Update_1.2.0_Dawless_Drop_Commander.mnl3)  
**Referans Kılavuz:** [MINILAB3_DROP_COMMANDER_KILAVUZU.md](file:///c:/Users/orkun/.gemini/antigravity/scratch/dawless_project/minilab3_otf/MINILAB3_DROP_COMMANDER_KILAVUZU.md)  
**Test Kurulumu:** `MiniLab 3 (5-Pin MIDI Out)` → `Roland SH-4d (Ch 1–5)` → `Donner B1 (Ch 6)` → `Boss RC-505mkII (Ch 14)` → `Donner D1 (Ch 10)`

> [!TIP]
> Firmware yüklemesi biter bitmez **Arturia MIDI Control Center (MCC)** programını kapat. MCC açık kaldığında MiniLab 3'ü bakım/editör kipinde tutabildiği için kapattığın anda tüm özel ekran ve performans özellikleri tam hızda devreye girer.

---

## Faz 0 — Firmware Yükleme & Ön Hazırlık (`2 Dakika`)

- [ ] **0.1 Firmware Yükleme:**
  1. *(Zaten MCC önbelleğine kopyalandı; tekrar seçmek istersen terminalde `python minilab3_otf\switch_mcc_firmware.py drop` çalıştırabilirsin).*
  2. **MIDI Control Center** uygulamasını aç → **`Firmware Revision -> Upgrade`** butonuna bas ve yüklemenin tamamlanmasını bekle.
  3. Yükleme bitince **MIDI Control Center uygulamasını tamamen kapat**.
- [ ] **0.2 MIDI Zinciri Kontrolü:**
  - `MiniLab 3 MIDI Out` → `Roland SH-4d MIDI In` (`Rhythm Ch = 5`, `MIDI THRU = ON`)
  - `SH-4d Out/Thru` → `Donner B1` (`Ch = 6`, `Din To Din = ON`, `RT = BOTH`) → `Boss RC-505mkII` (`RX CTL CH = 14`, `THRU = MIDI OUT`) → `Donner D1` (`Ch = 10`, `CLK SRC = DIN`, `BD` ve `SD` ses sürgüleri %100 açık).
- [ ] **0.3 `Boss RC-505mkII` 3 Assign Kontrolü (Opsiyonel ama Tam Deneyim İçin Önerilir):**
  - `Assign 1`: `#CC 80` (`MOMENT`) → `INPUT FX A ON/OFF` *(örn. Reverb veya HPF Filter)*
  - `Assign 2`: `#CC 81` → `INPUT FX A CONTROL`
  - `Assign 3`: `#CC 82` (`MOMENT`) → `INPUT FX B ON/OFF` *(`ISOLATOR` `LOW = -INF`, `INST 1 + INST 2` yönlendirilmiş)*

---

## Faz 1 — 2-Satırlı OLED Bilgi Ekranı, Preset İsimleri & Master Transport

- [ ] **1.1 Preset Seçimi Kontrolü (`Shift + Pad 3`):** **`Shift + Pad 3 (Prog)`** basılı tutarken **Siyah Ana Knob**'u yavaşça çevir *(Dikkat: `Shift + Pad 2` `Pad Bank A/B` değiştirir; `Pad Bank A`'da kaldığından emin ol)*.
  - **Beklenen OLED:** `Arturia`, `DAW`, **`Default`** *(MCC hafızasından gelen 1. kullanıcı slotu)*, **`SH-4d`**, **`RC-505`**, **`uKORG`**, **`K2000R`** isimlerini göreceksin. **`Default`** (veya `SH-4d`) üzerinde bırak *(`DAW` modunda bırakma; `DAW` modu bilgisayar/DAW için ayrılmıştır)*.
- [ ] **1.2 Açılış Pad LED Renkleri (`Pad Bank A`):**
  - **`Pad 1`:** Turkuaz *(Snare Roll hazır)*
  - **`Pad 2`:** Kraliyet Mavisi *(Dual Kick motoru aktif)*
  - **`Pad 3`:** Sıcak Kehribar *(Auto-Riser hazır)*
  - **`Pad 4`:** Koyu Macenta *(Vacuum Gate hazır)*
  - **`Pad 5`:** Kırmızı *(Master STOP)*
  - **`Pad 6`:** Yeşil *(Master START)*
  - **`Pad 7`:** Altın Sarısı *(D1 Uplifter FX)*
  - **`Pad 8`:** Ateş Turuncusu *(THE DROP!)*
- [ ] **1.3 Master START & Saf `4/4` Kick Kontrolü (`Pad 6`):** **`Pad 6`** tuşuna bir kez dokun *(veya her zaman saf 4/4'e sıfırlayıp başlatmak için `Hold + Pad 6`)*.
  - **Beklenen OLED:** Üst bantta `Master Transport`, alt satırda büyük kalın **`START + KICKS`** yazmalı!
  - **Beklenen Ses & LED:** `Pad 6` **Parlak Zümrüt Yeşili** yanar; `Fader 1` hangi konumda durursa dursun başlangıç koruması sayesinde **saf `1: 4/4 Classic` (`Düm - Düm - Düm - Düm`)** çalar ve her Kick vuruşunda **`Pad 2` Beyaz çakar**. *(Not: `SH-4d` veya `Donner D1`'in kendi içinde aksak bir kick pattern'i çalıyorsa üst üste binmemesi için cihazlardaki BD kanalını kapatabilir veya `Fader 1`'i en üste iterek `8: ExtKick OFF` seçebilirsin).*
- [ ] **1.4 Canlı Master BPM (`Siyah Ana Knob Çevirme`):** Siyah Ana Knob'u sağa ve sola çevir.
  - **Beklenen OLED & Ses:** Grafiksel `Rate` ekranında BPM **`30 – 270`** arasında değişir; Kick ve tüm bağlı cihazlar anında hızlanıp yavaşlar. **`124 BPM`** civarına getir.
- [ ] **1.5 Beat-1 Hizalama (`Siyah Ana Knob Tek Tık`):** Ritim akarken Siyah Ana Knob'a bir kez bas-bırak yap.
  - **Beklenen OLED:** `Beat-1 Re-Sync` / **`-> Step 1`**. Sayaç kesintisiz 1. vuruşa oturur.
- [ ] **1.6 Çift Kademeli Master STOP (`Pad 5`):**
  1. **`Pad 5`**'e 1. kez dokun → OLED: `Master Transport` / **`STOP (Clk ON)`** *(Kick susar, cihazlar durur, saat sıcak kalır)*.
  2. **`Pad 5`**'e 2. kez dokun → OLED: `Master Transport` / **`STOP (Free)`** *(`0xF8` saati de kesilir)*.

---

## Faz 2 — `Pad 1` Tap-Toggle Snare Roll & `Knob 1` Division (`1/1 → 1/32`) Testi

- [ ] **2.1 Dururken (`Free` Modda) Tap-Toggle Snare Roll Testi:** Henüz `Pad 6 (START)` basılı değilken bile **`Pad 1`**'e bir kez dokun ve **parmağını çek**.
  - **Beklenen OLED:** `Snare Roll ON` / **`1/4 (Beat)`**.
  - **Beklenen Ses & LED:** Parmağını çekmiş olmana rağmen **hem `Donner D1 (Ch 10, Nota 37 = SD)` hem `Roland SH-4d (Ch 5, Nota 38 = SD1)`** üzerinde her vuruşta net ve güçlü **Snare** çalmaya devam etmeli; `Pad 1` **Parlak Cyan** yanıp her Snare vuruşunda **Beyaz Strobe** çakmalı!
- [ ] **2.2 `Knob 1` ile Canlı Hız Artırma / Azaltma (`1/1 → 1/32`):** Snare Roll çalmaya devam ederken **`Knob 1`**'i önce en sola, sonra kademeli olarak en sağa çevir:
  - [ ] En Sol: OLED `Snare Roll ON` / **`1/1 (Bar)`** → Mezürde 1 vuruş
  - [ ] Sola Yakın: OLED `Snare Roll ON` / **`1/2 (Half)`** → Mezürde 2 vuruş
  - [ ] Orta-Sol: OLED `Snare Roll ON` / **`1/4 (Beat)`** → Her beat'te 1 vuruş (4x)
  - [ ] Orta-Sağ: OLED `Snare Roll ON` / **`1/8 Roll`** → Sekizlik hızlanma (8x)
  - [ ] Sağa Yakın: OLED `Snare Roll ON` / **`1/16 Roll`** → Onaltılık taramalı roll (16x)
  - [ ] En Sağ: OLED `Snare Roll ON` / **`1/32 Buzz`** → Otuzikilik makineli buzz roll (32x)!
- [ ] **2.3 Tek Dokunuşla `1/1` Sıfırlama (`Hold + Pad 1`):** Snare Roll `1/32 Buzz`'dayken **`Hold` basılı tut + `Pad 1`**'e dokun.
  - **Beklenen OLED & Ses:** `Snare Roll Div` / **`1/1 (Bar)`** yazar ve hız anında `1/1`'e döner.
- [ ] **2.4 İkinci Dokunuşla Kapatma (`Tap OFF`):** **`Pad 1`**'e tekrar dokun.
  - **Beklenen OLED & Ses:** `Snare Roll` / **`OFF`** yazar, Snare anında susar ve `Pad 1` sakin Turkuaz rengine döner.
- [ ] **2.5 `Shift + Knob 1` Synth CC Koruma Testi:** **`Shift` basılı tutarken `Knob 1`**'i çevir.
  - **Beklenen OLED:** Snare Roll değişmez; bunun yerine `Knob 1`'in normal synth parametresi (ör. `Cutoff (CC74)` / **`68  (Ch 1)`**) ekranda görünür ve synth'e gider.

---

## Faz 3 — `Pad 2` Tek Tuşla İkili Kick Kill, 8 Kick Ritim Slotu & Hedef Seçimi

- [ ] **3.1 Ritmi Başlat:** **`Pad 6 (START)`** tuşuna bas (`START + KICKS`).
- [ ] **3.2 `Fader 1` ile 8 Hazır Kick Pattern Testi:** Ritim çalarken **`Fader 1`**'i en alttan en üste yavaşça kaydır.
  - **Beklenen OLED & Ses:** `Kick Pattern` başlığı altında sırasıyla `1: 4/4 Classic` → `2: 4/4 Punchy` → `3: 4/4 Pickup` → `4: 4/4 Double` → `5: Driving 4/4` → `6: 4/4 Roll` → `7: ElectroBrk` → `8: ExtKick OFF` *(MiniLab MIDI Kick kapalı)* seçeneklerine geçer. Test için tekrar en alta (**`1: 4/4 Classic`**) çek.
- [ ] **3.3 `Fader 2` ile Davul Hedef Yönlendirmesi (`Drum Routing`):**
  1. **`Fader 2` En Alt (`0–42`):** OLED `Drum Routing` / **`SH-4d + D1`** → Hem SH-4d hem D1 aynı anda vurur.
  2. **`Fader 2` Orta (`43–84`):** OLED `Drum Routing` / **`Donner D1 Only`** → Sadece Donner D1 vurur, SH-4d Kick/Snare susar.
  3. **`Fader 2` En Üst (`85–127`):** OLED `Drum Routing` / **`SH-4d Ch5 Only`** → Sadece SH-4d vurur, Donner D1 susar.
  4. Test sonunda **`Fader 2`'yi tekrar En Alta (`SH-4d + D1`)** çek.
- [ ] **3.4 `Pad 2` Tek Tuşla Birleşik İkili Kick Kill (`Method 1 + Method 2`):**
  1. **`Pad 2`**'ye **1. kez** dokun:
     - **Beklenen OLED:** `Dual Kick Kill` / **`MUTED (M1+M2)`**.
     - **Beklenen Ses & LED:** `Pad 2` beat ile senkron **Kırmızı** yanıp söner; hem `SH-4d` hem `Donner D1` üzerindeki Kick vuruşları anında kesilir **VE** `RC-505mkII` üzerinde `Input FX B` (`CC82 = 127`) aktifleşir!
  2. **`Pad 2`**'ye **2. kez** dokun:
     - **Beklenen OLED:** `Dual Kick Kill` / **`KICKS ACTIVE`**.
     - **Beklenen Ses & LED:** Kick'ler anında geri girer, `RC-505mkII` Low-Kill kapanır (`CC82 = 0`), `Pad 2` tekrar **Kraliyet Mavisi + Beyaz Kick Çakar** durumuna döner.
- [ ] **3.5 `Hold + Pad 2` Mod Seçimi:** **`Hold` basılı tutarak `Pad 2`**'ye 3 kez bas.
  - **Beklenen OLED:** `Kick Kill Mode` başlığı altında `M1 MIDI Kick` → `M2 RC505 Kill` → **`M1+M2 Merged`** döner. **`M1+M2 Merged`** modunda bırak.

---

## Faz 4 — Manuel Riser, "Orijinal Değer" Hafızası & `Pad 8 (THE DROP!)` Testi

- [ ] **4.1 Synth "Orijinal Değer" Ayarı:** SH-4d üzerinde bir synth sesi çalarken **`Knob 2` / `Fader 4`** (veya `Shift + Knob 1` ile `CC74 Cutoff`) çevirerek tatlı, kapalı/orta bir filtre tonu (ör. değer `45`) ayarla.
  - **Beklenen OLED:** `Cutoff (CC74)` / **`45  (Ch 1)`** *(MiniLab 3 bu `45` değerini senin "Orijinal Değerin" olarak hafızaya aldı!)*.
- [ ] **4.2 Canlı Build-Up Kurulumu:**
  1. **`Pad 6 (START)`** çalıyor olsun.
  2. **`Pad 2`**'ye dokunarak Kick'leri sustur (`MUTED (M1+M2)`).
  3. **`Pad 1`**'e dokunarak Snare Roll'u başlat (`Snare Roll ON`) ve **`Knob 1`** ile hızı yavaşça `1/4 → 1/8 → 1/16 → 1/32` artır!
  4. Aynı anda **`Fader 3`**'ü (veya sol taraftaki **`Modulation Strip`**'i) yukarı doğru it!
     - **Beklenen OLED & Ses:** `Manual Riser` / **`Tension: 0% -> 100%`** yazar; `SH-4d` Part 1–4 filtreleri (`CC74`) ve reverb'ü (`CC91`) ile `RC-505` `Input FX A` (`CC80/81`) göğe yükselir!
- [ ] **4.3 `Pad 8 (THE DROP!)` Patlama Anı:** Gerilim `%100` ve Snare Roll `1/32 Buzz` zirvesindeyken **`Pad 8`**'e sertçe vur! *(Not: Fader 3'ü aşağı çektiğinde veya çekmeden bastığında anında sıfırlar; bir sonraki riser için Fader 3'ü de aşağı indir).*
  - **Beklenen 5 Eşzamanlı Sonuç (`< 1 ms`):**
    - [ ] OLED'de `Riser & Drop` / **`>>> DROP! <<<`** yazar ve `Pad 8` **Parlak Beyaz** patlar!
    - [ ] **`Pad 1` Snare Roll otomatik olarak kapanır!**
    - [ ] **`Pad 2` Dual Kick Kill otomatik olarak açılır (`KICKS ACTIVE`)** ve tam 1. vuruşta Kick güm diye girer!
    - [ ] Tüm `SH-4d` filtre/reverb ve `RC-505` efekt değerleri az önce ayarladığın **orijinal değerine (`45`)** şak diye geri döner!
    - [ ] `Donner D1` üzerinde **Crash (`CR = Nota 43`)** ve `Roland SH-4d` üzerinde **Crash (`Nota 49`)** patlar!

---

## Faz 5 — Eller Serbest 4-Bar & 8-Bar Auto-Riser (`Pad 3`) Testi

- [ ] **5.1 4-Bar Auto-Riser (`Pad 3`):** Ritim çalarken hiçbir fader'a dokunmadan **`Pad 3`**'e bir kez dokun ve iki elini klavyeye bırak!
  - **Beklenen OLED Geri Sayımı:** `Auto-Riser 4B` başlığı altında her beat'te **`DROP IN: 4.4` → `4.3` → ... → `2.1` → `1.4` → `1.3` → `1.2` → `1.1`** geri sayar!
  - **Beklenen Otomatik Final Barı (`1.4 .. 1.1`):** Son mezüre girildiği anda (`1.4`) MiniLab 3 **otomatik olarak Kick'leri susturur**, otomatik hızlanan (`1/16 → 1/32 → 1/64`) Snare Roll ekler ve **`1.1` biter bitmez kendi kendine `>>> DROP! <<<` patlatıp Kick'leri geri sokar!**
- [ ] **5.2 8-Bar Auto-Riser & İptal Testi:** **`Hold + Pad 3`** tuşuna bas → OLED'de `Auto-Riser 8B` / **`DROP IN: 8.4`** başladığını gör; yarı yolda tekrar **`Pad 3`**'e dokun → OLED'de **`Cancelled`** yazar ve sesler yumuşakça orijinal değerine döner.

---

## Faz 6 — Vacuum Gate, Tape-Stop, D1 Uplifter & Synth Pitch Rise (`Pad 4 & Pad 7`)

- [ ] **6.1 Pre-Drop Vacuum Gate (`Pad 4` Basılı Tut):** Drop'tan hemen önceki son yarım mezürde **`Pad 4`**'ü basılı tut, sonra bırak.
  - **Beklenen Sonuç:** Basılı tutarken OLED `Pre-Drop Gate` / **`VACUUM MUTE`** yazar, Kick/Snare ve uzayan `SH-4d` + `Donner B1` notaları bıçak gibi susar; bırakınca **`GROOVE ON`** ile ritim kaldığı yerden devam eder.
- [ ] **6.2 Tape-Stop Pitch Dive (`Hold + Pad 4` Basılı Tut):** Klavyeden bir synth akoru/notası basılı tutarken **`Hold + Pad 4`**'ü basılı tut, sonra bırak.
  - **Beklenen Sonuç:** OLED `Tape-Stop FX` / **`Pitch DIVE`** yazar; synth sesi plak duruyormuş gibi aşağı doğru kayar (`-8172`) ve bırakınca anında orijinal akorduna (`0`) döner!
- [ ] **6.3 Donner D1 Uplifter (`Pad 7` Basılı Tut):** **`Pad 7`**'yi 2 saniye basılı tut, sonra bırak.
  - **Beklenen Sonuç:** OLED `D1 FX Trigger` / **`SMP1 Uplifter`** yazar; `Donner D1` `SMP1` (Pad 9 = `Nota 44`) kanalı çalar, bırakınca susar.
- [ ] **6.4 Synth Pitch Rise UP (`Hold + Pad 7` Basılı Tut):** Klavyeden bir nota çalarken **`Hold + Pad 7`**'yi basılı tut.
  - **Beklenen Sonuç:** OLED `Synth Riser` / **`Pitch Rise UP`** yazar; aktif synth kanalında hem perde yukarı tırmanır (`+8160`) hem vibrato/modülasyon (`CC1`) açılır; bırakınca merkeze döner.

---

## Faz 7 — `Pad Bank B`: 16-Adım Özel Kick Editörü & Kalıcı Flash Kayıt Testi

- [ ] **7.1 `Pad Bank B`'ye Geçiş (`Shift + Pad 2`):** **`Shift + Pad 2 (Pad)`** tuşlarına basarak `Pad Bank B`'ye geç.
  - **Beklenen Pad LED:** `1: 4/4 Classic` seçiliyse `Pad 1` ve `Pad 5` **Kehribar/Cyan** (Kick vuruşları), diğerleri sönük görünür ve çalarken **Yeşil Playhead** akar.
- [ ] **7.2 3-Kademeli Kick Adımı Yazma (`Off / Normal / Accent`):** **`Pad 4`** üzerine üst üste 3 kez dokun:
  1. 1. Dokunuş → OLED: `Kick Step 4` / **`ON (Normal)`** *(Pad 4 **Cyan** yanar, normal sertlikte Kick eklenir)*
  2. 2. Dokunuş → OLED: `Kick Step 4` / **`ON (Accent!)`** *(Pad 4 **Kehribar** yanar, maksimum vuruşlu Accent Kick olur)*
  3. 3. Dokunuş → OLED: `Kick Step 4` / **`OFF (Muted)`** *(Pad 4 söner, adım silinir)*. Test için `Pad 4`'ü **`ON (Normal)`** bırak.
- [ ] **7.3 Adım 9–16 Sayfası (`Hold + Pad 2`):** **`Hold` basılı tut** *(Pad 1 Altın, Pad 2 Mavi yanar)* ve **`Pad 2`**'ye dokun.
  - **Beklenen OLED:** `Kick Edit Page` / **`P2 (Steps 9-16)`**. Artık Pad 1–8 adımlar `9–16`'yı düzenler! Tekrar **`Hold + Pad 1`** ile `P1 (Steps 1-8)`'e dön.
- [ ] **7.4 Kalıcı STM32 Flash Kayıt & Kapat-Aç Testi:**
  1. **`Hold` + `Siyah Ana Knob` ikisini birden basılı tutarken `Pad 1`**'e dokun.
  2. **Beklenen OLED:** `Saved to Flash` / **`1: 4/4 Classic`**.
  3. MiniLab 3'ün USB kablosunu çıkarıp tekrar tak, **`Pad 6 (START)`**'a bas → Az önce `Step 4`'e eklediğin ekstra Kick vuruşunun silinmeden hafızadan geri geldiğini doğrula!
  4. **`Shift + Pad 2`** ile tekrar ana **`Pad Bank A`** performans ekranına dön.

---

## Hızlı Sorun Giderme

| Belirti | Çözüm |
| :--- | :--- |
| **OLED ekran yazıları çıkmıyor veya eski sürüm davranışı var** | MIDI Control Center'dan `Upgrade` yaptıktan sonra **MCC uygulamasını tamamen kapattığından** emin ol. |
| **SH-4d'den Kick/Snare geliyor ama Donner D1'den ses gelmiyor** | 1) **`Fader 2`**'nin en altta (**`SH-4d + D1`**) olduğunu kontrol et.<br>2) SH-4d `MIDI THRU: ON`, Donner B1 `Din To Din: ON` ve D1 üzerinde `BD` / `SD` fader'larının açık olduğundan emin ol. |
| **`Pad 8 (DROP!)` sonrası Riser tekrar yükselmeye devam ediyor** | Manuel Riser için **`Fader 3`** fiziksel olarak en üstte kaldıysa fader'a dokunduğunda yeni hareket algılar; Drop vurduktan sonra bir sonraki build-up için `Fader 3`'ü en alta (`0`) çek. |
| **`OTF 64s` (64-Adım Melodik Sequencer) moduna geri dönmek istiyorum** | Terminalde `python minilab3_otf\switch_mcc_firmware.py pro64` çalıştırıp MCC'den `Upgrade` yapman yeterli; iki modun kayıtlı Flash pattern'leri birbirinden tamamen bağımsızdır. |
