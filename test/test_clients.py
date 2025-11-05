import socket
import json
import random
import time
import threading
import os
import sys

# === Cấu hình đường dẫn ===
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER_DIR = os.path.join(BASE_DIR, "server")
sys.path.append(SERVER_DIR)

from logger import get_logger

# === Cấu hình server ===
HOST = '127.0.0.1'
PORT = 9009  # phải khớp với server.py

MOVES = ["rock", "paper", "scissors"]
log = get_logger("TEST_CLIENT")

# === Hàm gửi/nhận JSON ===
def send_json(sock, obj):
    msg = json.dumps(obj) + "\n"
    sock.sendall(msg.encode("utf-8"))

def recv_json(sock):
    data = b""
    while b"\n" not in data:
        part = sock.recv(4096)
        if not part:
            return None
        data += part
    line, _, _ = data.partition(b"\n")
    return json.loads(line.decode("utf-8"))

# === Mô phỏng 1 client ===
def client_simulator(client_id):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        log.info(f"[Client {client_id}] Đã kết nối tới server.")

        # Gửi thông tin đăng nhập (hoặc tên người chơi)
        player_name = f"Tester_{client_id}"
        send_json(s, {"type": "login", "player": player_name})
        resp = recv_json(s)
        log.info(f"[Client {client_id}] Phản hồi login: {resp}")

        time.sleep(1)  # chờ ghép cặp hoặc server phản hồi

        # Gửi 5 lượt chơi
        for i in range(5):
            move = random.choice(MOVES)
            msg = {"type": "move", "choice": move}
            send_json(s, msg)
            log.info(f"[Client {client_id}] Gửi nước đi: {move}")

            response = recv_json(s)
            if response:
                log.info(f"[Client {client_id}] Nhận phản hồi: {response}")
            else:
                log.warning(f"[Client {client_id}] Không nhận được phản hồi!")

            time.sleep(random.uniform(1, 2))

        # Ngắt kết nối
        send_json(s, {"type": "logout"})
        s.close()
        log.info(f"[Client {client_id}] Đã ngắt kết nối.")
    except Exception as e:
        log.error(f"[Client {client_id}] LỖI: {e}")

# === Chạy nhiều client song song ===
if __name__ == "__main__":
    threads = []
    client_count = 4  # số client test cùng lúc

    for i in range(client_count):
        t = threading.Thread(target=client_simulator, args=(i,))
        threads.append(t)
        t.start()
        time.sleep(0.5)  # tạo độ trễ khi kết nối

    for t in threads:
        t.join()

    print("\n=== ✅ TEST FINISHED ===")
    print("→ Kết quả chi tiết được ghi trong file log ngày hôm nay.")