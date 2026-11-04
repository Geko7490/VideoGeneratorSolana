# VEX AI VIDEO GENERATOR
## Windows Desktop — Full Development Specification

### 1. Görevin ve temel hedef

Sıfırdan **VEX AI Video Generator** isimli, Windows üzerinde çalışan, tamamen yerel yapay zekâ destekli, otomatik video üretim uygulaması geliştir.

Bu proje bir Image Generator veya hazır AI Video Generator arayüzü değildir.

**Temel çalışma prensibi:**

Kullanıcı hikâye veya video fikri girer. Yerel LLM hikâyeyi analiz eder, senaryoyu oluşturur, sahneleri planlar, karakterleri ve nesneleri tanımlar. Uygulamanın kendi prosedürel çizim motoru sahneleri 2D, 3D veya Motion Graphics olarak çizer, animasyonları oluşturur, Kokoro ile İngilizce seslendirme yapar, Whisper ile İngilizce altyazıları hizalar ve FFmpeg ile MP4 video üretir.

**Kesin kurallar:**

- Yalnızca yerel LLM kullanılacak.
- Hiçbir bulut LLM API'si kullanılmayacak.
- Image Generator kesinlikle bulunmayacak.
- Stable Diffusion, FLUX, SDXL, ComfyUI ve benzeri görüntü üretim sistemleri kullanılmayacak.
- AI Video Generator modelleri kullanılmayacak.
- Çizim motoru uygulamanın kendi prosedürel sisteminden oluşacak.
- 2D + 3D + Motion Graphics desteklenecek.
- Dinamik prosedürel çizim ve tekrar kullanılabilir nesne kütüphanesi birlikte çalışacak.
- Kokoro TTS yalnızca İngilizce olacak.
- Whisper yalnızca İngilizce konuşma ve altyazı için kullanılacak.
- Windows 10/11 x64 desteklenecek.
- Kullanıcıya indirilebilir, kurulabilir EXE sağlanacak.
- Temel video üretim akışı tamamen çevrimdışı çalışabilecek.
- Modellerin ilk indirilmesi için internet kullanılabilir.
- Sahte çalışan butonlar, mock üretim sonuçları veya yalnızca arayüzde var olan özellikler kabul edilmeyecek.

### 2. Teknoloji mimarisi

Önerilen teknoloji yığını:

**Desktop UI**
- Python 3.11+
- PySide6
- QML / Qt Quick
- MVVM benzeri ayrıştırılmış mimari
- Dark Theme
- Modern, akıcı masaüstü arayüzü

**Yerel AI**
- llama.cpp
- GGUF model desteği
- Vulkan GPU hızlandırma
- CPU fallback
- Model Manager
- JSON schema tabanlı structured output

**2D Drawing Engine**
- Skia veya Qt'nin uygun çizim altyapısı
- Vektör çizimi
- Bezier paths
- Parametrik geometri
- Katmanlar
- Transform sistemi
- Karakter rig sistemi

**3D Engine**
- Blender Python API
- Prosedürel mesh oluşturma
- Materyal ve ışık sistemi
- Kamera animasyonları
- Blender headless render
- CPU/GPU render seçimi

**Motion Graphics**
- Keyframe engine
- Easing curves
- Text animation
- Shape animation
- Particle systems
- Masking
- Camera movement
- Transition effects

**Voice**
- Kokoro ONNX
- İngilizce ses profilleri
- Yerel inference

**Subtitles**
- faster-whisper
- English transcription
- Word-level timestamps
- SRT/ASS export
- Forced alignment veya doğrulama katmanı

**Video Composer**
- FFmpeg
- H.264 MP4
- AAC audio
- Scene composition
- Subtitle burn-in
- Audio mixing

**Persistence**
- SQLite
- JSON proje manifestleri
- Asset cache
- Render cache

**Distribution**
- Nuitka veya PyInstaller
- Windows installer
- GitHub Actions
- Otomatik EXE artifact üretimi

Kütüphane seçerken lisans, dağıtım, Windows uyumluluğu, performans ve gerçek çalışabilirlik kriterlerini değerlendir. Gerektiğinde daha uygun teknolojiyi gerekçesiyle seç.

### 3. Proje mimarisi

Kodları modüler oluştur.

Önerilen dizin yapısı:

