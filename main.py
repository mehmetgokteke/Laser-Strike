import tkinter as tk
from tkinter import ttk, messagebox
import serial
import threading
import time
import json
import os

PORT = 'COM3'  # Arduino port
BAUD = 9600
DATA_FILE = "game_records.json"

class LaserGameApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Laser Target Game")
        self.geometry("600x400")
        self.resizable(False, False)
        self.configure(bg="#121212")  

        self.style = ttk.Style(self)
        self.style.theme_use('clam')  
        self.style.configure("TButton",
                             font=("Segoe UI", 11),
                             padding=8)
        self.style.configure("TLabel",
                             background="#121212",
                             foreground="#e0e0e0",
                             font=("Segoe UI", 12))
        self.style.configure("Header.TLabel",
                             font=("Segoe UI", 16, "bold"),
                             foreground="#00ff99")

        self.username = ""
        self.score = 0
        self.missed = 0
        self.game_running = False

        self.records = self.load_records()

        self.create_widgets()

        self.serial_thread = None
        self.serial_running = False

    def create_widgets(self):
        self.frames = {}

        # Kullanıcı adı 
        self.frames['login'] = tk.Frame(self, bg="#121212")
        self.frames['login'].pack(fill="both", expand=True)

        ttk.Label(self.frames['login'], text="Oyuncu Adınızı Girin", style="Header.TLabel").pack(pady=(40,10))
        self.name_entry = ttk.Entry(self.frames['login'], font=("Segoe UI", 14))
        self.name_entry.pack(pady=10, ipadx=8, ipady=4)
        self.name_entry.focus()

        self.start_button = ttk.Button(self.frames['login'], text="Oyuna Gir", command=self.start_game)
        self.start_button.pack(pady=20)

        # Ana oyun ekranı
        self.frames['game'] = tk.Frame(self, bg="#121212")

        # Başlık ve kullanıcı adı
        self.user_label = ttk.Label(self.frames['game'], text="", style="Header.TLabel")
        self.user_label.grid(row=0, column=0, sticky="w", padx=20, pady=15)

        # Oyun 
        self.status_label = ttk.Label(self.frames['game'], text="Oyun Durumu: Durdu", font=("Segoe UI", 14), foreground="#ff5555")
        self.status_label.grid(row=0, column=1, sticky="e", padx=20)

        score_frame = ttk.Frame(self.frames['game'])
        score_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=10, sticky="ew")

        # Skor 
        header_label = ttk.Label(score_frame, text="Skor Bilgileri", style="Header.TLabel")
        header_label.grid(row=0, column=0, columnspan=2, pady=(0,10))

        self.score_label = ttk.Label(score_frame, text="Vurulan Hedefler: 0", font=("Segoe UI", 14))
        self.score_label.grid(row=1, column=0, padx=20, pady=5, sticky="w")

        self.missed_label = ttk.Label(score_frame, text="Kaçırılan Hedefler: 0", font=("Segoe UI", 14))
        self.missed_label.grid(row=1, column=1, padx=20, pady=5, sticky="w")


        # Kayıtlar
        self.records_button = ttk.Button(self.frames['game'], text="Kayıtları Görüntüle", command=self.show_records)
        self.records_button.grid(row=2, column=0, columnspan=2, pady=20)

        # Grid 
        self.frames['game'].columnconfigure(0, weight=1)
        self.frames['game'].columnconfigure(1, weight=1)

    def start_game(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Uyarı", "Lütfen bir isim girin!")
            return
        self.username = name
        self.score = 0
        self.missed = 0

        self.user_label.config(text=f"Oyuncu: {self.username}")
        self.score_label.config(text="Vurulan Hedefler: 0")
        self.missed_label.config(text="Kaçırılan Hedefler: 0")
        self.status_label.config(text="Oyun Durumu: Durdu", foreground="#ff5555")

        self.frames['login'].pack_forget()
        self.frames['game'].pack(fill="both", expand=True)

        self.serial_running = True
        self.serial_thread = threading.Thread(target=self.read_serial)
        self.serial_thread.daemon = True
        self.serial_thread.start()

    def read_serial(self):
        try:
            with serial.Serial(PORT, BAUD, timeout=1) as ser:
                while self.serial_running:
                    line = ser.readline().decode(errors='ignore').strip()
                    if not line:
                        continue

                    if "GAME START" in line:
                        self.game_running = True
                        self.update_status("Oyun Başladı", "#00ff99")
                    elif "GAME STOP" in line:
                        self.game_running = False
                        self.update_status("Oyun Durdu", "#ff5555")
                        self.save_record()
                    elif "HIT" in line:
                        self.score += 1
                        self.update_score()
                    elif "MISS" in line:
                        self.missed += 1
                        self.update_missed()
        except serial.SerialException:
            messagebox.showerror("Hata", f"{PORT} bağlantısı bulunamadı veya açılamadı.")

    def update_status(self, text, color):
        self.status_label.config(text=f"Oyun Durumu: {text}", foreground=color)

    def update_score(self):
        self.score_label.config(text=f"Vurulan Hedefler: {self.score}")

    def update_missed(self):
        self.missed_label.config(text=f"Kaçırılan Hedefler: {self.missed}")

    def save_record(self):
        if not self.username:
            return
        rec = self.records.get(self.username, {"score": 0, "missed": 0, "games": 0})
        rec["score"] += self.score
        rec["missed"] += self.missed
        rec["games"] += 1
        self.records[self.username] = rec
        with open(DATA_FILE, "w") as f:
            json.dump(self.records, f, indent=2)

    def load_records(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        return {}

    def show_records(self):
        rec_window = tk.Toplevel(self)
        rec_window.title("Kayıtlar")
        rec_window.geometry("500x300")
        rec_window.configure(bg="#121212")

        style = ttk.Style(rec_window)
        style.theme_use('clam')
        style.configure("Treeview", background="#222222",
                        foreground="#e0e0e0", fieldbackground="#222222",
                        font=("Segoe UI", 11))
        style.map('Treeview', background=[('selected', '#009999')])

        columns = ("oyuncu", "toplam_skor", "kaçırılan", "oyun_sayısı")
        tree = ttk.Treeview(rec_window, columns=columns, show='headings')
        tree.heading("oyuncu", text="Oyuncu")
        tree.heading("toplam_skor", text="Toplam Skor")
        tree.heading("kaçırılan", text="Kaçırılanlar")
        tree.heading("oyun_sayısı", text="Oyun Sayısı")
        tree.column("oyuncu", anchor="center", width=150)
        tree.column("toplam_skor", anchor="center", width=100)
        tree.column("kaçırılan", anchor="center", width=100)
        tree.column("oyun_sayısı", anchor="center", width=100)
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        for user, rec in self.records.items():
            tree.insert("", "end", values=(user, rec["score"], rec["missed"], rec["games"]))

        close_btn = ttk.Button(rec_window, text="Kapat", command=rec_window.destroy)
        close_btn.pack(pady=10)


    def on_closing(self):
        self.serial_running = False
        self.destroy()


if __name__ == "__main__":
    app = LaserGameApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
