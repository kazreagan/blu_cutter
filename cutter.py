import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pydub import AudioSegment
import pygame
import tempfile
import threading
import os
import time

class Mp3CutterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Blu Cutter")
        self.root.geometry("700x450")
        self.root.configure(bg="#1E1E2F")  

        self.audio = None
        self.original_file = None
        self.duration_ms = 0
        self.tempfile = None
        self.is_playing = False
        self.current_playing = None  

        # Initialize pygame mixer
        pygame.mixer.init()
        self.preview_channel = pygame.mixer.Channel(0)
        self.full_channel = pygame.mixer.Channel(1)

        #style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", font=("Segoe UI", 11, "bold"), padding=8,
                        background="#2f80ed", foreground="white")
        style.map("TButton", background=[("active", "#6B84E4")])
        style.configure("TScale", troughcolor="#33334D", background="#4B6ED4", sliderlength=20)

        #load button
        ttk.Button(root, text="Load MP3", command=self.load_file).pack(pady=15)

        #sliders
        sliders_frame = tk.Frame(root, bg="#1E1E2F")
        sliders_frame.pack(fill="x", padx=30, pady=10)

        #start slider + label
        self.start_label = tk.Label(sliders_frame, text="0 s", bg="#1E1E2F", fg="white", font=("Segoe UI", 10))
        self.start_label.pack(anchor="e")
        self.start_slider = ttk.Scale(sliders_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                      command=self.update_start)
        self.start_slider.pack(fill="x", pady=5)

        #end slider + label
        self.end_label = tk.Label(sliders_frame, text="0 s", bg="#1E1E2F", fg="white", font=("Segoe UI", 10))
        self.end_label.pack(anchor="e")
        self.end_slider = ttk.Scale(sliders_frame, from_=0, to=100, orient=tk.HORIZONTAL,
                                    command=self.update_end)
        self.end_slider.pack(fill="x", pady=5)

        #buttons
        buttons_frame = tk.Frame(root, bg="#1E1E2F")
        buttons_frame.pack(pady=15)

        ttk.Button(buttons_frame, text="Play Full", command=self.play_full).grid(row=0, column=0, padx=10)
        ttk.Button(buttons_frame, text="Stop", command=self.stop_playback).grid(row=0, column=1, padx=10)
        ttk.Button(buttons_frame, text="Preview", command=self.preview_selection).grid(row=0, column=2, padx=10)
        ttk.Button(buttons_frame, text="Cut & Save", command=self.cut_audio).grid(row=0, column=3, padx=10)

        #info
        self.info_label = tk.Label(root, text="No file loaded", bg="#1E1E2F", fg="white",
                                   font=("poppins", 10), anchor="center")
        self.info_label.pack(pady=10, fill="x")

    #audio logic
    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("MP3 files", "*.mp3")])
        if not file_path:
            return

        self.audio = AudioSegment.from_file(file_path, format="mp3")
        self.original_file = file_path
        self.duration_ms = len(self.audio)
        duration_sec = self.duration_ms // 1000

        #configure sliders
        self.start_slider.config(to=duration_sec)
        self.end_slider.config(to=duration_sec)
        self.start_slider.set(0)
        self.end_slider.set(duration_sec)

        #update dynamic labels
        self.start_label.config(text=f"{0} s")
        self.end_label.config(text=f"{duration_sec} s")

        self.info_label.config(text=f"Loaded: {os.path.basename(file_path)} ({duration_sec}s)")

    #update functions for dynamic second labels
    def update_start(self, value):
        self.start_label.config(text=f"{int(float(value))} s")
        self.preview_snippet(value, 'start')

    def update_end(self, value):
        self.end_label.config(text=f"{int(float(value))} s")
        self.preview_snippet(value, 'end')

    def preview_snippet(self, value, slider_type):
        if not self.audio or self.current_playing is not None:
            return

        pos_sec = int(float(value))
        snippet = self.audio[pos_sec * 1000:pos_sec * 1000 + 1500]

        if self.tempfile:
            try: os.remove(self.tempfile)
            except: pass

        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        snippet.export(temp.name, format="wav")
        self.tempfile = temp.name
        temp.close()

        sound = pygame.mixer.Sound(self.tempfile)
        self.preview_channel.play(sound)

    def preview_selection(self):
        if not self.audio:
            return

        if self.current_playing == "full":
            self.full_channel.stop()
        elif self.current_playing == "selection":
            self.preview_channel.stop()

        self.is_playing = False
        self.current_playing = "selection"

        start_sec = int(self.start_slider.get())
        end_sec = int(self.end_slider.get())
        if start_sec >= end_sec:
            messagebox.showwarning("Error", "Start must be less than End!")
            self.current_playing = None
            return

        segment = self.audio[start_sec * 1000:end_sec * 1000]

        if self.tempfile:
            try: os.remove(self.tempfile)
            except: pass

        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        segment.export(temp.name, format="wav")
        self.tempfile = temp.name
        temp.close()

        sound = pygame.mixer.Sound(self.tempfile)
        self.preview_channel.play(sound)

    def play_full(self):
        if not self.original_file or not os.path.exists(self.original_file):
            messagebox.showwarning("Error", "No audio loaded!")
            return

        self.preview_channel.stop()
        self.is_playing = True
        self.full_channel.stop()
        self.current_playing = "full"

        sound = pygame.mixer.Sound(self.original_file)
        self.full_channel.play(sound)

        def update_slider():
            duration_sec = self.duration_ms / 1000
            start_time = time.time()
            while self.is_playing and self.full_channel.get_busy():
                elapsed = time.time() - start_time
                self.start_slider.set(min(int(elapsed), int(duration_sec)))
                self.start_label.config(text=f"{int(min(elapsed, duration_sec))} s")
                time.sleep(0.2)
            self.is_playing = False
            self.current_playing = None

        threading.Thread(target=update_slider, daemon=True).start()

    def stop_playback(self):
        if self.current_playing == "full":
            self.full_channel.stop()
        elif self.current_playing == "selection":
            self.preview_channel.stop()
        self.is_playing = False
        self.current_playing = None

    def cut_audio(self):
        if not self.audio:
            messagebox.showwarning("Error", "No audio loaded!")
            return

        start_sec = int(self.start_slider.get())
        end_sec = int(self.end_slider.get())

        if start_sec >= end_sec:
            messagebox.showwarning("Error", "Start must be less than End!")
            return

        cut = self.audio[start_sec * 1000:end_sec * 1000]

        save_path = filedialog.asksaveasfilename(
            defaultextension=".mp3", filetypes=[("MP3 files", "*.mp3")]
        )
        if save_path:
            cut.export(save_path, format="mp3")
            messagebox.showinfo("Success", "Saved Successfully")

if __name__ == "__main__":
    root = tk.Tk()
    app = Mp3CutterApp(root)
    root.mainloop()