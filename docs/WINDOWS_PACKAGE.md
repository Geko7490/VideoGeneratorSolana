# VEX Video — Windows paketi

1. ZIP dosyasını bir klasöre çıkarın. `VEXVideo.exe` ve `_internal` klasörü birlikte kalmalıdır.
2. `VEXVideo.exe` dosyasını açın. Python kurmanız gerekmez.
3. Model olmadan denemek için **Prosedürel robot örneğini aç**, ardından **360p video önizle** seçin. Bu işlem gerçek sessiz video üretir.
4. Hikâyeden sesli video için **Ayarlar → Temel modelleri indir** seçin. Yaklaşık 1.6 GB dosya indirilir; ilk indirmede internet gerekir. Sonraki inference yereldir.
5. Hikâyeyi yazıp **Hikâyeden sesli MP4 üret** seçin. Yerel LLM, Kokoro ve Whisper sırayla çalışır.

Veriler `%LOCALAPPDATA%\VEXVideo` altında saklanır. Ayarlarda Windows yollarını `/` veya JSON için çift ters bölü ile yazın. Yerel GGUF/runtime dosyaları ayrıca seçilebilir. Blender 3D için ayrı Blender runtime gerekir; bu pakete dahil değildir.

Bu v0.1 geliştirme sürümüdür. İmzalı installer değildir. Windows 11 üzerinde kontrol edilmiştir; Windows 10 ve temiz farklı makine doğrulaması henüz yapılmamıştır. Görsel kalite temel prosedürel primitive düzeyindedir. İleri özelliklerin ve bilinen sınırların listesi kaynak projedeki `docs/PROGRESS.md` ve `docs/ARCHITECTURE.md` dosyalarındadır.

Güvenli yerleşim düzeltmesi uygulanırsa uygulama bunu uyarıyla gösterir. İşlem iptal edilirse tamamlanan sahne cache'leri korunur; aynı render tekrar başlatılarak kullanılabilir.
