<h1 align="center">🎧 SoundCloud Playlist Downloader</h1>
<p align="center">
  <i>A simple tool I built to download full SoundCloud playlists as MP3 — made to solve a real problem I faced as a DJ.</i><br>
  <b>Python · yt-dlp · Tkinter GUI</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Language-Python-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Tool-yt--dlp-orange.svg" alt="yt-dlp">
  <img src="https://img.shields.io/badge/Interface-Tkinter-lightgrey.svg" alt="Tkinter">
  <img src="https://img.shields.io/badge/Year-2025-lightgrey.svg" alt="Year">
</p>

---

### 🎯 Overview
This project started from a **real need** — as a DJ, I often wanted to keep offline copies of **SoundCloud playlists** I used for sets or inspiration.  
Manually downloading each track was time-consuming, so I decided to create a small, reliable Python tool that could **automate the process** and handle entire playlists cleanly.

It’s a personal project, but it became a genuinely useful tool in my workflow.

---

### 🧠 What It Does
- Downloads **entire SoundCloud playlists** as MP3 files  
- Displays **two progress bars**:
  - One for the current track  
  - One for the full playlist  
- Automatically organizes tracks into folders by playlist name  
- Works via a clean **Tkinter GUI** (no terminal needed)  

---

### ⚙️ Tech Stack
- **Language:** Python  
- **Libraries:** yt-dlp, Tkinter  
- **Features:** Multithreading, progress hooks, playlist scanning, FFmpeg post-processing  

---

### 💡 Why I Built It
As a **DJ**, I regularly curate playlists for events and mixes.  
Having a quick way to **batch-download SoundCloud playlists** made it much easier to prepare tracks offline, test transitions, and manage files without relying on unstable third-party websites.  
This project turned a repetitive task into a simple one-click process.

---

### 🪄 How to Use
```bash
pip install yt-dlp
# Make sure FFmpeg is installed and on your PATH