```text
VEX-AI-Video-Generator/
├── app/
│   ├── main.py
│   ├── ui/
│   │   ├── dashboard/
│   │   ├── story_studio/
│   │   ├── scene_director/
│   │   ├── asset_library/
│   │   ├── voice_studio/
│   │   ├── subtitle_studio/
│   │   ├── render_center/
│   │   └── settings/
│   ├── core/
│   │   ├── project_manager/
│   │   ├── job_scheduler/
│   │   ├── event_bus/
│   │   ├── cache_manager/
│   │   └── error_handler/
│   ├── ai/
│   │   ├── llama_runtime/
│   │   ├── story_director/
│   │   ├── scene_planner/
│   │   └── schema_validator/
│   ├── drawing/
│   │   ├── engine_2d/
│   │   ├── engine_3d/
│   │   ├── motion_engine/
│   │   ├── procedural_factory/
│   │   └── asset_registry/
│   ├── audio/
│   │   ├── kokoro/
│   │   ├── whisper/
│   │   ├── alignment/
│   │   └── mixer/
│   ├── rendering/
│   │   ├── compositor/
│   │   ├── ffmpeg/
│   │   └── export/
│   └── models/
├── assets/
├── tests/
├── scripts/
├── docs/
├── .github/workflows/
└── README.md
```

Bu yapı başlangıç önerisidir. Gerçek geliştirme sırasında daha iyi bir modüler yapı gerekiyorsa düzenle.

### 4. Yerel LLM sistemi

LLM, uygulamanın merkezi karar motorudur.

LLM doğrudan video frame'leri üretmeyecek. Bunun yerine sahne motorunun anlayabileceği yapılandırılmış komutlar oluşturacak.

**Model Manager özellikleri:**

- GGUF model dosyası seçme.
- Yerel diskten model yükleme.
- Model indirme ve indirme ilerlemesi.
- Model kaldırma.
- Model boyutu ve quantization gösterimi.
- CPU/GPU kullanım seçimi.
- Vulkan hızlandırma.
- Context length ayarı.
- GPU layer ayarı.
- RAM/VRAM durumunu gösterme.
- Model yükleme hatalarını açıklama.
- Çalışan modelin gerçek durumunu gösterme.

Model yükleme işlemi UI thread'ini engellememeli.

**Story Director görevleri:**

1. Hikâyeyi analiz et.
2. Karakterleri tanımla.
3. Ortamları ve nesneleri belirle.
4. Sahne sayısını hesapla.
5. Sahne sürelerini planla.
6. 2D/3D/Motion Graphics motorunu seç.
7. Kamera hareketlerini belirle.
8. Karakter hareketlerini planla.
9. İngilizce narration oluştur.
10. Ses efektlerini planla.
11. Sahne geçişlerini oluştur.
12. Sahne verilerini doğrulanabilir JSON formatına dönüştür.

LLM çıktısı JSON Schema veya Pydantic ile doğrulanmalı.

Geçersiz komutlarda:
- Önce sınırlı sayıda otomatik düzeltme dene.
- Desteklenmeyen özellikleri tespit et.
- Güvenli fallback kullan.
- Kullanıcıya anlaşılır hata göster.

**Güvenlik:**

LLM tarafından üretilen rastgele Python, shell, Blender script veya işletim sistemi komutlarını doğrudan çalıştırma.

LLM yalnızca izin verilen sahne DSL/JSON komutlarını üretsin. Renderer bu komutları güvenli, önceden tanımlanmış fonksiyonlarla uygulasın.

### 5. Procedural Drawing Engine

Bu projenin en önemli modülüdür.

Image Generator kullanılmayacağı için sahneler kod tabanlı çizim ve geometri algoritmalarıyla oluşturulacak.

**5.1. Dinamik çizim sistemi**

Desteklenecek temel öğeler:

- Line
- Circle
- Ellipse
- Rectangle
- Polygon
- Bezier Curve
- Path
- Gradient
- Material
- Texture pattern
- Mesh
- Transform
- Group
- Layer
- Camera
- Light
- Particle

Çizim komutları hiyerarşik bir scene graph üzerinde yönetilmeli.

Her nesnenin:
- Benzersiz kimliği
- Konumu
- Boyutu
- Rotasyonu
- Ölçeği
- Materyali
- Parent-child ilişkisi
- Animasyon özellikleri

