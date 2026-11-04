# Bağımlılıklar ve kaynaklar

Test ortamı: Windows 11 x64, Python 3.12.14. PySide6-Essentials 6.12.0, Pydantic 2.14.2 ve imageio-ffmpeg 0.8.1 Windows wheel olarak kuruldu. Ses testleri kokoro-onnx 0.6.1, faster-whisper 1.2.1 ve PyAV 16.1.0 ile yapıldı. PyAV 19, faster-whisper 1.2.1'in kullandığı `metadata_errors` parametresini kabul etmediği için `av<17` sınırı eklendi.

Tam test edilmiş ortam sürümleri `requirements-windows.lock.txt` dosyasında bulunur. Windows 10 ve temiz Python bulunmayan başka bir makine üzerinde bağımsız test henüz yapılmadı.

## Resmî kaynaklar

- Qt for Python kurulum ve LGPLv3/GPLv3/commercial seçenekleri: https://doc.qt.io/qtforpython-6/
- Pydantic (MIT): https://github.com/pydantic/pydantic
- llama.cpp (MIT), server sözleşmesi: https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md
- Kullanılan Windows runtime: https://github.com/ggml-org/llama.cpp/releases/tag/b12110
- Kokoro ONNX (MIT): https://github.com/thewh1teagle/kokoro-onnx
- Kokoro model ve voices: https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0
- Kokoro-82M model kartı/lisans: https://huggingface.co/hexgrad/Kokoro-82M
- faster-whisper (MIT): https://github.com/SYSTRAN/faster-whisper
- Whisper tiny.en dönüştürülmüş model: https://huggingface.co/Systran/faster-whisper-tiny.en
- Qwen2.5 0.5B GGUF model kartı/lisans: https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF
- Varsayılan Qwen2.5 1.5B GGUF model kartı/lisans: https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF
- imageio-ffmpeg Python wrapper (BSD-2-Clause): https://github.com/imageio/imageio-ffmpeg
- FFmpeg lisans ve build ayrıntıları: `ffmpeg -L`, `ffmpeg -buildconf`; https://ffmpeg.org/legal.html
- Blender portable runtime ve lisans: https://www.blender.org/about/license/
- PyInstaller: https://pyinstaller.org/en/stable/license.html
- espeak-ng/phonemizer gibi ses bağımlılıklarının lisansları da paket kapsamında değerlendirilmelidir: https://github.com/espeak-ng/espeak-ng ve https://github.com/bootphon/phonemizer

Paketlerin ve model ağırlıklarının lisansları birbirinden ayrıdır. Kaynak listesi bir dağıtım/lisans denetiminin tamamlandığı anlamına gelmez. Bu sürüm imzalı/sertifikalı genel release olarak yayımlanmadı; üçüncü taraf lisans metinleri `third_party_licenses` klasöründe korunur.
