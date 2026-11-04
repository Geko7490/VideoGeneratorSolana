# Test sonuçları — 2026-11-04/05

## Ortam

Windows 11 x64, Python 3.12.14, AMD Radeon RX 6700M 10 GB. Kaynak sürümleri `requirements-windows.lock.txt` dosyasındadır. Windows 10 ve temiz başka bilgisayar kontrolü yapılmadı.

## Otomatik kontroller

`python -m pytest -q`: **26 passed** (son çalışma yaklaşık 4.5 saniye).

`python -m ruff check .`: başarılı. `compileall`: başarılı.

Kontroller gerçek çıktıları kapsar:

- JSON proje kaydı/açma, bozuk veri ve kaydın korunması.
- İzin listesi, bilinmeyen komut, parent döngüsü, kırık referans, NaN ve yol kaçışı reddi.
- Zaman tabanlı animasyon, parent transform, gerçek QImage piksel kontrolü.
- Typewriter, particles, gradient ve Bezier çizimi; aynı timestamp'te deterministik çıktı.
- Scheduler bağımlılık sırası, başarı/hata/iptal durumları ve kesilmiş iş kurtarma.
- Gerçek H.264 MP4 üretimi, decode ve frame sayısı.
- SHA256 sahne cache'i, değişmeyen sahnelerin korunması ve bozuk cache'in onarılması.
- İptal sırasında önceki finalin ve biten cache'in korunması; render'ı tekrar başlatma.
- AAC ve seçilebilir İngilizce altyazı mux; burn-in ve Türkçe/boşluk/tırnak içeren yollar.
- Yerel müzik + narration ducking/normalization; gerçek FFmpeg miks çıktısının süresi.
- Asset sürümlerinin değişmezliği ve namespace'li referanslar.
- QML penceresinin gerçek yüklenmesi ve örnek/yeni/aç eylemlerinin görünür alanları yenilemesi.
- İndirme byte ilerlemesi, iptal sonrası kısmi dosya temizliği ve zip path traversal reddi.

## Gerçek model ve runtime kabul kontrolleri

| Kontrol | Sonuç | Kanıt |
| --- | --- | --- |
| CPU yerel LLM | Başarılı | llama.cpp b12110 ve gerçek Qwen2.5 0.5B GGUF ile sahne JSON üretildi. |
| Vulkan yerel LLM | Başarılı | RX 6700M algılandı; inference Vulkan0 kullandı; bazı Flash Attention işlemleri CPU'ya atandı. |
| Kokoro İngilizce TTS | Başarılı | Gerçek model ve af_heart ile mono PCM16 WAV; sahne süresi sese göre uzatıldı. |
| Whisper İngilizce | Başarılı | Yerel tiny.en, CPU/int8; word timestamps, SRT/ASS ve kaynak metin karşılaştırması. |
| Tam hikâyeden 720p video | Başarılı, kalite sınırlı | a151bd15-cacd-42cd-ac15-b4bfdcab4ce8: 36 sn, 1280x720, 24 FPS, H.264 + AAC + English mov_text. Sözcük uyumu %94.3. |
| Blender 3D | Başarılı | Blender 4.5.3 EEVEE headless; 5 gerçek 640x360 kare encode/decode edildi; ekran karesi incelendi. |
| PyInstaller onedir | Başarılı | PATH'teki yabancı ICU DLL'i dışlanınca build tamamlandı. |
| Paket EXE QML smoke | Başarılı | Pencere açıldı, örnek yüklendi, ekran görüntüsü kaydedildi; çıkış kodu 0. |
| Paket EXE gerçek sesli export | Başarılı | Paketlenmiş Kokoro/Whisper ile MP4 üretildi; çıkış kodu 0, çıktı 671278 byte. |
| Daha büyük 1.5B model kalite kontrolü | Başarılı, ilk sürüm kalitesi | 1d4e634a-3e08-41c4-b001-ba1182b05694: farklı narration içeren 3 sahne, 13.125 sn, 1280x720/24 FPS, H.264/AAC/English mov_text, metin uyumu %100. Kadraj/çakışma recovery uyarıları kaydedildi; video karesi incelendi. |
| Installer | CI build başarılı | Yerel compiler kurulumu engellendi; izole GitHub Windows runner üzerinde Inno Setup ile derlendi. Kur/kaldır henüz test edilmedi. |
| GitHub Actions | Başarılı | Run 41917522197: bütün adımlar ve artifact upload geçti. |