bulunmalı.

**5.2. Procedural Asset Factory**

LLM, nesneleri sadece sabit şablonlardan seçmek zorunda kalmamalı.

Desteklenen geometri bileşenlerini kullanarak yeni nesneler tanımlayabilmeli.

Örnek:

LLM bir robot istediğinde:

- Gövde geometrisi
- Kafa şekli
- Kol ve bacaklar
- Eklemler
- Renkler
- Materyaller
- Animasyon rig'i

gibi özellikleri tanımlar.

Procedural Asset Factory bunları çizilebilir bir nesneye dönüştürür.

**5.3. Asset Library**

Oluşturulan nesneler tekrar kullanılabilir olmalı.

- Character Library
- Environment Library
- Vehicle Library
- Building Library
- Nature Library
- Props Library
- Materials Library
- Animation Library

Her asset sürümlenebilir, önbelleğe alınabilir ve farklı sahnelerde aynı kimlikle kullanılabilir olmalı.

**5.4. Character Consistency**

Aynı karakter farklı sahnelerde değişmemeli.

Karakterin:
- Geometrisi
- Oranları
- Renkleri
- Materyalleri
- Rig yapısı
- Kimliği

korunmalı.

Karakterin hareketleri değişebilir ancak temel görünümü tutarlı kalmalı.

### 6. VEX 2D Engine

2D motoru şu özellikleri desteklemeli:

- Vektör sahneleri
- Parametrik karakterler
- 2D rigging
- Transform animasyonları
- Katman yönetimi
- Parallax
- Kamera pan/zoom
- Maskeleme
- Opacity
- Geçişler
- Frame-accurate rendering

Sahne çıktısı istenen çözünürlükte üretilebilmeli.

Çizim kalitesi çözünürlükten bağımsız vektör mantığıyla korunmalı.

### 7. VEX 3D Engine

3D motoru Blender tabanlı prosedürel sahne oluşturma desteği sağlayacak.

**Özellikler:**

- Procedural mesh generation
- Primitive composition
- Mesh transforms
- Materials
- Lighting
- Camera
- Rigging
- Object animation
- Environment generation
- Particle effects
- Headless rendering

Blender UI'sinin açılması zorunlu olmamalı.

Uygulama Blender'ı arka planda kontrollü bir render süreci olarak kullanabilmeli.

Blender bulunmadığında kullanıcıya kurulum veya uyumlu runtime seçimi gösterilmeli.

Blender'ın lisans ve dağıtım koşullarını dikkate al. EXE içine gömülmesi uygun değilse ayrı runtime kullan.

GPU hızlandırması desteklenmeyen cihazlarda CPU fallback sağla.

### 8. VEX Motion Graphics Engine

Bu motor özellikle anlatım videoları ve bilgi içerikleri için kullanılacak.

Desteklenecekler:

- Kinetic typography
- Text reveal
- Typewriter effect
- Shape morphing
- Graph animation
- Animated counters
- Particle transitions
- Easing curves
- Keyframe interpolation
- Motion blur
- Glow
- Masks
- Timeline-based animation

Animasyonlar sabit FPS'e bağımlı olmamalı.

Zaman tabanlı animasyon sistemi kullan:

```text
position = evaluate(animation, timestamp)
rotation = evaluate(animation, timestamp)
opacity = evaluate(animation, timestamp)
```

Böylece aynı sahne 24, 30 veya 60 FPS olarak render edilebilmeli.

### 9. Kokoro English TTS

Kokoro yalnızca İngilizce kullanılacak.

**Özellikler:**

- İngilizce narration.
- İngilizce karakter diyalogları.
- Ses profili seçimi.
- Konuşma hızı.
- Ses önizleme.
- Sahne bazlı ses üretimi.
- WAV cache.
- Audio normalization.
- Sessizlik ve duraklama yönetimi.

Her sahne için ayrı ses dosyası üretilebilmeli.

Kokoro ses dosyası değişmediyse yeniden üretme.

Seslendirme süreleri sahne planlamasına geri bildirim sağlamalı.

Örneğin narration sekiz saniyeye sığmıyorsa sahne süresini ayarlama veya metni yeniden planlama mekanizması bulunmalı.

### 10. Whisper English Subtitle Engine

