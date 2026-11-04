# VEX AI Video Generator — çalışma kuralları

## Her oturumda

1. Önce bu dosyayı ve `docs/PROGRESS.md` dosyasını oku.
2. `git status --short --branch` ile yerel değişiklikleri kontrol et; kullanıcı değişikliklerini koru.
3. Sadece seçilen küçük göreve ait kod, yapılandırma ve testleri aç. Tam şartnameyi ancak ilgili gereksinim için oku.
4. Göreve başlamadan ilerleme dosyasında kapsamı ve kabul ölçütünü belirt.
5. Gerçek uygulamayı tamamla, ilgili kontrolleri çalıştır, ardından sonucu kaydet.
6. Her küçük aşama sonunda `docs/PROGRESS.md` güncellenmeli: durum, değişen dosyalar, çalıştırılan kontroller, sonuç, engeller ve sıradaki adım.

## Bağlam bütçesi

- `.git`, `.venv`, `node_modules`, `__pycache__`, model ağırlıkları, cache, log, frame, video, build ve dist içeriklerini topluca okuma.
- Önce `rg --files` ile hedef dosyaları bul; ilgili modülü ve gerekli testleri seçerek oku.
- Tam şartname: `docs/SPECIFICATION.md`. İlerleme ve görev sırası: `docs/PROGRESS.md`.
- Model veya araç çıktısı, kodun çalıştığının kanıtı değildir. Test sonucu ile beklentiyi ayır.

## Değişmez ürün sınırları

- Windows 10/11 x64 masaüstü uygulaması; temel üretim akışı yerel ve çevrimdışı.
- Yalnızca yerel LLM/GGUF; bulut LLM API'si yok.
- Görüntü/video üretim modeli yok. Görseller uygulamanın prosedürel 2D, 3D ve motion motorlarından gelir.
- Kokoro TTS ve Whisper yalnızca İngilizce; müzik/SFX için yerel dosyalar.
- LLM yalnızca doğrulanan, izin listeli scene DSL/JSON üretir. LLM metnini Python, shell veya Blender kodu olarak çalıştırma.
- AI/render işleri UI iş parçacığını engellememeli. İlerleme ölçülebilir gerçek işten gelmeli.
- Tamamlanmamış özellikleri çalışan düğme, sahte çıktı veya sahte yüzde ile sunma.
- Önce gerçek uçtan uca küçük 2D video; gelişmiş motorlar ve UI kapsamı daha sonra genişletilir.
- Modelleri, render çıktısını ve büyük runtime dosyalarını Git'e ekleme.

## Tamamlanma tanımı

- Kod + ilgili gerçek kontrol + kaydedilmiş sonuç gerekir; yalnızca TODO veya taslak tamamlanma sayılmaz.
- Eksik model/runtime nedeniyle çalışmayan testler açıkça belirtilir; mock test gerçek entegrasyonun yerine geçmez.
- EXE/installer ancak build, başlatma kontrolü ve çıktı doğrulaması başarılıysa tamamlanmış sayılır.
- Herhangi bir commit/push/release yapılmış olduğunu ancak gerçekten yapıldıysa raporla.

## Mevcut başlangıç

2026-11-04 ilk incelemesinde origin boştu. Kullanıcının sonraki talebiyle v0.1 geliştirildi: PySide6/QML masaüstü, proje/görev kaydı, yerel llama.cpp, prosedürel 2D/motion/Blender 3D, Kokoro/Whisper ve gerçek MP4. Güncel test, paket ve kalan işler `docs/PROGRESS.md` içindedir; eski inceleme kaydını güncel durum sanma. Origin bağlantısı korunuyor. Güncel uzak durumu git remote/log ile doğrula; release yayımlanmadı.
