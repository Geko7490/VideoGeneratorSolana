# Proje durumu ve ilerleme günlüğü

Son güncelleme: 2026-11-05 · Europe/Istanbul

## Güncel durum

B7 kabulü tamamlandı: son EXE gerçek yerel LLM → Kokoro → Whisper → MP4 zincirini 31.94 saniyede bitirdi; çıkış kodu 0, metin uyumu %98.68, MP4 decode başarılı. Kanıt: frozen-acceptance.json. Önceki timeout doğrudan loopback HTTPConnection ile giderildi.

VEX 0.1, sıfırdan oluşturulmuş çalışan Windows masaüstü geliştirme sürümüdür. PySide6/QML, JSON+SQLite kayıt, scheduler, yerel llama.cpp, prosedürel 2D/motion ve Blender 3D, İngilizce Kokoro/Whisper ve FFmpeg export uygulanmıştır. Tam şartnamenin tüm gelişmiş özellikleri bitmedi.

- Repo: https://github.com/Geko7490/VideoGeneratorSolana
- Başlangıçta origin boştu; bu oturumdaki kaynaklar yerelde oluşturuldu. İlk kaynak aktarımı hazırlanıyor; release yok.
- 26 otomatik test geçiyor; ruff ve compileall başarılı.
- Gerçek CPU ve Vulkan GGUF inference, WAV, İngilizce kelime hizalama, 720p H.264/AAC/altyazı MP4 ve Blender 3D çıktısı doğrulandı.
- PyInstaller onedir build, EXE UI ekran görüntüsü ve paket içinden gerçek sesli MP4 export kontrolü başarılı.
- Varsayılan Qwen2.5 1.5B ile farklı narration içeren üç sahnelik 13.125 saniye 720p video üretildi; Whisper metin uyumu %100. Görsel kalite temel primitive düzeyindedir; kadraj recovery'si UI ve JSON'da uyarılır.
- Installer compiler kurulumu otomatik onay denetimiyle engellendi. Installer derlenmedi; tanımı ve CI adımı hazır.
- Ayrıntılı kanıt: TEST_RESULTS.md. Mimari ve gerçek destek sınırları: ARCHITECTURE.md.

## Tamamlanan küçük aşamalar

| Aşama | Gerçek sonuç |
| --- | --- |
| A1–A4: inceleme ve yerel repo | Boş uzak repo doğrulandı, klonlandı, şartname korundu, AGENTS ve görev planı kaydedildi. |
| B1: temel | Python 3.12 sanal ortam, paket metadata, QML UI, proje kaydı, scheduler durumları, iptal ve CI tanımı. |
| B2: 2D ilk video | Güvenli scene graph, animasyon, kamera, primitives, frame streaming, cache, gerçek MP4 ve 15 test. |
| B3: yerel AI/ses | GGUF inference, küçük plan şeması/derleyici, gerçek Kokoro WAV, Whisper/SRT/ASS; PyAV uyumsuzluğu giderildi. |
| B4: uçtan uca ve GPU | CPU ve RX 6700M Vulkan ile LLM→ses→altyazı→MP4; ilk gerçek 720p video; düşük model kalitesi ayrıca kaydedildi. |
| B5: 3D/asset/motion | Blender 4.5.3 headless video; sürümlü asset registry; path/gradient/clip/text/particles; toplam 24 test. |
| B6: Windows paket | ICU DLL çakışması düzeltildi; onedir build, EXE QML smoke ve paket içinden gerçek Kokoro/Whisper export başarılı. |
| B7: teslimat ve kalite | 1.5B kabul videosu, tam EXE kabul testi, kullanıcı belgeleri ve teslimat arşivleri tamamlandı. |

## Sonraki görevler ve kabul ölçütleri

Her satır ayrı bir çalışma birimidir. Başlamadan kapsamı kaydet; kodu ve gerçek kontrol sonucunu yazmadan tamamlandı sayma.

| ID | Durum | Küçük görev / kabul ölçütü |
| --- | --- | --- |
| Q1 | Tamamlandı | 1.5B ile farklı narration, görünür robot/bina/kule ve hareket doğrulandı; kadraj recovery testi ve görünür uyarılar eklendi. |
| Q2 | Bekliyor | İçerik doğrulamasını genişlet; farklı sahne narration'ı ve karakter kimliklerini koruyan testler ekle. |
| UI1 | Bekliyor | Runtime/model seçimlerini JSON formundan dosya seçicili Model Manager'a taşı; quantization/context ayarı ve silme işlemini gerçek servislere bağla. |
| UI2 | Bekliyor | Görsel Scene Director ve zaman çizelgesi; değişiklik kaydı ve gerçek frame önizlemesi. |
| A1 | Bekliyor | Ses/stil seçimi ve önizleme UI'ı; Kokoro iptalinin ayrı süreçten anında yapılması. |
| A2 | Bekliyor | Referans metne gerçek forced alignment, karaoke ve altyazı stil/konum editörü; zor seslerde kelime doğrulaması. |
| A3 | Bekliyor | Çok kanallı müzik/diyalog/SFX UI'ı, yerel ses içe aktarma; miks servisi var fakat bu UI yok. |
| M1 | Bekliyor | Shape morphing, graph/counter, glow/motion blur ve geçişlerin gerçek video testleri. |
| D1 | Bekliyor | Tam 3D koordinat/mesh DSL, procedural rig/skin ve karakter yürüme animasyonu. |
| D2 | Bekliyor | Cycles CPU/GPU seçim ve CPU fallback; runtime olmayan cihazda açıklayıcı akış ve gerçek CPU testi. |
| J1 | Bekliyor | Gerçek pause; pipeline checkpoint'lerinden süreç yeniden açıldıktan sonra görev düzeyinde resume. Sahne cache'inden yeniden başlatma şu an çalışıyor. |
| P1 | Bekliyor | Dikey/kare otomatik kadrajlama; tüm çözünürlük/FPS profilleri ve uzun işlerde bellek ölçümü. |
| R1 | Engelli | Inno Setup compiler erişimi sağlanırsa installer derle ve kur/kaldır testlerini yap. Otomatik onay kurulumu reddetti. |
| R2 | Bekliyor | Windows 10 ve Python bulunmayan temiz Windows makinede UI/LLM/ses/render/EXE kabulü. |
| R3 | Bekliyor | Üçüncü taraf lisans/source dağıtım denetimi, release imzası ve gerçek GitHub Actions artifact doğrulaması. Workflow henüz uzak depoda çalışmadı. |

