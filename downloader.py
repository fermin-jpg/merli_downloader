import os
import re
import sys
import json
import time
import queue
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import requests
from bs4 import BeautifulSoup
import yt_dlp

# Target folders
APP_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEOS_DIR = os.path.join(os.path.expanduser('~'), 'Videos')
STATE_FILE = os.path.join(APP_DIR, "download_state.json")
CACHE_FILE = os.path.join(APP_DIR, "episodes_cache.json")

# Ensure video directory exists
os.makedirs(VIDEOS_DIR, exist_ok=True)

class MerliDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Merlí - Descargador Autónomo de Episodios v1.0.0 | Creado por Fermin32")
        self.root.geometry("900x650")
        self.root.configure(bg="#121214")
        
        # Ensure beautiful styling on Windows
        try:
            self.root.iconbitmap(default=None) # Can add icon later
        except:
            pass

        # State Variables
        self.episodes = []
        self.download_state = {}
        self.is_downloading = False
        self.current_download_index = -1
        self.stop_event = threading.Event()
        self.gui_queue = queue.Queue()
        
        # UI Styling Setup
        self.setup_styles()
        self.build_ui()
        
        # Load Cache first, then run scraper in background to verify/update
        self.load_cache_and_state()
        
        # Start background scraper if cache is empty or outdated
        if not self.episodes:
            self.status_var.set("Cargando lista de episodios desde 3Cat...")
            threading.Thread(target=self.scrape_episodes_bg, daemon=True).start()
        else:
            self.update_ui_lists()
            self.status_var.set("Listo para iniciar. Episodios cargados desde caché.")
            
        # Start queue poller
        self.root.after(100, self.poll_queue)

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Dark Theme Palette
        # bg_dark = #121214
        # bg_card = #1e1e24
        # fg_light = #cdd6f4
        # accent_blue = #3498db
        # accent_green = #2ecc71
        
        self.style.configure(".", bg="#121214", fg="#cdd6f4")
        
        # Frame styles
        self.style.configure("TFrame", background="#121214")
        self.style.configure("Card.TFrame", background="#1e1e24", relief="flat")
        
        # Treeview styling
        self.style.configure("Treeview", 
                             background="#1e1e24", 
                             foreground="#cdd6f4", 
                             fieldbackground="#1e1e24",
                             rowheight=35,
                             font=("Segoe UI", 10))
        self.style.configure("Treeview.Heading", 
                             background="#121214", 
                             foreground="#a5a5b4", 
                             font=("Segoe UI", 10, "bold"),
                             relief="flat")
        
        # Map selections to a sleek color
        self.style.map("Treeview", 
                      background=[('selected', '#313244')],
                      foreground=[('selected', '#f5c2e7')])
        
        # Styled Buttons
        self.style.configure("Primary.TButton", 
                             font=("Segoe UI", 11, "bold"), 
                             background="#2ecc71", 
                             foreground="#ffffff", 
                             borderwidth=0,
                             padding=10)
        self.style.map("Primary.TButton",
                      background=[('active', '#27ae60'), ('disabled', '#34495e')])
                      
        self.style.configure("Danger.TButton", 
                             font=("Segoe UI", 11, "bold"), 
                             background="#e74c3c", 
                             foreground="#ffffff", 
                             borderwidth=0,
                             padding=10)
        self.style.map("Danger.TButton",
                      background=[('active', '#c0392b')])
                      
        self.style.configure("Secondary.TButton", 
                             font=("Segoe UI", 10), 
                             background="#34495e", 
                             foreground="#ffffff", 
                             borderwidth=0,
                             padding=8)
        self.style.map("Secondary.TButton",
                      background=[('active', '#2c3e50')])

        # Progressbar
        self.style.configure("Sleek.Horizontal.TProgressbar", 
                             thickness=10, 
                             troughcolor="#1e1e24", 
                             background="#3498db",
                             relief="flat")

    def build_ui(self):
        # Main Layout: 3 sections (Header, Body, Footer)
        self.main_container = ttk.Frame(self.root, padding=20)
        self.main_container.pack(fill="both", expand=True)
        
        # 1. HEADER SECTION
        self.header_frame = ttk.Frame(self.main_container)
        self.header_frame.pack(fill="x", pady=(0, 20))
        
        # Title & Subtitle
        title_label = tk.Label(self.header_frame, 
                              text="MERLÍ", 
                              font=("Segoe UI", 26, "bold"), 
                              fg="#89b4fa", 
                              bg="#121214")
        title_label.pack(side="left", anchor="w")
        
        subtitle_label = tk.Label(self.header_frame, 
                                 text=" |  v1.0.0 by Fermin32", 
                                 font=("Segoe UI", 12, "bold"), 
                                 fg="#9898a6", 
                                 bg="#121214")
        subtitle_label.pack(side="left", anchor="s", pady=(0, 6))
        
        # Stats summary on the right
        self.stats_label = tk.Label(self.header_frame, 
                                   text="Cargando...", 
                                   font=("Segoe UI", 11, "bold"), 
                                   fg="#a6e3a1", 
                                   bg="#121214")
        self.stats_label.pack(side="right", anchor="e", pady=(0, 6))

        # 2. BODY SECTION (Horizontal split: Left list, Right controls/info)
        self.body_frame = ttk.Frame(self.main_container)
        self.body_frame.pack(fill="both", expand=True)
        
        # LEFT: Episode list in a custom styled frame
        list_card = ttk.Frame(self.body_frame, style="Card.TFrame")
        list_card.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        list_header = tk.Label(list_card, 
                               text="Lista de Capítulos (Temporadas 1, 2 y 3)", 
                               font=("Segoe UI", 11, "bold"), 
                               fg="#cdd6f4", 
                               bg="#1e1e24",
                               anchor="w",
                               padx=10, pady=10)
        list_header.pack(fill="x")
        
        # Treeview Scrollbar
        scroll = ttk.Scrollbar(list_card)
        scroll.pack(side="right", fill="y")
        
        # Treeview table
        self.tree = ttk.Treeview(list_card, 
                                 columns=("season_ep", "title", "status", "progress"), 
                                 show="headings", 
                                 yscrollcommand=scroll.set,
                                 style="Treeview")
        self.tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        scroll.config(command=self.tree.yview)
        
        # Headings definition
        self.tree.heading("season_ep", text="Capítulo")
        self.tree.heading("title", text="Título de Episodio")
        self.tree.heading("status", text="Estado")
        self.tree.heading("progress", text="Progreso")
        
        self.tree.column("season_ep", width=80, anchor="center")
        self.tree.column("title", width=350, anchor="w")
        self.tree.column("status", width=120, anchor="center")
        self.tree.column("progress", width=80, anchor="center")
        
        # Tags for colored statuses
        self.tree.tag_configure("pending", foreground="#a5a5b4")
        self.tree.tag_configure("downloading", foreground="#f9e2af", background="#2a2b36")
        self.tree.tag_configure("completed", foreground="#a6e3a1")
        self.tree.tag_configure("failed", foreground="#f38ba8")

        # RIGHT: Controls, Progress & Logs
        right_panel = ttk.Frame(self.body_frame, width=280)
        right_panel.pack(side="right", fill="both", padx=(10, 0))
        right_panel.pack_propagate(False) # Keep fixed width
        
        # Control card
        control_card = ttk.Frame(right_panel, style="Card.TFrame", padding=15)
        control_card.pack(fill="x", pady=(0, 15))
        
        tk.Label(control_card, 
                 text="Acciones", 
                 font=("Segoe UI", 12, "bold"), 
                 fg="#cdd6f4", 
                 bg="#1e1e24", 
                 anchor="w").pack(fill="x", pady=(0, 15))
        
        # Main Start / Stop Button
        self.btn_start = ttk.Button(control_card, 
                                    text="🚀 INICIAR", 
                                    style="Primary.TButton", 
                                    command=self.toggle_download)
        self.btn_start.pack(fill="x", pady=(0, 10))
        
        # Utility Buttons
        self.btn_open_folder = ttk.Button(control_card, 
                                          text="📁 Abrir Carpeta Videos", 
                                          style="Secondary.TButton", 
                                          command=self.open_videos_folder)
        self.btn_open_folder.pack(fill="x", pady=(0, 10))
        
        self.btn_reload = ttk.Button(control_card, 
                                     text="🔄 Buscar Episodios Web", 
                                     style="Secondary.TButton", 
                                     command=self.force_scrape)
        self.btn_reload.pack(fill="x")
        
        # Progress Card
        self.progress_card = ttk.Frame(right_panel, style="Card.TFrame", padding=15)
        self.progress_card.pack(fill="x", pady=(0, 15))
        
        tk.Label(self.progress_card, 
                 text="Descarga Actual", 
                 font=("Segoe UI", 12, "bold"), 
                 fg="#cdd6f4", 
                 bg="#1e1e24", 
                 anchor="w").pack(fill="x", pady=(0, 10))
        
        self.lbl_active_episode = tk.Label(self.progress_card, 
                                           text="Ningún capítulo activo", 
                                           font=("Segoe UI", 9, "bold"), 
                                           fg="#89b4fa", 
                                           bg="#1e1e24", 
                                           anchor="w", 
                                           wraplength=230,
                                           justify="left")
        self.lbl_active_episode.pack(fill="x", pady=(0, 10))
        
        self.progress_bar = ttk.Progressbar(self.progress_card, 
                                            style="Sleek.Horizontal.TProgressbar", 
                                            mode="determinate")
        self.progress_bar.pack(fill="x", pady=(0, 5))
        
        self.lbl_speed_percent = tk.Label(self.progress_card, 
                                           text="Progreso: 0.0%  |  Velocidad: ---", 
                                           font=("Segoe UI", 9), 
                                           fg="#a5a5b4", 
                                           bg="#1e1e24", 
                                           anchor="w")
        self.lbl_speed_percent.pack(fill="x")
        
        # Log / Logs Card
        log_card = ttk.Frame(right_panel, style="Card.TFrame", padding=15)
        log_card.pack(fill="both", expand=True)
        
        tk.Label(log_card, 
                 text="Consola de Estado", 
                 font=("Segoe UI", 11, "bold"), 
                 fg="#cdd6f4", 
                 bg="#1e1e24", 
                 anchor="w").pack(fill="x", pady=(0, 5))
        
        self.log_text = tk.Text(log_card, 
                                bg="#121214", 
                                fg="#a5a5b4", 
                                font=("Consolas", 8), 
                                bd=0, 
                                highlightthickness=0, 
                                wrap="word")
        self.log_text.pack(fill="both", expand=True)
        self.log_text.config(state="disabled")

        # 3. FOOTER SECTION
        self.footer_frame = ttk.Frame(self.main_container)
        self.footer_frame.pack(fill="x", pady=(15, 0))
        
        self.status_var = tk.StringVar(value="Cargando aplicación...")
        status_label = tk.Label(self.footer_frame, 
                                textvariable=self.status_var, 
                                font=("Segoe UI", 9), 
                                fg="#a5a5b4", 
                                bg="#121214", 
                                anchor="w")
        status_label.pack(side="left")
        
        path_label = tk.Label(self.footer_frame, 
                             text=f"Destino: {VIDEOS_DIR}", 
                             font=("Segoe UI", 9, "bold"), 
                             fg="#89b4fa", 
                             bg="#121214", 
                             anchor="e")
                             
        path_label.pack(side="right")

    # ================= STATE & CACHE MANAGEMENT =================
    def load_cache_and_state(self):
        # 1. Load episodes cache
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    self.episodes = json.load(f)
            except Exception as e:
                self.log(f"Error cargando caché de episodios: {e}")
                
        # 2. Load download state
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r', encoding='utf-8') as f:
                    self.download_state = json.load(f)
            except Exception as e:
                self.log(f"Error cargando estado de descarga: {e}")
                self.download_state = {}
        else:
            self.download_state = {}

    def save_state(self):
        try:
            with open(STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.download_state, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.log(f"Error guardando estado: {e}")

    def save_cache(self):
        try:
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.episodes, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.log(f"Error guardando caché de episodios: {e}")

    # ================= SCRAPER LOGIC =================
    def scrape_episodes_bg(self):
        urls = [
            "https://www.3cat.cat/3cat/merli/capitols/temporada/1/",
            "https://www.3cat.cat/3cat/merli/capitols/temporada/2/",
            "https://www.3cat.cat/3cat/merli/capitols/temporada/3/"
        ]
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        scraped_episodes = []
        
        def extract_items_recursive(obj):
            if isinstance(obj, dict):
                if 'items' in obj and isinstance(obj['items'], list):
                    items = obj['items']
                    if items and isinstance(items[0], dict) and 'nom_friendly' in items[0] and 'id' in items[0]:
                        return items
                for k, v in obj.items():
                    res = extract_items_recursive(v)
                    if res:
                        return res
            elif isinstance(obj, list):
                for item in obj:
                    res = extract_items_recursive(item)
                    if res:
                        return res
            return None

        self.gui_queue.put(("log", "Iniciando raspado de la web 3Cat..."))
        
        for idx, url in enumerate(urls, 1):
            self.gui_queue.put(("log", f"Raspando Temporada {idx}..."))
            try:
                r = requests.get(url, headers=headers)
                r.raise_for_status()
                soup = BeautifulSoup(r.text, 'html.parser')
                next_data = soup.find('script', id='__NEXT_DATA__')
                if next_data:
                    data = json.loads(next_data.string)
                    items = extract_items_recursive(data)
                    if items:
                        self.gui_queue.put(("log", f"¡Encontrados {len(items)} episodios en Temporada {idx}!"))
                        for item in items:
                            nom_friendly = item.get('nom_friendly')
                            video_id = str(item.get('id'))
                            title = item.get('titol') or item.get('permatitle') or f"S{idx} Ep"
                            
                            # Clean titles from standard typos
                            title = re.sub(r'T\d+xC\d+\s*-\s*', '', title) # Remove prefix T1xC1
                            
                            full_url = f"https://www.3cat.cat/3cat/{nom_friendly}/video/{video_id}/"
                            
                            scraped_episodes.append({
                                "season": idx,
                                "episode_num": item.get('capitol') or item.get('capitol_temporada') or len(scraped_episodes)+1,
                                "title": title,
                                "url": full_url,
                                "id": video_id
                            })
                    else:
                        self.gui_queue.put(("log", f"Advertencia: No se encontraron items en Temporada {idx}."))
                else:
                    self.gui_queue.put(("log", f"Advertencia: No se encontró NEXT_DATA en Temporada {idx}."))
            except Exception as e:
                self.gui_queue.put(("log", f"Error raspando temporada {idx}: {str(e)}"))

        if scraped_episodes:
            self.episodes = scraped_episodes
            self.save_cache()
            self.gui_queue.put(("scrape_complete", True))
        else:
            self.gui_queue.put(("scrape_failed", "No se pudo extraer ningún episodio de la web."))

    def force_scrape(self):
        if self.is_downloading:
            messagebox.showwarning("Acción no permitida", "No se puede recargar mientras hay descargas activas.")
            return
        
        self.btn_reload.config(state="disabled")
        self.status_var.set("Forzando recarga de episodios desde la web...")
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")
        threading.Thread(target=self.scrape_episodes_bg, daemon=True).start()

    # ================= UI UPDATER & POLLERS =================
    def update_ui_lists(self):
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        completed_count = 0
        
        # Populate
        for ep in self.episodes:
            video_id = ep['id']
            # Default state if not defined
            if video_id not in self.download_state:
                self.download_state[video_id] = "pending"
                
            status = self.download_state[video_id]
            
            # Format display
            season_ep = f"S{ep['season']}E{ep['episode_num']:02d}"
            title = ep['title']
            
            status_text = "Pendiente"
            progress_text = "---"
            tag = "pending"
            
            if status == "completed":
                status_text = "✅ Completado"
                progress_text = "100%"
                tag = "completed"
                completed_count += 1
            elif status == "downloading":
                status_text = "⏳ Grabando..."
                progress_text = "0%"
                tag = "downloading"
            elif status == "failed":
                status_text = "❌ Fallido"
                progress_text = "Error"
                tag = "failed"
                
            self.tree.insert("", "end", iid=video_id, values=(season_ep, title, status_text, progress_text), tags=(tag,))
            
        # Update Stats Overview
        total = len(self.episodes)
        pending = total - completed_count
        percent = (completed_count / total * 100) if total > 0 else 0
        
        self.stats_label.config(text=f"Progreso: {completed_count}/{total} cap. ({percent:.1f}%) | Quedan: {pending}")

    def log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def poll_queue(self):
        try:
            while True:
                msg_type, data = self.gui_queue.get_nowait()
                
                if msg_type == "log":
                    self.log(data)
                elif msg_type == "scrape_complete":
                    self.save_state() # Ensure states for new episodes are set
                    self.update_ui_lists()
                    self.status_var.set("Lista de episodios actualizada con éxito.")
                    self.btn_reload.config(state="normal")
                elif msg_type == "scrape_failed":
                    self.status_var.set(f"Error cargando lista: {data}")
                    messagebox.showerror("Error de conexión", f"Ocurrió un error al obtener la serie:\n{data}\n\nSe usará la caché local si está disponible.")
                    self.btn_reload.config(state="normal")
                elif msg_type == "progress":
                    # data is (percent, speed_str)
                    percent, speed = data
                    self.progress_bar['value'] = percent
                    self.lbl_speed_percent.config(text=f"Progreso: {percent:.1f}%  |  Velocidad: {speed}")
                    # Update Treeview progress
                    active_id = self.episodes[self.current_download_index]['id']
                    if self.tree.exists(active_id):
                        self.tree.set(active_id, "progress", f"{percent:.1f}%")
                elif msg_type == "download_started":
                    # data is (index, title)
                    idx, title = data
                    self.lbl_active_episode.config(text=title)
                    self.progress_bar['value'] = 0
                    self.status_var.set(f"Grabando capítulo {idx+1} de {len(self.episodes)}...")
                    # Update status in treeview
                    active_id = self.episodes[idx]['id']
                    if self.tree.exists(active_id):
                        self.tree.set(active_id, "status", "⏳ Grabando...")
                        self.tree.item(active_id, tags=("downloading",))
                elif msg_type == "download_finished":
                    # data is (index, success, error_msg)
                    idx, success, err = data
                    ep = self.episodes[idx]
                    video_id = ep['id']
                    
                    if success:
                        self.download_state[video_id] = "completed"
                        self.log(f"¡Capítulo S{ep['season']}E{ep['episode_num']:02d} completado!")
                    else:
                        self.download_state[video_id] = "failed"
                        self.log(f"Error en capítulo S{ep['season']}E{ep['episode_num']:02d}: {err}")
                        
                    self.save_state()
                    self.update_ui_lists()
                    
                    # Next episode or stop
                    if self.is_downloading and success:
                        self.download_next()
                    else:
                        self.stop_downloading_ui()
                        if not success and not self.stop_event.is_set():
                            messagebox.showerror("Error de Grabación", f"La grabación se detuvo debido a un error:\n{err}")
                            
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.poll_queue)

    # ================= DOWNLOAD CONTROLLER =================
    def toggle_download(self):
        if self.is_downloading:
            # STOP
            self.log("Deteniendo descargas... Por favor espera a que se cancele la conexión actual.")
            self.status_var.set("Cancelando descarga en curso...")
            self.stop_event.set()
            self.btn_start.config(state="disabled")
        else:
            # START
            if not self.episodes:
                messagebox.showwarning("Sin episodios", "La lista de episodios está vacía. Intenta recargar primero.")
                return
                
            self.is_downloading = True
            self.stop_event.clear()
            
            # Find next pending
            self.current_download_index = -1
            self.download_next()
            
            if self.current_download_index == -1:
                # All completed
                self.is_downloading = False
                messagebox.showinfo("Completado", "¡Todos los episodios ya han sido grabados con éxito!")
                return
                
            # Change UI to downloading state
            self.btn_start.config(text="🛑 DETENER", style="Danger.TButton")
            self.btn_reload.config(state="disabled")

    def download_next(self):
        if not self.is_downloading or self.stop_event.is_set():
            self.stop_downloading_ui()
            return
            
        # Find next pending
        next_idx = -1
        for i, ep in enumerate(self.episodes):
            video_id = ep['id']
            if self.download_state.get(video_id, "pending") != "completed":
                next_idx = i
                break
                
        if next_idx == -1:
            # Done!
            self.gui_queue.put(("log", "¡¡Toda la serie se ha grabado con éxito!!"))
            self.status_var.set("¡Todo grabado!")
            self.stop_downloading_ui()
            messagebox.showinfo("Felicidades", "¡Todos los capítulos de la serie han sido grabados de forma autónoma!")
            return
            
        self.current_download_index = next_idx
        ep = self.episodes[next_idx]
        
        # Start download thread
        threading.Thread(target=self.download_thread_worker, args=(next_idx,), daemon=True).start()

    def stop_downloading_ui(self):
        self.is_downloading = False
        self.btn_start.config(text="🚀 INICIAR", style="Primary.TButton", state="normal")
        self.btn_reload.config(state="normal")
        self.lbl_active_episode.config(text="Detenido")
        self.progress_bar['value'] = 0
        self.lbl_speed_percent.config(text="Progreso: 0.0%  |  Velocidad: ---")
        self.status_var.set("Descargas detenidas.")

    def download_thread_worker(self, index):
        ep = self.episodes[index]
        video_id = ep['id']
        url = ep['url']
        
        clean_title = re.sub(r'[\\/*?:"<>|]', "", ep['title'])
        filename = f"Merli - S{ep['season']:02d}E{ep['episode_num']:02d} - {clean_title}"
        filepath = os.path.join(VIDEOS_DIR, filename)
        
        # Notify start
        display_title = f"S{ep['season']}E{ep['episode_num']:02d} - {ep['title']}"
        self.gui_queue.put(("download_started", (index, display_title)))
        
        # Custom progress hook
        def ytdl_hook(d):
            if self.stop_event.is_set():
                raise Exception("Cancelled by user")
                
            if d['status'] == 'downloading':
                # Calculate percent
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                if total > 0:
                    percent = (downloaded / total) * 100
                else:
                    percent = 0.0
                    
                # Format speed
                speed = d.get('speed', 0)
                speed_str = "---"
                if speed:
                    if speed > 1024 * 1024:
                        speed_str = f"{speed / (1024*1024):.1f} MB/s"
                    else:
                        speed_str = f"{speed / 1024:.1f} KB/s"
                        
                self.gui_queue.put(("progress", (percent, speed_str)))
                
            elif d['status'] == 'finished':
                self.gui_queue.put(("progress", (100.0, "Guardando...")))

        ydl_opts = {
            'outtmpl': filepath + '.%(ext)s',
            'progress_hooks': [ytdl_hook],
            'quiet': True,
            'no_warnings': True,
            # Force standard single file best quality format that doesn't need merging
            'format': 'best',
            'retries': 20,              # Internal yt-dlp retries for network timeouts
            'fragment_retries': 20,
            'continuedl': True,         # Resume partially downloaded files
        }
        
        success = False
        error_msg = ""
        max_attempts = 4             # Application-level self-healing retry loop
        attempt = 0
        
        while attempt < max_attempts and not self.stop_event.is_set():
            attempt += 1
            if attempt > 1:
                self.gui_queue.put(("log", f"Reintentando descarga en 5 segundos... (Intento {attempt}/{max_attempts})"))
                for _ in range(50):  # Check for cancellation every 100ms
                    if self.stop_event.is_set():
                        break
                    time.sleep(0.1)
                if self.stop_event.is_set():
                    break
            
            self.gui_queue.put(("log", f"Iniciando descarga de: {display_title} (Intento {attempt}/{max_attempts})"))
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                success = True
                break
            except Exception as e:
                error_msg = str(e)
                # Clean up yt-dlp ANSI terminal colors from exception string (fixes visual bugs in UI)
                error_msg = re.sub(r'\x1b\[[0-9;]*m', '', error_msg)
                
                if "Cancelled by user" in error_msg or self.stop_event.is_set():
                    error_msg = "Detenido por el usuario"
                    break
                else:
                    self.gui_queue.put(("log", f"Fallo en intento {attempt}: {error_msg}"))
                    
        # Send finish message
        self.gui_queue.put(("download_finished", (index, success, error_msg)))

    # ================= UTILITIES =================
    def open_videos_folder(self):
        try:
            if sys.platform == "win32":
                os.startfile(VIDEOS_DIR)
            else:
                subprocess.Popen(["explorer", VIDEOS_DIR])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la carpeta:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MerliDownloaderApp(root)
    
    # Enable close button handling
    def on_closing():
        if app.is_downloading:
            if messagebox.askyesno("Salir", "¿Hay descargas en curso, seguro que quieres salir?"):
                app.stop_event.set()
                root.destroy()
        else:
            root.destroy()
            
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