Whisper yalnızca İngilizce altyazı için kullanılacak.

**Özellikler:**

- English-only transcription.
- Word timestamps.
- Sentence timestamps.
- SRT export.
- ASS export.
- Subtitle preview.
- Karaoke-style word highlighting.
- Subtitle position.
- Font size.
- Outline.
- Shadow.
- Animation styles.

Kokoro tarafından oluşturulan orijinal narration metni mevcut olduğundan bu metni hizalama referansı olarak kullan.

Whisper transkripsiyonunu orijinal metinle karşılaştır.

Kelime zamanlamalarının hatalı olduğu durumlarda forced alignment veya kontrollü düzeltme uygula.

İngilizce dışındaki diller için TTS veya altyazı modeli sunma.

### 11. Audio Engine

Video yalnızca anlatıcı sesinden oluşmamalı.

Audio Engine şu özellikleri desteklemeli:

- Narration track
- Character dialogue tracks
- Background music track
- Sound effects
- Fade in/out
- Volume automation
- Ducking
- Normalization
- Mixing

İlk sürümde yerel ses dosyası kütüphanesi kullan.

Otomatik müzik veya SFX üretim modeli ekleme.

LLM, mevcut ses kütüphanesinden uygun efektleri seçebilmeli.

Kullanıcı kendi ses dosyalarını içe aktarabilmeli.

### 12. Video Composer ve Export

FFmpeg tabanlı video birleştirme sistemi geliştir.

Desteklenecek çözünürlükler:

- 480p
- 720p
- 1080p
- 1440p
- 2160p

FPS seçenekleri:

- 24
- 30
- 60

Aspect ratio:

- 16:9
- 9:16
- 1:1

Çıktı:

- MP4
- H.264
- AAC

İleri aşamada donanım destekliyorsa GPU encoder kullanılabilir.

Render pipeline:

1. Sahne verilerini yükle.
2. Animasyon zamanlamalarını hesapla.
3. Frame'leri çiz.
4. Sahneleri encode et.
5. Sesleri miksle.
6. Altyazıları uygula.
7. Final MP4 oluştur.
8. Dosyayı doğrula.

Büyük videolarda tüm frame'leri RAM'de tutma.

Streaming veya parça bazlı render kullan.

Render kesildiğinde mümkün olan tamamlanmış sahneler yeniden işlenmemeli.

### 13. Story Studio ve kullanıcı arayüzü

Modern Windows masaüstü arayüzü oluştur.

Tasarım:
- Dark Theme
- Mor vurgu renkleri
- Modern kartlar
- Yumuşak animasyonlar
- Responsive masaüstü düzeni
- Açık durum göstergeleri

**Dashboard**
- Yeni proje
- Mevcut projeler
- Son videolar
- Model durumu
- Render geçmişi

**Story Studio**
- Hikâye giriş alanı
- Video başlığı
- Hedef süre
- Aspect ratio
- Çözünürlük
- FPS
- Görsel stil
- Narration voice
- Generate butonu

**Scene Director**
- Sahne kartları
- Sahne süresi
- Kullanılan motor
- Karakterler
- Kamera hareketi
- Narration
- Sahne önizleme
- Sahneyi yeniden oluşturma

**Asset Library**
- Karakterler
- Ortamlar
- Nesneler
- Materyaller
- Animasyonlar

**Voice Studio**
- Kokoro ses seçimi
- İngilizce ses önizleme
- Konuşma hızı
- Seslendirme üretimi

**Subtitle Studio**
- Whisper altyazı
- Kelime zamanlaması
- Altyazı stili
- Önizleme

**Render Center**
- Toplam ilerleme
- Aktif işlem
- Sahne bazlı ilerleme
- Geçen süre
- Tahmini kalan süre
- CPU/GPU/RAM kullanımı
- Hata günlüğü
- Pause/Cancel
- Resume
- Output klasörünü aç

### 14. Job Scheduler ve gerçek ilerleme sistemi

AI ve render işlemleri arka plan görevleri olarak çalışmalı.

Her görev için durumlar:

```text
PENDING
RUNNING
COMPLETED
FAILED
CANCELLED
INTERRUPTED
```

Görev bağımlılıklarını takip eden bir scheduler oluştur.

Örneğin Whisper hizalaması, ilgili Kokoro ses dosyası hazır olmadan başlamamalı.

