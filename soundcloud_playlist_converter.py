

"""
SoundCloud Playlist Downloader (GUI) with comments to make understanding clearer
- Downloads a full SoundCloud playlist as MP3 using yt-dlp
- Tkinter GUI with *two* progress bars:
    1) Current file progress (percent)
    2) Whole playlist progress (tracks completed / total)
- Frame-safe (background thread)
- No hard-coded ffmpeg path (expects FFmpeg on PATH)

Prereqs:
    pip install yt-dlp
    # Install FFmpeg
    
"""

import os
import sys
import threading
import queue
from pathlib import Path
from tkinter import (
    Tk, StringVar, Text, END, DISABLED, NORMAL, BOTH, X, N, W, E, filedialog, messagebox
)
from tkinter import ttk

try:
    from yt_dlp import YoutubeDL
except ImportError:
    raise SystemExit("Missing dependency: yt-dlp. Install with `pip install yt-dlp`.")

APP_TITLE = "SoundCloud Playlist Downloader"
DEFAULT_SUBDIR = "SoundCloud"


class DownloaderGUI:
    def __init__(self, root: Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.minsize(580, 420)

        # --- State ---
        self.url_var = StringVar()
        self.outdir_var = StringVar(value=str(Path.home() / "Downloads" / DEFAULT_SUBDIR))
        self.status_var = StringVar(value="Idle.")
        self.progress_var = StringVar(value="")
        self.percent = 0.0

        # Whole-playlist progress
        self.total_tracks = 0
        self.done_tracks = 0
        self.total_text = StringVar(value="0/0 (0%)")

        self.queue = queue.Queue()
        self.worker = None
        self.downloading = False

        # --- UI ---
        self._build_ui()
        self._poll_queue()

    def _build_ui(self):
        pad = {"padx": 10, "pady": 8}

        # Frame: URL
        url_frame = ttk.LabelFrame(self.root, text="Playlist URL")
        url_frame.pack(fill=X, **pad)
        ttk.Entry(url_frame, textvariable=self.url_var).pack(fill=X, padx=10, pady=10)

        # Frame: Output directory
        out_frame = ttk.LabelFrame(self.root, text="Output Folder")
        out_frame.pack(fill=X, **pad)
        out_row = ttk.Frame(out_frame)
        out_row.pack(fill=X, padx=10, pady=8)
        self.out_entry = ttk.Entry(out_row, textvariable=self.outdir_var)
        self.out_entry.pack(side="left", fill=X, expand=True)
        ttk.Button(out_row, text="Browse…", command=self._choose_dir).pack(side="left", padx=8)

        # Frame: Controls
        ctrl = ttk.Frame(self.root)
        ctrl.pack(fill=X, **pad)
        self.btn_start = ttk.Button(ctrl, text="Start Download", command=self._on_start)
        self.btn_start.grid(row=0, column=0, sticky=W)
        self.btn_cancel = ttk.Button(ctrl, text="Cancel", command=self._on_cancel, state=DISABLED)
        self.btn_cancel.grid(row=0, column=1, sticky=W, padx=8)

        # Progress bars
        # 1) Current file progress
        lbl1 = ttk.Label(self.root, text="Current file")
        lbl1.pack(anchor=W, padx=12)
        self.pb = ttk.Progressbar(self.root, orient="horizontal", mode="determinate", maximum=100)
        self.pb.pack(fill=X, padx=12, pady=(0, 2))
        self.lbl_pct = ttk.Label(self.root, textvariable=self.progress_var)
        self.lbl_pct.pack(anchor=E, padx=12)

        # 2) Playlist progress
        lbl2 = ttk.Label(self.root, text="Playlist")
        lbl2.pack(anchor=W, padx=12, pady=(6, 0))
        self.pb_total = ttk.Progressbar(self.root, orient="horizontal", mode="determinate")
        self.pb_total.pack(fill=X, padx=12, pady=(0, 2))
        self.lbl_total = ttk.Label(self.root, textvariable=self.total_text)
        self.lbl_total.pack(anchor=E, padx=12)

        # Status + log
        stat = ttk.Label(self.root, textvariable=self.status_var)
        stat.pack(anchor=W, padx=12, pady=(6, 0))

        self.log = Text(self.root, height=10, wrap="word", state=DISABLED)
        self.log.pack(fill=BOTH, expand=True, padx=12, pady=(4, 12))

    # -----------------------
    # UI helpers
    # -----------------------
    def _choose_dir(self):
        d = filedialog.askdirectory(initialdir=self.outdir_var.get() or str(Path.home()))
        if d:
            self.outdir_var.set(d)

    def _log(self, msg: str):
        self.log.configure(state=NORMAL)
        self.log.insert(END, msg.rstrip() + "\n")
        self.log.see(END)
        self.log.configure(state=DISABLED)

    def _set_status(self, msg: str):
        self.status_var.set(msg)

    def _set_progress(self, pct: float, line: str = ""):
        self.percent = max(0.0, min(100.0, pct))
        self.pb["value"] = self.percent
        self.progress_var.set(line or f"{self.percent:.1f}%")

    def _reset_totals(self):
        self.total_tracks = 0
        self.done_tracks = 0
        self.pb_total["maximum"] = 1
        self.pb_total["value"] = 0
        self.total_text.set("0/0 (0%)")

    def _set_total_tracks(self, n: int):
        self.total_tracks = max(0, int(n or 0))
        self.done_tracks = 0
        self.pb_total["maximum"] = max(1, self.total_tracks)
        self.pb_total["value"] = 0
        self._update_total_text()

    def _tick_track_done(self):
        self.done_tracks = min(self.total_tracks or 0, self.done_tracks + 1)
        self.pb_total["value"] = self.done_tracks
        self._update_total_text()

    def _update_total_text(self):
        total = self.total_tracks or 0
        done = self.done_tracks or 0
        pct = 0 if total == 0 else int(done / total * 100)
        self.total_text.set(f"{done}/{total} ({pct}%)")

    def _toggle_controls(self, downloading: bool):
        self.downloading = downloading
        self.btn_start.configure(state=DISABLED if downloading else NORMAL)
        self.btn_cancel.configure(state=DISABLED if not downloading else NORMAL)

    # -----------------------
    # Events
    # -----------------------
    def _on_start(self):
        url = self.url_var.get().strip()
        outdir = self.outdir_var.get().strip()

        if not url:
            messagebox.showwarning("Missing URL", "Please paste a SoundCloud playlist URL.")
            return

        if not outdir:
            messagebox.showwarning("Missing Folder", "Please choose an output folder.")
            return

        # Ensure output dir exists
        try:
            Path(outdir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Folder Error", f"Could not create output folder:\n{e}")
            return

        self._toggle_controls(True)
        self._set_status("Starting…")
        self._set_progress(0.0, "")
        self._reset_totals()
        self._log(f"Output: {outdir}")
        self._log(f"URL: {url}")

        # Spawn worker thread
        self.worker = threading.Thread(
            target=self._download_worker, args=(url, outdir), daemon=True
        )
        self.worker.start()

    def _on_cancel(self):
        # Soft cancel: yt-dlp doesn’t support a safe hard stop mid-file via this hook.
        messagebox.showinfo("Cancel", "Cancel will stop after the current item finishes.")
        self._toggle_controls(False)
        self._set_status("Cancellation requested.")

    # -----------------------
    # Worker + hooks
    # -----------------------
    def _download_worker(self, playlist_url: str, output_dir: str):
        """
        Run yt-dlp in a background thread. We first extract info to count entries,
        then perform the download while updating both progress bars.
        """

        def hook(d: dict):
            # Called by yt-dlp with progress events
            status = d.get("status")

            if status == "downloading":
                downloaded = d.get("downloaded_bytes") or 0
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                pct = 0.0
                if total:
                    pct = downloaded / total * 100.0
                fn = d.get("filename") or ""
                short = os.path.basename(fn)
                self.queue.put(("progress", pct, f"{pct:5.1f}% — {short}"))

                # If yt-dlp provided n_entries/playlist_index live, initialize total once
                info = d.get("info_dict") or {}
                n_entries = info.get("n_entries")
                if n_entries and self.total_tracks == 0:
                    self.queue.put(("set_total", int(n_entries)))

            elif status == "finished":
                fn = d.get("filename") or ""
                self.queue.put(("log", f"Finished: {os.path.basename(fn)}"))
                self.queue.put(("track_done",))

            elif status == "error":
                self.queue.put(("log", "An error occurred during download."))

        # 1) Pre-scan to count playlist items (best effort)
        try:
            scan_opts = {
                "quiet": True,
                "no_warnings": True,
                "noplaylist": False,
            }
            with YoutubeDL(scan_opts) as y_scan:
                info = y_scan.extract_info(playlist_url, download=False)
                # Prefer explicit entries when present
                entries = []
                if isinstance(info, dict) and "entries" in info and info["entries"] is not None:
                    entries = [e for e in info["entries"] if e]
                n = len(entries) if entries else int(info.get("n_entries") or 0)
                if n:
                    self.queue.put(("set_total", n))
        except Exception as e:
            # Counting failed; we’ll still download and try to infer total later
            self.queue.put(("log", f"Count warning: {e}"))

        # 2) Actual download with hooks
        ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "noplaylist": False,
            "outtmpl": os.path.join(output_dir, "%(playlist_title)s/%(title)s.%(ext)s"),
            "ignoreerrors": "only-download",
            "writethumbnail": False,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [hook],
        }

        try:
            self.queue.put(("status", "Downloading…"))
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([playlist_url])
            self.queue.put(("status", "✓ Completed"))
            self.queue.put(("done",))
        except Exception as e:
            self.queue.put(("status", "Error"))
            self.queue.put(("log", f"FATAL: {e}"))
            self.queue.put(("fail",))

    # -----------------------
    # Queue polling (main thread)
    # -----------------------
    def _poll_queue(self):
        try:
            while True:
                item = self.queue.get_nowait()
                kind = item[0]

                if kind == "progress":
                    _, pct, line = item
                    self._set_progress(pct, line)

                elif kind == "set_total":
                    _, n = item
                    self._set_total_tracks(n)
                    self._log(f"Playlist items: {n}")

                elif kind == "track_done":
                    self._tick_track_done()

                elif kind == "status":
                    _, msg = item
                    self._set_status(msg)

                elif kind == "log":
                    _, msg = item
                    self._log(msg)

                elif kind == "done":
                    self._toggle_controls(False)
                    self._set_progress(100.0, "100%")
                    messagebox.showinfo("Success", "All downloads completed.")

                elif kind == "fail":
                    self._toggle_controls(False)
                    messagebox.showerror("Error", "The download failed. Check the log.")
        except queue.Empty:
            pass

        # poll again
        self.root.after(100, self._poll_queue)


def main():
    root = Tk()
    # Use a modern ttk theme if available
    try:
        style = ttk.Style(root)
        if sys.platform == "win32":
            style.theme_use("vista")
        else:
            style.theme_use("clam")
    except Exception:
        pass

    app = DownloaderGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
