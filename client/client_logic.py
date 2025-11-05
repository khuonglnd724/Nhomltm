import socket
import json

HOST = '127.0.0.1'
PORT = 9009

class client_logic:
    def __init__(self):
        self.sock = None
        self.connected = False
        self.buffer = b""

    def connect(self, host=HOST, port=PORT):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self.connected = True

    def send_json(self, obj):
        if self.sock and self.connected:
            self.sock.sendall((json.dumps(obj) + "\n").encode('utf-8'))
            return True
        return False

    def recv_json(self):
        if not self.sock or not self.connected:
            return None
        try:
            while b"\n" not in self.buffer:
                part = self.sock.recv(4096)
                if not part:
                    self.connected = False
                    return None
                self.buffer += part
            line, sep, remaining = self.buffer.partition(b"\n")
            self.buffer = remaining
            return json.loads(line.decode('utf-8'))
        except:
            self.connected = False
            return None

    def disconnect(self):
        self.connected = False
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
                self.sock.close()
            except:
                pass
            finally:
                self.sock = None

    def is_connected(self):
        return self.connected and self.sock is not None
