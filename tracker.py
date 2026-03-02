import pyautogui
import requests
import sys  # Required for Mac detection
import time
import os
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import threading
import random
import tempfile
from PIL import Image, ImageTk
from pynput import mouse, keyboard

# --- CONFIG ---
URL = "https://gjwxzydjkeyundcjyrpi.supabase.co/storage/v1/object/screenshots/"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imdqd3h6eWRqa2V5dW5kY2p5cnBpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE0OTMxMjEsImV4cCI6MjA4NzA2OTEyMX0.05xpngSzUk4inTeb_QCUBiTaqlvsDUEYHGTB6S99bcg"
VALID_PASSWORD = "1214"

class TrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("504 Digital - Pro Tracker")
        self.root.geometry("500x850") 
        self.root.configure(bg='#0f172a')
        
        # --- MAC PERMISSION CHECK ---
        if sys.platform == 'darwin': 
            self.check_mac_permissions()
        
        self.account_id = None
        self.is_tracking = False
        self.is_paused = False
        
        self.session_seconds = 0
        self.day_seconds = 0
        self.week_seconds = 0
        
        self.last_activity_time = time.time()
        self.next_capture_in = random.randint(240, 360) 
        
        self.setup_login_ui()
        self.start_activity_listeners()

    def check_mac_permissions(self):
        """MacOS specific permission handling"""
        try:
            # Trigger the Mac system popup for Screen Recording
            pyautogui.screenshot()
        except:
            pass

    def start_activity_listeners(self):
        def on_activity(*args):
            self.last_activity_time = time.time()
        self.m_listener = mouse.Listener(on_click=on_activity, on_move=on_activity)
        self.k_listener = keyboard.Listener(on_press=on_activity)
        self.m_listener.start()
        self.k_listener.start()

    def format_time(self, seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    def setup_login_ui(self):
        self.clear_window()
        tk.Label(self.root, text="504 DIGITAL", font=("Impact", 40), fg="#22d3ee", bg="#0f172a").pack(pady=(60, 5))
        frame = tk.Frame(self.root, bg="#1e293b", padx=30, pady=30)
        frame.pack(pady=40)
        
        tk.Label(frame, text="ACCOUNT ID", fg="#38bdf8", bg="#1e293b", font=("Arial", 8, "bold")).pack(anchor="w")
        self.acc_entry = tk.Entry(frame, width=30, font=("Arial", 12), bg="#0f172a", fg="white", insertbackground="white", borderwidth=0)
        self.acc_entry.pack(pady=(5, 15))
        
        tk.Label(frame, text="PASSWORD", fg="#38bdf8", bg="#1e293b", font=("Arial", 8, "bold")).pack(anchor="w")
        self.pass_entry = tk.Entry(frame, show="*", width=30, font=("Arial", 12), bg="#0f172a", fg="white", insertbackground="white", borderwidth=0)
        self.pass_entry.pack(pady=5)
        
        tk.Button(self.root, text="START MISSION", command=self.login, bg="#22d3ee", fg="#0f172a", font=("Arial", 11, "bold"), width=25, bd=0, cursor="hand2").pack(pady=20)

    def setup_dashboard(self):
        self.clear_window()
        
        self.clock_label = tk.Label(self.root, text="", font=("Arial", 10), fg="#94a3b8", bg="#0f172a")
        self.clock_label.pack(pady=10)

        stats_container = tk.Frame(self.root, bg="#1e293b", padx=20, pady=20)
        stats_container.pack(fill="x", padx=30)

        self.session_label = tk.Label(stats_container, text="00:00:00", font=("Consolas", 36, "bold"), fg="white", bg="#1e293b")
        self.session_label.pack()
        tk.Label(stats_container, text="SESSION TIME", font=("Arial", 8, "bold"), fg="#22d3ee", bg="#1e293b").pack()

        lower_stats = tk.Frame(stats_container, bg="#1e293b", pady=15)
        lower_stats.pack(fill="x")
        
        self.day_label = tk.Label(lower_stats, text="Day: 00:00:00", font=("Arial", 9, "bold"), fg="#f8fafc", bg="#1e293b")
        self.day_label.pack(side="left", expand=True)
        
        self.week_label = tk.Label(lower_stats, text="Week: 00:00:00", font=("Arial", 9, "bold"), fg="#f8fafc", bg="#1e293b")
        self.week_label.pack(side="right", expand=True)

        tk.Label(self.root, text="LAST SYNC PREVIEW", font=("Arial", 8, "bold"), fg="#64748b", bg="#0f172a").pack(pady=(20, 5))
        
        self.preview_frame = tk.Frame(self.root, bg="#334155", padx=2, pady=2)
        self.preview_frame.pack(padx=20)
        
        self.preview_label = tk.Label(self.preview_frame, text="Awaiting first sync...", bg="#020617", width=55, height=14, fg="#475569")
        self.preview_label.pack()
        
        self.sync_info = tk.Label(self.root, text="Auto-sync in: --:--", font=("Arial", 9), fg="#94a3b8", bg="#0f172a")
        self.sync_info.pack(pady=10)

        tk.Button(self.root, text="SYNC NOW", command=self.perform_capture, bg="#0ea5e9", fg="white", width=30, font=("Arial", 9, "bold"), bd=0).pack(pady=5)
        
        self.pause_btn = tk.Button(self.root, text="PAUSE TRACKING", command=self.toggle_pause, bg="#334155", fg="white", width=30, font=("Arial", 10, "bold"), bd=0, pady=12)
        self.pause_btn.pack(pady=5)
        
        tk.Button(self.root, text="SIGN OUT", command=self.sign_out, bg="#ef4444", fg="white", width=30, font=("Arial", 10, "bold"), bd=0, pady=10).pack(pady=5)

        threading.Thread(target=self.main_loop, daemon=True).start()

    def main_loop(self):
        while self.is_tracking:
            now = datetime.now()
            self.clock_label.config(text=now.strftime("%A, %b %d %Y | %I:%M:%S %p"))

            if not self.is_paused:
                if time.time() - self.last_activity_time > 600:
                    self.is_paused = True
                    self.root.after(0, lambda: messagebox.showinfo("On Break", "System idle for 10 minutes.\nTracking paused."))
                
                self.session_seconds += 1
                self.day_seconds += 1
                self.week_seconds += 1
                
                self.session_label.config(text=self.format_time(self.session_seconds))
                self.day_label.config(text=f"Day: {self.format_time(self.day_seconds)}")
                self.week_label.config(text=f"Week: {self.format_time(self.week_seconds)}")

                if self.next_capture_in <= 0:
                    self.perform_capture()
                    self.next_capture_in = random.randint(240, 360)
                
                self.next_capture_in -= 1
                m, s = divmod(self.next_capture_in, 60)
                self.sync_info.config(text=f"Auto-sync in {m:02d}:{s:02d}")
            
            time.sleep(1)

    def perform_capture(self):
        def task():
            try:
                temp_dir = tempfile.gettempdir()
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                local_path = os.path.join(temp_dir, f"504_shot_{timestamp}.png")
                
                pic = pyautogui.screenshot()
                pic.save(local_path)
                
                with Image.open(local_path) as img:
                    img.thumbnail((400, 225))
                    photo = ImageTk.PhotoImage(img)
                    self.preview_label.config(image=photo, text="", width=400, height=225)
                    self.preview_label.image = photo 

                cloud_fn = f"{self.account_id}_{timestamp}.png"
                with open(local_path, 'rb') as f:
                    headers = {"Authorization": f"Bearer {KEY}", "apikey": KEY}
                    requests.post(f"{URL}{self.account_id}/{cloud_fn}", headers=headers, data=f)
                
                self.root.after(2000, lambda: self.safe_delete(local_path))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showwarning("Sync Warning", f"Permission error: {e}"))
        
        threading.Thread(target=task, daemon=True).start()

    def safe_delete(self, path):
        try:
            if os.path.exists(path): os.remove(path)
        except: pass

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        self.pause_btn.config(text="RESUME" if self.is_paused else "PAUSE TRACKING", bg="#10b981" if self.is_paused else "#334155")
        if not self.is_paused: self.last_activity_time = time.time()

    def login(self):
        u = self.acc_entry.get().upper()
        if u.startswith("504-DS-") and self.pass_entry.get() == VALID_PASSWORD:
            self.account_id = u
            self.is_tracking = True
            self.setup_dashboard()
        else:
            messagebox.showerror("Error", "Access Denied")

    def sign_out(self):
        if messagebox.askyesno("Exit", "Stop tracking and log out?"):
            self.is_tracking = False
            self.setup_login_ui()

    def clear_window(self):
        for w in self.root.winfo_children(): w.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = TrackerApp(root)
    root.mainloop()