İlerleme yüzdeleri gerçek görevlerden alınmalı.

Sahte ilerleme çubukları kullanılmamalı.

Toplam ilerleme, görevlerin ölçülebilir iş yüküne göre hesaplanmalı.

Tahmini kalan süre yalnızca yeterli veri varsa gösterilmeli.

İşlem iptal edildiğinde alt süreçler güvenli biçimde sonlandırılmalı.

Tamamlanmış çıktılar cache'de korunmalı.

### 15. Cache ve proje kaydı

Uygulama aynı sahneleri gereksiz yere tekrar üretmemeli.

Cache anahtarları şunları dikkate almalı:

- Scene JSON
- Asset version
- Animation parameters
- Renderer version
- Narration text
- Kokoro voice settings
- Subtitle settings
- Export settings

Her proje kendi klasöründe saklanmalı.

Örnek:

```text
Projects/
└── MyStory/
    ├── project.json
    ├── scenes/
    ├── assets/
    ├── audio/
    ├── subtitles/
    ├── cache/
    └── exports/
```

Proje kapanıp yeniden açıldığında kaldığı yerden devam edebilmeli.

### 16. Windows EXE dağıtımı

Uygulama Windows için paketlenecek.

Hedef:

- Kullanıcı Python kurmak zorunda kalmasın.
- Kullanıcı kaynak kod derlemek zorunda kalmasın.
- EXE çift tıklanarak başlatılabilsin.
- Gerekli DLL ve uygulama dosyaları paketlensin.
- Modeller ayrı indirilebilsin.
- FFmpeg ve Blender bağımlılıkları açık biçimde yönetilsin.
- Model dosyaları kurulum paketini gereksiz büyütmesin.

Öncelikle güvenilir bir onedir paket üret.

Ardından Windows installer oluştur.

GitHub Actions workflow ekle.

Workflow görevleri:

1. Dependencies install.
2. Static checks.
3. Unit tests.
4. Integration tests.
5. Windows package build.
6. EXE smoke test.
7. Installer build.
8. Artifact upload.

GitHub Actions artifact olarak indirilebilir Windows paketini sağla.

Build başarılı olmadan tamamlandı deme.

### 17. Performans ve bellek yönetimi

Hedef donanım profillerinden biri:

- AMD Ryzen 7 5800H
- AMD Radeon RX 6700M 10 GB VRAM
- 32 GB RAM
- Windows

Bu donanım için Vulkan tabanlı llama.cpp desteğini değerlendir.

LLM ve render motorunun aynı anda VRAM tüketimini kontrol et.

Gerekirse:
- LLM inference bittikten sonra modeli bellekten çıkar.
- Ardından render işlemini başlat.
- Sahne bazlı render kullan.
- Preview çözünürlüğünü düşür.
- CPU fallback uygula.

**Preview çözünürlüğü ile final export çözünürlüğü ayrı olmalı.**

Örneğin 360p preview kullanılırken final video 1080p veya 4K olabilir.

Bu özellik video render motorunda gerçek olarak uygulanmalı.

### 18. Test stratejisi

Yalnızca uygulamanın açılması yeterli değildir.

Gerçek testler oluştur:

- LLM model yükleme testi.
- Geçerli JSON sahne üretimi.
- Geçersiz sahne verisi doğrulama testi.
- 2D frame render testi.
- 3D sahne render testi.
- Motion Graphics testi.
- Kokoro İngilizce WAV üretim testi.
- Whisper İngilizce zamanlama testi.
- FFmpeg MP4 üretim testi.
- Proje kaydetme ve yeniden açma testi.
- Cache testi.
- Render iptal/devam testi.
- EXE başlatma testi.

Entegrasyon testleri gerçek çıktıları doğrulamalı.

Eksik model veya runtime nedeniyle yapılamayan testleri açıkça raporla. Mock testlerin gerçek model testlerinin yerine geçtiğini iddia etme.

### 19. Aşamalı geliştirme planı

**FAZ 1 — Foundation**

- Proje yapısı.
- Windows UI.
- Dashboard.
- Proje yönetimi.
- Settings.
- Logging.
- Job Scheduler.
- GitHub Actions temel CI.

**FAZ 2 — Local LLM**

