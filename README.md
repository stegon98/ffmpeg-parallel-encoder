# Multi-threaded Video Converter (H.264 → HEVC)

This Python script scans an input folder, processes all video files, and converts them from **H.264** to **HEVC** (H.265) using `ffmpeg`.  
It leverages **multi-threaded workers** to process multiple files in parallel, improving overall performance.

If a file is not encoded in H.264, the script will simply **copy** it to the output folder without re-encoding.  
The default configuration is optimized for **AMD GPU acceleration** (`hevc_amf`), tested on an **AMD RX 7800X**.

---

## ✨ Features
- 🚀 **Multi-threaded execution** (customizable number of workers).
- 🎥 Converts **H.264** videos to **HEVC (H.265)** using AMD GPU acceleration.
- 📂 Preserves the **input folder structure** inside the output directory.
- ⏩ **Skips already converted files** to save time.
- 🪟 Windows-friendly (uses `copy` command for non-H.264 files).

---

## 📦 Requirements
- **Python 3.7+**
- **ffmpeg** and **ffprobe** installed and accessible from your system PATH  
  👉 Download here: [ffmpeg.org](https://ffmpeg.org/)

---

## ⚙️ Installation
Clone this repository and ensure that `ffmpeg` is installed:

## ▶️ Run with `conv.bat`
