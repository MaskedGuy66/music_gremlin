import socket;
import threading;
import json;

class BridgeController:
    def __init__(self, host='127.0.0.1', port=65432):
        self.host = host
        self.port = port
        self.is_locked  = False
        self.client.socket = None
        
        self.state_map = {
            "FREE": "IDLE",
            "ANALYZING": "HOVER",
            "LOADING": "GRAB",
            "PLAYING": "EMOTE1",
            "SLEEPING": "SLEEP"
        }
    def connect(self):
        try:
            self.client.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.socket.connect((self.host, self.port))
            print(f"Connected to Gremlin at {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"Failed to connect to Gremlin: {e}")
            return False
    def send_command(self, action, state_name=None):
        """
        Gửi dữ liệu JSON tới C#
        action: 'CHANGE_STATE', 'LOCK', 'UNLOCK'
        """
        if not self.client_socket:
            if not self.connect(): return

        data = {
            "action": action,
            "state": self.state_map.get(state_name, state_name) if state_name else None,
            "locked": self.is_locked
        }

        try:
            message = json.dumps(data) + "\n"
            self.client_socket.sendall(message.encode('utf-8'))
        except Exception as e:
            print(f"[BRIDGE] Lỗi gửi dữ liệu: {e}")
            self.client_socket = None # Reset để reconnect lần sau

    def update_state(self, new_state):
        """Logic xử lý trạng thái kèm cơ chế Lock"""
        
        # Nếu đang bị khóa (đang nhảy), không cho phép đổi sang trạng thái bình thường
        if self.is_locked and new_state != "FREE":
            print(f"[BRIDGE] Đang Lock: Bỏ qua lệnh chuyển sang {new_state}")
            return

        print(f"[BRIDGE] Processing: {new_state}")

        if new_state == "PLAYING":
            # Khi nhảy, thực hiện khóa để tránh IDLE chen ngang
            self.lock_state()
            self.send_command("CHANGE_STATE", "PLAYING")
            
        elif new_state == "FREE":
            # Khi kết thúc, mở khóa và trả về IDLE
            self.unlock_state()
            self.send_command("CHANGE_STATE", "FREE")
            
        else:
            # Các trạng thái trung gian (ANALYZING, LOADING)
            self.send_command("CHANGE_STATE", new_state)

    def lock_state(self):
        self.is_locked = True
        self.send_command("LOCK")
        print("[BRIDGE] Agnes is busy dancing... (LockState)")

    def unlock_state(self):
        self.is_locked = False
        self.send_command("UNLOCK")
        print("[BRIDGE] Agnes is free now. (UnlockState)")

    def close(self):
        if self.client_socket:
            self.client_socket.close()

# Singleton instance để audio_widget.py gọi dễ dàng
bridge = BridgeController()