## Bulunan ve düzeltilen sorunlar

1. Offscreen font veritabanı boş glyph çizdi; Windows Segoe UI/Consolas fontları açıkça yüklendi.
2. QML alan yenileme kontrolü bağlı property nedeniyle örnek başlığını güncellemedi; bağımsız son sürüm değeri ve gerçek UI testi eklendi.
3. llama.cpp'ye geniş proje şeması verilince 0.5B model narration alanını boş bıraktı; sade zorunlu StoryPlan ve doğrulanan derleyici ayrıldı.
4. Küçük model süre değerlerini yanlış üretti; süre seçenekleri enum'a dönüştürüldü.
5. Model hikâyedeki kuleyi atladı; bilinen temel nesneler için plan şeması ve içerik kontrolü eklendi. Başarısız plan video gibi gösterilmez.
6. faster-whisper + PyAV 19 `metadata_errors` uyumsuzluğu; test edilen PyAV 16.1.0 sınırlandı.
7. PyInstaller, PATH'teki Poppler ICU DLL'ini topladı; build PATH'i Windows sistem dizinleriyle sınırlandı.
8. 1.5B model nesneleri sağ kenarda üst üste yerleştirdi; güvenli prosedürel kadraj recovery'si, görünür uyarılar ve regresyon testi eklendi. Robot görünümü ilk sahneyle eşitlenir. Kaynak JSON'da uyarılar korunur.

## Kabul edilmeyen kalite ve kalan doğrulamalar

0.5B modelin tekrarlayan narration, koyu renk ve anlamsız çevre hareketleri üretmesi bilinen kalite sorunudur. Şema ve encode başarısı sanatsal/anlamsal doğruluğu kanıtlamaz. Görsel editörler, gelişmiş rig/motion, forced alignment, gerçek pause ve 3D CPU fallback kapsamı tamamlanmadı. Tüm 4K/FPS/aspect kombinasyonları uzun videolarla test edilmedi. İlk indirmeden sonra ağ bağlantısı kapalı ayrı bir sistem kabul testi henüz yapılmadı; inference kodu yalnızca yerel runtime/model dosyalarını kullanır.

## Son paket tam kabulü — 2026-11-05

`python scripts/verify_frozen.py` başarılı: son EXE, gerçek yerel 1.5B Vulkan LLM → Kokoro → Whisper → FFmpeg zincirini 31.94 saniyede tamamladı. Çıkış kodu 0; yeni MP4 492678 byte, decode kontrolü başarılı, kaynak metin uyumu %98.684. Makinece okunabilir kanıt: `frozen-acceptance.json`.

Bu kontrol sırasında bulunan loopback timeout'u, HTTPS/proxy handler hazırlığı gerektirmeyen doğrudan `HTTPConnection` ile giderildi. Yalnızca loopback portuna bağlanma, proxy'den bağımsız kalma ve model yüklenirken 503 cevabını işleme regresyon testi eklendi.

## GitHub Windows CI — 2026-11-05

İlk kaynak commit 14023a5cfc72fe694b7f368c67dee05a0392fdbf için workflow başarıyla tamamlandı. Artifact VEXVideo-Windows-x64, ID 13364934440; onedir ve installer içerir. Bu sonuç installer'ın kur/kaldır işleminin veya Windows 10'un test edildiği anlamına gelmez.
