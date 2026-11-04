# VEX AI Video Generator · 0.1

Windows için yerel hikâye planlama ve prosedürel video üretim stüdyosu. Görüntü veya video üretim modeli kullanılmaz. Yerel llama.cpp sahne planlar; VEX kendi geometrisini çizer. Kokoro ve Whisper yalnızca İngilizce ses/altyazı üretir.

## Çalıştırma

Hazır paket `dist/VEXVideo/VEXVideo.exe` dosyasındadır. `dist/VEXVideo` klasörünü bütün olarak koruyun; EXE tek başına taşınmaz. Çıktılar klasöründeki `Start-VEX.cmd`, bu makine için hazırlanmış model yollarıyla uygulamayı başlatır.

Bağımsız çalıştırmada varsayılan veri dizini `%LOCALAPPDATA%/VEXVideo` olur. Ayarlar ekranında **Temel modelleri indir** ile ilk kurulum dosyalarını indirebilirsiniz (~1.6 GB; ilk indirmede internet gerekir). Varsayılan Qwen2.5 1.5B modeldir. Denenen 0.5B modelin anlatım/görsel plan kalitesi zayıf olduğundan varsayılan yapılmadı. Daha güçlü yerel GGUF seçilebilir. Blender ayrıca seçilir ve bu indirmeye dahil değildir.

Kaynak koddan kurulum (Python 3.11–3.13, test edilen sürüm 3.12):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev,audio]"
.\.venv\Scripts\python.exe -m vex
```

Test edilen Windows ortamını aynı sürümlerle kurmak için önce `requirements-windows.lock.txt`, ardından `pip install -e . --no-deps` kullanılabilir.

## İlk video

1. **Prosedürel robot örneğini aç** ile elle hazırlanmış şehir/robot sahnelerini açın. **360p video önizle** model gerektirmeden gerçek sessiz MP4 üretir. Bu örnek bir AI planı değildir.
2. Ayarlar'da `llama_server` ve `gguf` dosyalarını seçin veya temel modelleri indirin. `gpu_layers: 0` CPU; pozitif değer GPU offload talebidir. Vulkan runtime desteklenen cihazları kullanır; GPU yükleme başarısız olursa CPU tekrar denenir.
3. Hikâyeyi yazıp **Yerel LLM ile sahneleri planla** düğmesine basın. Scene Director'da doğrulanan JSON'u düzenleyebilirsiniz.
4. `kokoro_model`, `kokoro_voices` dosyalarını ve `whisper_model` yerel klasörünü ayarlayın. **Hikâyeden sesli MP4 üret**, planlama → ses → altyazı → final render işlemlerini tek görev zincirinde çalıştırır.
5. Var olan sahneleri seslendirmek için **Kokoro İngilizce ses + Whisper altyazı ekle** seçeneğini işaretleyip export başlatın. İşaretli değilse çıktı sessizdir. Ses modelleri eksikse işlem açık hata verir.
6. **Videoyu aç** ile sonucu açın. İptal sonrası aynı render tekrar başlatılırsa sağlam sahne cache'leri kullanılır.

Windows yollarında JSON içinde `/` veya `\\` kullanın. İngilizce ses varsayılanı `af_heart`. Model Manager ilk indirmeden sonra inference sırasında internet kullanmaz.

## Desteklenen işlemler

- Koyu QML masaüstü UI; proje oluştur/aç/kaydet; son projeler; gerçek görev geçmişi.
- İzin listeli JSON sahneleri, parent-child transform, katman ve zaman tabanlı keyframe animasyonu.
- Vektör 2D primitives, robot/şehir geometrisi; gradient, Bezier path, clip mask, typewriter/reveal ve particles.
- Immutable sürümlü asset kütüphanesi; aynı geometriyi yeni nesne kimlikleriyle tekrar kullanma.
- Blender headless primitive 3D, materyal, ışık, kamera ve transform animasyonu. Sahne `engine` alanı `3d` olmalıdır.
- Kokoro gerçek WAV cache'i; ses süresine göre sahne uzatma; Whisper kelime zamanları ve kaynak metin uyum kontrolü; SRT/ASS.
- H.264 MP4, isteğe bağlı AAC narration ve seçilebilir İngilizce altyazı. JSON'da `export.burn_subtitles: true` görüntüye gömmeyi açar.
- 480p–2160p, 24/30/60 FPS, 16:9 / 9:16 / 1:1; 360p preview final çözünürlükten ayrıdır. Dikey/kare profiller letterbox kullanır.
- SHA256 kontrollü sahne cache'i, sınırlı RAM kullanımı, gerçek frame/dosya ilerlemesi, iptal ve tekrar başlatma.

## Komut satırı

```powershell
.\.venv\Scripts\python.exe -m vex doctor --data-dir data
.\.venv\Scripts\python.exe -m vex sample --data-dir data
.\.venv\Scripts\python.exe -m vex render --data-dir data --project "data/projects/PROJE_ID/project.json" --preview
.\.venv\Scripts\python.exe -m vex generate --data-dir data --title "Robot Story" --story "A small robot explores an abandoned city." --preview --voice
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
./scripts/build.ps1
```

`render` var olan JSON'u çizer; `plan` gerçek yerel LLM ile JSON üretir; `generate` gerçek yerel LLM ile başlayıp video üretir. `--voice` eklenirse Kokoro/Whisper zorunludur. Komut satırı için Python girişi önerilir; paket EXE'si konsolsuz masaüstü uygulamasıdır.

## Durum ve sınırlar

Bu ilk çalışan geliştirme sürümüdür. Yerel CPU ve Vulkan LLM, Kokoro WAV, Whisper hizalama, 2D MP4, Blender 3D MP4 ve EXE açılışı bu makinede gerçek çıktılarla kontrol edildi. [Test raporu](docs/TEST_RESULTS.md) ayrıntıları içerir.

Şartnamenin gelişmiş tüm özellikleri tamamlanmış değildir: ayrıntılı 3D mesh/skin rig, Cycles CPU render fallback, görsel timeline/scene editörü, karaoke/stil editörü, çok kanallı ses/SFX arayüzü, gerçek pause ve süreç yeniden başlatma sonrası görev düzeyinde resume, otomatik kadrajlama, eksiksiz lisans dağıtım denetimi ve Windows 10 doğrulaması kalmıştır. Kokoro/Whisper aktif inference çağrısı iptal isteğine çağrı sonunda yanıt verir. Altyazı uyum kontrolü gerçek forced alignment yerine geçmez.

Installer tanımı `scripts/installer.iss` içindedir. Bu oturumda Inno Setup compiler kurulumu otomatik onay denetimiyle engellendi; installer henüz derlenmedi. GitHub Actions workflow hazırdır; uzak depoda çalıştırılmadı. GitHub'a push/release yapılmadı.

- [Çalışma kuralları](AGENTS.md)
- [Güncel durum ve küçük görev planı](docs/PROGRESS.md)
- [Mimari ve motor sınırları](docs/ARCHITECTURE.md)
- [Bağımlılıklar ve resmî kaynaklar](docs/DEPENDENCIES.md)
- [Tam şartname](docs/SPECIFICATION.md)