- llama.cpp entegrasyonu.
- GGUF yükleme.
- Vulkan desteği.
- Model Manager.
- Story Director.
- Scene JSON schema.
- Validation ve recovery.

**FAZ 3 — 2D Drawing Engine**

- Scene graph.
- Parametrik çizim.
- Shape primitives.
- Transform sistemi.
- 2D animation.
- Camera.
- İlk gerçek 2D video testi.

**FAZ 4 — Procedural Asset Factory**

- Dinamik nesne tanımlama.
- Character Library.
- Environment Library.
- Asset Registry.
- Character consistency.
- Asset cache.

**FAZ 5 — Motion Graphics**

- Keyframe engine.
- Text animation.
- Shape animation.
- Easing.
- Transitions.
- Motion graphics render.

**FAZ 6 — Procedural 3D**

- Blender integration.
- Mesh generation.
- Materials.
- Lighting.
- Camera animation.
- Headless rendering.
- 3D video testi.

**FAZ 7 — Kokoro + Whisper**

- English TTS.
- Voice Studio.
- English subtitles.
- Word alignment.
- Subtitle Studio.
- SRT/ASS export.

**FAZ 8 — Video Composer**

- Audio mixing.
- Scene composition.
- FFmpeg.
- Resolution/FPS settings.
- MP4 export.
- Render cache.
- Resume.

**FAZ 9 — Full Automation**

- Hikâyeden videoya tek işlem.
- Otomatik sahne planlama.
- Otomatik çizim.
- Otomatik animasyon.
- Otomatik seslendirme.
- Otomatik altyazı.
- Otomatik render.

**FAZ 10 — Release**

- Windows EXE.
- Installer.
- GitHub Actions build.
- Artifact upload.
- Smoke tests.
- README.
- Kullanıcı kılavuzu.

### 20. Geliştirme çalışma kuralları

Her fazda:

1. Mevcut kodu incele.
2. Geliştirme kapsamını belirle.
3. Gerçek çalışan kod yaz.
4. Testleri çalıştır.
5. Hataları düzelt.
6. Önceki çalışan özellikleri koru.
7. Değişiklikleri raporla.
8. Bir sonraki faza geç.

Sadece TODO bırakıp özelliği tamamlandı olarak işaretleme.

Bir özelliğin çalışması için eksik bağımlılık varsa açıkça belirt.

Arayüzde bulunan her buton gerçek bir fonksiyona bağlı olmalı.

Önce basit ama çalışan uçtan uca video üretimini gerçekleştir. Ardından çizim çeşitliliğini, 3D motorunu ve gelişmiş animasyonları artır.

### 21. İlk kabul testi

İlk çalışan sürümün aşağıdaki hikâyeyi videoya dönüştürebilmesini hedefle:

"A small robot wakes up in an abandoned city. It looks around, walks toward a glowing tower, and discovers a mysterious message."

Beklenen:

- Yerel LLM hikâyeyi sahnelere ayırır.
- Robot ve şehir prosedürel olarak çizilir.
- Robot hareket eder.
- Kamera animasyonları uygulanır.
- Kokoro İngilizce anlatıcı sesi üretir.
- Whisper İngilizce altyazıları hizalar.
- FFmpeg videoyu birleştirir.
- Kullanıcı gerçek MP4 dosyasını açabilir.

Görüntü üretim modeli veya video üretim modeli kullanılmayacak.

### 22. Son teslimat

Geliştirme tamamlandığında şunları sun:

- Çalışan kaynak kod.
- Kurulum ve kullanım README dosyası.
- Teknik mimari dokümantasyonu.
- Çizim motoru dokümantasyonu.
- Sahne JSON şeması.
- Test sonuçları.
- GitHub Actions workflow.
- Windows EXE/installer.
- İndirilebilir build artifact.

**Öncelik sırası:**

1. Gerçek işlevsellik.
2. Güvenilir mimari.
3. Video üretim kalitesi.
4. Performans.
5. Modern arayüz.
6. Dağıtım kolaylığı.

Şimdi projeyi geliştirmeye başla. İlk olarak mimariyi ve bağımlılıkları doğrula, ardından Faz 1'i uygula. Planı yalnızca yazıp bırakma; mevcut araç ve izinlerin ölçüsünde gerçek dosyaları oluştur, test et ve aşamalı olarak ilerle.