## Oturum günlüğü

### 2026-11-04 — başlangıç

Uzak referanslar ve yerel klasör denetlendi. Repo boştu; önceki kod veya tamamlanmış özellik yoktu. Şartname SHA256 eşleşmesi ve belge bağlantıları doğrulandı. Kullanıcı ardından sıfırdan geliştirmeyi istedi.

### 2026-11-04 — temel ve ilk kontroller

Temel paketler kuruldu. Gerçek UI, kayıt/scheduler ve 2D pipeline yazıldı. İlk 15 test başarılı oldu. QML font ve alan yenileme sorunları düzeltildi. Gereksiz model/cache/build dosyaları bağlama ve Git'e alınmadı.

### 2026-11-04 — AI ve ses

Yerel llama.cpp b12110 indirildi, mevcut Qwen2.5 0.5B GGUF kopyasıyla CPU ve Vulkan test edildi. Kokoro model/voices ve Whisper tiny.en indirildi. PyAV 19 uyumsuzluğu 16.1.0 ile giderildi. Whisper kaynak metin uyumu gerçek örneklerde yaklaşık %94–98 aralığında oldu. Şema hataları sınırlı düzeltme denemelerinden sonra açık hata olarak döndü; sahte plan veya ses kullanılmadı.

### 2026-11-04 — 3D ve paket

Blender 4.5.3 ile 5 karelik gerçek 3D video encode/decode edildi. Kaynak ve QML testleri 24'e ulaştı. PATH'teki Poppler ICU DLL'i paket çakışmasına yol açtı; temiz PATH ile EXE doğrulandı. Paket EXE'si gerçek sesli MP4 üretti (671278 byte). Inno Setup kurulumu otomatik onay denetimiyle reddedildi; installer tamamlandı denmedi.

### 2026-11-04 — kalite

Asıl robot hikâyesi 36 saniye 1280x720/24 FPS H.264+AAC+İngilizce altyazı olarak üretildi; decode başarılı, metin uyumu %94.3. 0.5B planının yinelenen narration, siyah nesne renkleri ve çevre hareketi sorunları gözlendi. Daha güçlü 1.5B GGUF indirildi; gerçek kalite denemesi devam ediyor. Sonuç ve teslimat dosyaları tamamlanınca buraya kaydedilecek.

### 2026-11-04 — 1.5B kalite sonucu

Gerçek Qwen2.5 1.5B Vulkan inference, farklı İngilizce narration içeren üç sahne üretti. Kadraj dışı/üst üste yerleşime görünür recovery uyarıları ve regresyon testi eklendi. Son video 13.125 sn, 1280x720, 24 FPS, H.264/AAC/İngilizce altyazı; Whisper metin uyumu %100. Kaynak sahne örneği `examples/robot-generated.json`, makinece okunabilir kanıt `docs/acceptance-report.json`. Kullanıcıya sunulan video `outputs/VEX-robot-demo.mp4`. Bu bir prodüksiyon kalitesinde animasyon iddiası değildir; gerçek temel geometri ve yerel inference akışını doğrular.

### 2026-11-05 — son EXE ve arşiv kontrolü

Son EXE tam LLM zinciri ilk denemede timeout verdi. Proxy/TLS handler hazırlığı olmayan doğrudan HTTPConnection eklendi; loopback/proxy/503 regresyon testi ile toplam 26 test geçti. Yeniden derlenen EXE gerçek 1.5B Vulkan, Kokoro ve Whisper kullanarak 31.94 saniyede 492678 byte MP4 üretti; decode başarılı, metin uyumu %98.68. Orphan test alt süreci sahipliği doğrulanıp sonlandırıldı; yeniden kullanılabilir verify_frozen.py eklendi.

Teslimat: outputs/VEXVideo-Windows-x64.zip (model/Blender ağırlıkları hariç tam onedir), outputs/VEXVideo-source.zip (sanal ortam/model/cache/build hariç kaynak), outputs/VEX-robot-demo.mp4 ve .srt; bu makine için outputs/Start-VEX.cmd. Arşiv CRC ve içerik kontrolleri teslimat aşamasında çalıştırılır. Installer hâlâ derlenmedi; R1 engeli değişmedi. Sonraki geliştirme Q2 ve UI1'dir.
