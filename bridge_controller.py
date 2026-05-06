import socket
import threading
import json

class BridgeController:
    def __init__(self, host='127.0.0.1', port=65432):
        self.host = host
        self.port = port
        self.is_locked = False
        self.client_socket = None 
        self._lock = threading.Lock() 
        
        self.state_map = {
            "FREE": "IDLE",
            "ANALYZING": "HOVER",
            "LOADING": "GRAB",
            "PLAYING": "EMOTE1",
            "SLEEPING": "SLEEP"
        }

    def connect(self):
        if self.client_socket:
            return True
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(2.0)
            self.client_socket.connect((self.host, self.port))
            print(f"Connected to Gremlin at {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"Failed to connect to Gremlin: {e}")
            self.client_socket = None
            return False

    def send_command(self, action, state_name=None):
        with self._lock:
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
                print(f"[BRIDGE] Error sending data: {e}")
                self.close() 

    def update_state(self, new_state):
        if self.is_locked and new_state != "FREE":
            return

        if new_state == "PLAYING":
            self.lock_state()
            self.send_command("CHANGE_STATE", "PLAYING")
        elif new_state == "FREE":
            self.unlock_state()
            self.send_command("CHANGE_STATE", "FREE")
        else:
            self.send_command("CHANGE_STATE", new_state)

    def lock_state(self):
        self.is_locked = True
        self.send_command("LOCK")

    def unlock_state(self):
        self.is_locked = False
        self.send_command("UNLOCK")

    def override_config(self, key, value):
        # Added helper for configuration overrides
        self.send_command("OVERRIDE", f"{key}:{value}")

    def close(self):
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None

bridge = BridgeController()