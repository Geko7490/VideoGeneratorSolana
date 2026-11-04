# Mimari ve destek sınırları

## Veri ve yürütme

Python 3.12 üzerinde PySide6/QML arayüzü `Bridge` üzerinden servisleri çağırır. Scheduler işleri tek arka plan worker'ında bağımlılık sırasıyla çalıştırır. Worker UI nesnelerini doğrudan değiştirmez; sonuç ve ilerleme Qt signal'larıyla ana iş parçacığına taşınır.

`StoryPlan` yerel LLM için küçük, zorunlu alanlı bir sözleşmedir. `compile_plan`, bu veriyi daha geniş `Project/Scene/Node` DSL'ine çevirir. Hikâye yalnızca 127.0.0.1 üzerinde uygulamanın başlattığı llama-server'a gönderilir. Proxy kullanılmaz. GGUF yükleme ve inference tamamlandıktan sonra süreç kapatılır; render sırasında LLM GPU belleği tutulmaz. GPU yükleme süreci başarısızsa bir kez CPU ile tekrar başlatılır.

Bilinen robot/tower/city kavramları için plan sözleşmesi ve içerik kontrolü temel nesnelerin atlanmasını önler. Model tüm nesneleri aynı x noktasına veya kadraj dışına koyarsa derleyici güvenli prosedürel yerleşim uygular; bu karar `planning_warnings` alanına yazılır ve UI'da gösterilir. Robot görünümü ilk sahneye göre korunur; yinelenen narration ayrıca uyarılır. Derleyici küçük kamera pan'ı ekler. Bu kurtarma katmanı modelin hatasını gizlemez; ileri sahne kalitesi manuel düzenleme veya daha güçlü model gerektirebilir.

Renderer yalnızca izinli nesneleri uygular. JSON içinde Python, shell, dosya yolu veya Blender script'i üretme arayüzü yoktur. Şema bilinmeyen alanları, döngüleri, kırık parent referanslarını, NaN/Infinity ve süre sınırı ihlallerini reddeder. `docs/scene.schema.json` kalıcı proje sözleşmesi, `docs/story-plan.schema.json` LLM planlama sözleşmesidir.

## Dosyalar

Varsayılan kullanıcı verisi `%LOCALAPPDATA%/VEXVideo` altındadır. `--data-dir` ile değiştirilebilir. SQLite son projeleri ve görev geçmişini tutar; proje JSON manifestleri gerçek sahne kaynağıdır. Manifestler geçici dosya + flush/fsync + atomik replace ile yazılır. Loglar/model dosyaları Git'e alınmaz.

Her projenin `audio`, `assets`, `cache`, `scenes`, `subtitles`, `exports` klasörü vardır. Ortak sürümlü asset kütüphanesi veri kökünün `assets` klasöründedir. Asset sürümleri içerik hash'i ile saklanır; instantiate nesne kimliklerini namespace ile ayırır.

## 2D ve motion

QPainter vektör geometriyi 1280x720 tasarım koordinatlarından hedef çözünürlüğe ölçekler. Dikey/kare çıktıda oranı koruyan letterbox uygulanır; otomatik yeniden kadrajlama henüz yoktur. Preview 360p, final seçilen 480/720/1080/1440/2160p profilidir; 24/30/60 FPS desteklenir.

Parent-child transform, katman, opaklık, kamera pan/zoom, rectangle, ellipse, line, polygon, cubic Bezier path, gradient, dikdörtgen clip mask, typewriter/reveal text, deterministik particles, robot/building/tower primitives uygulanmıştır. Animasyonlar timestamp üzerinden değerlendirilir. İlk motion motoru gelişmiş shape morphing, motion blur, glow veya görsel timeline editörü içermez.

## 3D

Blender ayrı portable runtime'dır. Yalnızca uygulamanın sabit `blender_runtime.py` yorumlayıcısı çalıştırılır; LLM script çalıştırılmaz. Desteklenen primitive'ler mesh/material/ışık/kamera ve transform animasyonlarına dönüşür. EEVEE ile gerçek PNG kareleri disk üzerinde oluşturulur, FFmpeg ile encode edilir. RAM'de bütün video tutulmaz.

İlk 3D motoru 2D tasarım koordinatlarını 3D dünyaya taşır. Tam 3D editör, skin/rig animasyonu, gelişmiş procedural mesh DSL ve Cycles CPU/GPU seçimi henüz yoktur. EEVEE için çalışan grafik altyapısı gerekir; CPU render fallback uygulanmış değildir. Particles, Bezier path, gradient, clip, text effects ve kısmi opacity 3D için açık hata verir. 3D tek kare paneli yerine gerçek 360p video önizlemesi kullanılır.

## Ses, altyazı ve export

Kokoro ONNX yalnızca İngilizce `af_/am_/bf_/bm_` sesleriyle WAV üretir. Metin/ses/model kimliği cache anahtarındadır. Ses sahneden uzunsa süre genişletilir; animasyon son pozda kalır. Aralara gerçek sessizlik eklenerek mono PCM16 narration timeline oluşturulur.

Whisper yerel model klasöründen, CPU/int8 ile İngilizce kelime zamanları üretir. Kaynak narration başlangıç referansıdır; transkripsiyonla sözcük benzerliği karşılaştırılır. %80 altı uyumda export durdurulur. Bu kontrol forced alignment değildir; eksik kelimeler için zaman uydurulmaz. Word JSON, SRT ve ASS yazılır. MP4 seçilebilir İngilizce altyazı içerir; `export.burn_subtitles=true` ile ayrıca görüntüye gömülebilir. Karaoke ve altyazı stil editörü henüz yoktur.

FFmpeg raw RGBA karelerini pipe üzerinden H.264'e encode eder. Sahne cache anahtarı sahne JSON, çözünürlük, FPS ve renderer sürümünü kapsar; yeniden kullanım SHA256 ile doğrulanır. Final dosya decode kontrolünden sonra atomik olarak yerini alır. İptal önceki finali ve tamamlanan sahne cache'lerini korur. Aynı render tekrar başlatıldığında tamamlanmış sahneler tekrar çizilmez.

İlk sürüm narration içerir. `mix_audio` servisinde yerel müzik için ducking ve normalization vardır; arayüzde çok kanallı müzik/SFX editörü henüz yoktur. İptal Kokoro/Whisper'ın devam eden tek inference çağrısını anında kesmez; çağrı bitince kontrol edilir. FFmpeg, llama.cpp ve Blender alt süreçleri iptalde sonlandırılır.

## Görevler ve doğruluk

PENDING, RUNNING, COMPLETED, FAILED, CANCELLED ve başlangıçta kesilmiş işlere INTERRUPTED kaydedilir. Frame/dosya/sahne sayımı ilerleme kaynağıdır; yükleme/token yüzdesi bilinmiyorsa yüzde ilerletilmez. ETA üretilmez. Pause ve bütün pipeline'ı süreç yeniden başlatma sonrasında görev düzeyinde devam ettirme henüz yoktur; proje ve sahne cache'i üzerinden tekrar başlatma vardır.

## Dağıtım

PyInstaller onedir paket, Python ve Qt runtime'ını içerir. GGUF, Kokoro/Whisper model ağırlıkları ve Blender ayrı tutulur. FFmpeg, imageio-ffmpeg Windows wheel'inden gelir. Installer için Inno Setup tanımı vardır; mevcut oturumda compiler kurulumu otomatik onay denetimiyle engellendiği için installer build yapılmadı. GitHub Actions workflow yerelde hazırlanmıştır; uzak depoda henüz çalıştırılmadı.
