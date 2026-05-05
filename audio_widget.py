import tkinter as tk
from PIL import ImageGrab
import pyautogui
import threading
import time
import numpy as np
import pyaudio
import struct
import socket
from bridge_controller import bridge
import winsound # Thư viện mặc định của Windows để phát âm thanh nhanh

CHUNK = 1024 * 2             # Kích thước mẫu thử
FORMAT = pyaudio.paInt16     # Định dạng bit
CHANNELS = 1                 # Mono
RATE = 44100                 # Sampling rate

class InsightWidget:
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("250x150")
        self.root.attributes('-topmost', True, '-alpha', 0.8)
        self.root.overrideredirect(True)

        self.status_var = tk.StringVar(value="FREE")
        self.is_running = True # Biến điều khiển trạng thái các luồng
        self.setup_ui()

        # Dragging logic
        self.root.bind("<Button-1>", self.start_drag)
        self.root.bind("<B1-Motion>", self.do_drag)

        # 1. Khởi chạy Luồng Logic (Phân tích trạng thái)
        self.logic_thread = threading.Thread(target=self.main_loop, daemon=True)
        self.logic_thread.start()

        # 2. Khởi chạy Luồng Audio (Phân tích nhịp nhạc)
        self.audio_thread = threading.Thread(target=self.audio_analysis_thread, daemon=True)
        self.audio_thread.start()
    
    def start_music_session(self):
        self.bridge.send_command("LOCK_STATE") # Gửi lệnh khóa sang C#
        self.send_state_to_gremlin("PLAYING")
    
    def stop_widget(self):
        self.is_running = False
        # Giải phóng Agnes trước khi thoát[cite: 1]
        self.bridge.send_command("UNLOCK_STATE") 
        self.bridge.override_config("ALLOW_RANDOM_ACTIONS", True)
        self.root.destroy()

    # ### 4. Sơ đồ luồng hoạt động tổng thể
    # Quy trình kiểm soát luồng vận hành theo chu kỳ khép kín để đảm bảo tính mượt mà:

    # *   **Giai đoạn Bắt đầu**: Widget kết nối Bridge $\rightarrow$ Ghi đè cấu hình (`ALLOW_RANDOM_ACTIONS=False`) $\rightarrow$ Agnes tập trung vào Widget[cite: 1].
    # *   **Giai đoạn Hoạt động**: Widget gửi tọa độ (nếu cách biệt $> 125.0$ px) $\rightarrow$ Agnes di chuyển đuổi theo $\rightarrow$ Phân tích Audio $\rightarrow$ Khóa trạng thái và Nhảy[cite: 1].
    # *   **Giai đoạn Kết thúc**: Widget gửi lệnh Mở khóa $\rightarrow$ Khôi phục cấu hình mặc định $\rightarrow$ Agnes tự do thực hiện hành động ngẫu nhiên (IDLE/WALK)[cite: 1].

    # Việc tuân thủ nghiêm ngặt thứ tự: **Nạp dữ liệu (Mapping) $\rightarrow$ Khóa (Lock) $\rightarrow$ Thực thi $\rightarrow$ Giải phóng (Unlock)** sẽ giúp nhân vật Agnes trở thành một trợ lý ảo hoàn hảo trên màn hình của bạn[cite: 1].

    def trigger_context_response(self, state):
        """Ánh xạ trạng thái sang hành động và âm thanh cụ thể"""
        
        if state == "FREE":
            # Agnes tự do, không phát nhạc, cho phép hành động ngẫu nhiên
            bridge.override_config("ALLOW_RANDOM_ACTIONS", True)
            self.send_state_to_gremlin("FREE")

        elif state == "ANALYZING":
            # Phát âm thanh hover và chuyển Agnes sang tư thế quan sát
            winsound.PlaySound("assets/sounds/hover.wav", winsound.SND_ASYNC)
            self.send_state_to_gremlin("ANALYZING")

        elif state == "LOADING":
            # Agnes thực hiện động tác 'Grab' để chuẩn bị dữ liệu
            winsound.PlaySound("assets/sounds/intro.wav", winsound.SND_ASYNC)
            bridge.lock_state() # Khóa trạng thái để diễn xong intro
            self.send_state_to_gremlin("LOADING")
        
    def send_state_to_gremlin(self, state_name):
        """
        Đây là bước 'Đăng ký/Gửi tín hiệu'. 
        Nó báo cho SpriteManager biết cần dùng Key nào trong _fileNameMap.
        """
        self.status_var.set(state_name)
        print(f"[BRIDGE] Gửi trạng thái: {state_name}")
        
        # Mô phỏng Logic LockState theo yêu cầu:
        # Nếu đang PLAYING thì phải Lock để không nhảy sang IDLE ngẫu nhiên
        if state_name == "PLAYING":
            print("[C#] Execute: LockState()")
        elif state_name == "FREE":
            print("[C#] Execute: UnlockState()")
            
    def setup_ui(self):
        self.frame = tk.Frame(self.root, bg='#2c3e50', bd=2)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        self.label_title = tk.Label(self.frame, text="CONTEXT ANALYZER", fg="white", bg="#2c3e50", font=("Arial", 10, "bold"))
        self.label_title.pack(pady=5)
        
        self.status_label = tk.Label(self.frame, textvariable=self.status_var, fg="#3498db", bg="#2c3e50", font=("Arial", 14))
        self.status_label.pack(pady=10)

        self.btn_exit = tk.Button(self.frame, text="×", command=self.root.destroy, bg="#e74c3c", fg="white", bd=0)
        self.btn_exit.place(x=225, y=5, width=20, height=20)

    def start_drag(self, event):
        self.x = event.x
        self.y = event.y

    def do_drag(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")
        self.status_var.set("ANALYZING")

    def analyze_screen(self):
        """Captures the area behind the widget and detects 'context'"""
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        
        # Take a screenshot of the region
        screenshot = ImageGrab.grab(bbox=(x, y, x+w, y+h))
        # Simple Logic: Analyze dominant color or brightness
        img_np = np.array(screenshot)
        avg_color = np.mean(img_np, axis=(0, 1))
        
        # Placeholder for more complex logic (like OCR or Image Recognition)
        return avg_color
    
    def get_audio_intensity(self, data):
        """Xử lý RMS từ dữ liệu thô"""
        count = len(data) / 2
        format = "%dh" % (count)
        shorts = struct.unpack(format, data)
        samples = np.array(shorts).astype(float)
        return np.sqrt(np.mean(samples**2))

    def audio_analysis_thread(self):
        """Luồng bắt âm thanh hệ thống liên tục[cite: 1]"""
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, 
                        input=True, frames_per_buffer=2048)

        while self.is_running:
            try:
                if self.status_var.get() == "PLAYING":
                    data = stream.read(2048, exception_on_overflow=False)
                    intensity = self.get_audio_intensity(data)
                    
                    # Mapping logic dựa trên cường độ âm thanh[cite: 1]
                    if intensity < 500:
                        bridge.update_state("SLEEP") # Nhạc chậm[cite: 1]
                    elif intensity < 3000:
                        bridge.update_state("EMOTE1") # Nhạc vừa[cite: 1]
                    else:
                        bridge.update_state("EMOTE3") # Nhạc nhanh[cite: 1]
                time.sleep(0.1) # Giảm tải CPU
            except Exception as e:
                print(f"Audio Error: {e}")
                
    def sync_animation_to_audio(self, intensity):
        # Ngưỡng (Threshold) có thể điều chỉnh tùy theo âm lượng máy tính
        LOW_THRESHOLD = 500
        HIGH_THRESHOLD = 3000

        if intensity < LOW_THRESHOLD:
            # Nhạc rất nhỏ hoặc không nhạc: SLEEP (255 frames)
            self.bridge.send_state("SLEEP") 
        elif intensity < HIGH_THRESHOLD:
            # Nhạc vừa: EMOTE1 (42 frames - Mambo)
            self.bridge.send_state("EMOTE1")
        else:
            # Nhạc sôi động: EMOTE3 (189 frames)
            self.bridge.send_state("EMOTE3")
    
    def main_loop(self):
        """Vòng lặp điều khiển trạng thái Widget[cite: 1]"""
        while self.is_running:
            try:
                # FREE -> IDLE
                self.send_state_to_gremlin("FREE")
                time.sleep(3)

                # ANALYZING -> HOVER
                self.send_state_to_gremlin("ANALYZING")
                self.analyze_screen()
                time.sleep(2)

                # PLAYING -> Kích hoạt Audio Thread điều khiển tiếp
                self.send_state_to_gremlin("PLAYING")
                time.sleep(10) # Để nhạc phát trong 10 giây
                
            except Exception as e:
                print(f"Logic Error: {e}")
                
                # Giả lập bắt nhịp BPM
                mock_bpm = np.random.randint(60, 150)
                if mock_bpm > 100:
                    print(f"[AUDIO] BPM: {mock_bpm} -> Chuyển Agnes sang EMOTE1 (Quẩy)")
                else:
                    print(f"[AUDIO] BPM: {mock_bpm} -> Chuyển Agnes sang SLEEP")
                
                time.sleep(5) 
                
            except Exception as e:
                print(f"Error: {e}")
                break

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = InsightWidget()
    app.run()