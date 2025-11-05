# test_clients.py
import socket
import random
import time
import threading
from logger import get_logger

HOST = '127.0.0.1'
PORT = 5555

moves = ["rock", "paper", "scissors"]
log = get_logger("TEST")

def client_simulator(id):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        log.info(f"[Client {id}] đã kết nối tới Server")

        time.sleep(2)   # đợi ghép cặp ở server

        for i in range(5): # test 5 lần
            move = random.choice(moves)
            msg = f"CHOICE:{move}"
            s.send(msg.encode("utf-8"))
            log.info(f"[Client {id}] gửi {msg}")

            response = s.recv(2048).decode('utf-8')
            log.info(f"[Client {id}] nhận về:\n{response}")

            time.sleep(1)

        s.close()
        log.info(f"[Client {id}] đóng kết nối")
    except Exception as e:
        log.error(f"[Client {id}] LỖI: {e}")

if __name__ == "__main__":
    threads = []
    for i in range(4):     # tạo 4 client test cùng lúc
        t = threading.Thread(target=client_simulator, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    print("=== TEST FINISHED ===")
    print("Log đã lưu vào file log ngày hôm nay")
