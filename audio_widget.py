import tkinter as tk
from PIL import Image, ImageTk
import threading
import time
import numpy as np
import pyaudio
import struct
import os

class AgnesIntegratedVisualizer:
    def __init__(self, sprite_dir):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-transparentcolor", "black")
        self.root.geometry("300x300+100+100")

        self.sprite_dir = sprite_dir
        self.frame_dim = 300
        self.columns = 10
        
        # State & Animation Setup
        self.status = "FREE"
        self.active_anim = "FREE" # FIXED: Initialize attribute here to prevent AttributeError
        self.current_frame = 0
        self.sprite_cache = {}
        self.is_running = True

        self.animations = {
            "FREE": {"file": "idle", "frames": 340},
            "ANALYZE": {"file": "hover", "frames": 30},
            "LOADING": {"file": "grab", "frames": 40},
            "PLAYING_LOW": {"file": "sleep", "frames": 255},
            "PLAYING_MED": {"file": "emote1", "frames": 42},
            "PLAYING_HIGH": {"file": "emote3", "frames": 189}
        }

        # UI Components
        self.canvas = tk.Canvas(self.root, width=300, height=300, bg="black", highlightthickness=0)
        self.canvas.pack()
        
        # Beat Visualizer (Pulsing Circle behind Agnes)
        self.viz_circle = self.canvas.create_oval(150, 150, 150, 150, outline="#3498db", width=2)
        self.sprite_obj = self.canvas.create_image(0, 0, anchor="nw")

        # Interaction Bindings
        self.canvas.bind("<Button-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.do_drag)
        self.canvas.bind("<ButtonRelease-1>", self.end_drag)

        # Start Threads
        threading.Thread(target=self.audio_thread, daemon=True).start()
        self.animate()

    def start_drag(self, event):
        self.status = "ANALYZE"
        self.drag_x, self.drag_y = event.x, event.y

    def do_drag(self, event):
        x = self.root.winfo_x() + (event.x - self.drag_x)
        y = self.root.winfo_y() + (event.y - self.drag_y)
        self.root.geometry(f"+{x}+{y}")

    def end_drag(self, event):
        self.status = "LOADING"
        # Simulate loading then transition to PLAYING
        self.root.after(2000, lambda: setattr(self, 'status', 'PLAYING'))

    def get_frame(self, anim_key, frame_idx):
        anim = self.animations.get(anim_key, self.animations["FREE"])
        filename = anim["file"]
        
        if filename not in self.sprite_cache:
            path = os.path.join(self.sprite_dir, f"{filename}.png")
            if not os.path.exists(path): return None
            self.sprite_cache[filename] = Image.open(path)

        sheet = self.sprite_cache[filename]
        col, row = frame_idx % self.columns, frame_idx // self.columns
        frame = sheet.crop((col*300, row*300, (col+1)*300, (row+1)*300))
        return ImageTk.PhotoImage(frame)

    def audio_thread(self):
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
        while self.is_running:
            try:
                data = stream.read(1024, exception_on_overflow=False)
                shorts = struct.unpack("%dh" % (len(data)/2), data)
                rms = np.sqrt(np.mean(np.array(shorts).astype(float)**2))
                
                # Update visualizer circle size based on volume
                radius = int(min(140, 50 + (rms / 50))) 
                self.canvas.coords(self.viz_circle, 150-radius, 150-radius, 150+radius, 150+radius)
                self.canvas.itemconfig(self.viz_circle, outline=self.get_viz_color(rms))

                if self.status == "PLAYING":
                    if rms < 500: self.active_anim = "PLAYING_LOW"
                    elif rms < 3000: self.active_anim = "PLAYING_MED"
                    else: self.active_anim = "PLAYING_HIGH"
                else:
                    self.active_anim = self.status
            except: pass
            time.sleep(0.02)

    def get_viz_color(self, rms):
        if rms > 3000: return "#e74c3c" # Red for high intensity
        if rms > 500: return "#2ecc71"  # Green for mid
        return "#3498db"                # Blue for quiet

    def animate(self):
        anim_data = self.animations.get(self.active_anim, self.animations["FREE"])
        self.current_frame = (self.current_frame + 1) % anim_data["frames"]
        
        photo = self.get_frame(self.active_anim, self.current_frame)
        if photo:
            self.canvas.itemconfig(self.sprite_obj, image=photo)
            self.canvas.image = photo
        
        # Faster framerate for smoother dancing (~30fps)
        self.root.after(33, self.animate)

if __name__ == "__main__":
    # Ensure path points to your Agnes folder
    PATH = r"SpriteSheet\Gremlins\Agnes" 
    app = AgnesIntegratedVisualizer(PATH)
    app.root.mainloop()