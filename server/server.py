import socket
import threading
from datetime import datetime

HOST = '127.0.0.1'
PORT = 5555

clients = []         # Danh sách client đang chờ
rooms = []           # Danh sách bàn chơi [(player1, player2)]
lock = threading.Lock()

# ========== HÀM XỬ LÝ TRẬN ĐẤU ==========
def determine_winner(choice1, choice2):
    if choice1 == choice2:
        return "Hòa!"
    elif (choice1 == "rock" and choice2 == "scissors") or \
         (choice1 == "scissors" and choice2 == "paper") or \
         (choice1 == "paper" and choice2 == "rock"):
        return "Người chơi 1 thắng!"
    else:
        return "Người chơi 2 thắng!"

# ========== GHI LOG ==========
def save_log(msg):
    with open("game_log.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")

# ========== GỬI TIN NHẮN ==========
def send(client, msg):
    try:
        client.sendall(msg.encode('utf-8'))
    except:
        pass

# ========== XỬ LÝ MỘT TRẬN ĐẤU ==========
def play_game(p1_socket, p2_socket, p1_addr, p2_addr):
    send(p1_socket, f"\n✅ Đã ghép cặp với {p2_addr}. Hãy chọn Kéo – Búa – Bao.")
    send(p2_socket, f"\n✅ Đã ghép cặp với {p1_addr}. Hãy chọn Kéo – Búa – Bao.")

    choices = {}

    while True:
        for player_socket, addr, idx in [(p1_socket, p1_addr, 1), (p2_socket, p2_addr, 2)]:
            try:
                data = player_socket.recv(1024).decode('utf-8')
                if not data:
                    raise ConnectionError
                if data.startswith("CHOICE:"):
                    choice = data.split(":")[1]
                    choices[idx] = choice
                    print(f"[NHẬN] {addr} chọn {choice}")
            except:
                send(p1_socket, f"❌ {addr} đã rời trận.")
                send(p2_socket, f"❌ {addr} đã rời trận.")
                return

        if len(choices) == 2:
            c1, c2 = choices[1], choices[2]
            result = determine_winner(c1, c2)
            msg = f"\n--- KẾT QUẢ TRẬN ---\n" \
                  f"Người chơi 1 ({p1_addr}): {c1}\n" \
                  f"Người chơi 2 ({p2_addr}): {c2}\n" \
                  f"=> {result}\n"
            send(p1_socket, msg)
            send(p2_socket, msg)
            save_log(msg)
            choices.clear()
            send(p1_socket, "Trận mới! Hãy chọn lại.")
            send(p2_socket, "Trận mới! Hãy chọn lại.")

# ========== XỬ LÝ CLIENT ==========
def handle_client(client_socket, addr):
    send(client_socket, "🟢 Kết nối thành công tới server Rock-Paper-Scissors!\nVui lòng chờ ghép cặp...\n")
    print(f"[KẾT NỐI] Client {addr} đã tham gia.")
    save_log(f"Client {addr} đã tham gia.")

    with lock:
        clients.append((client_socket, addr))

        # Nếu đủ 2 người thì tạo bàn chơi
        if len(clients) >= 2:
            p1_socket, p1_addr = clients.pop(0)
            p2_socket, p2_addr = clients.pop(0)
            rooms.append((p1_addr, p2_addr))
            print(f"[GHÉP CẶP] {p1_addr} vs {p2_addr}")
            save_log(f"[GHÉP CẶP] {p1_addr} vs {p2_addr}")
            threading.Thread(target=play_game, args=(p1_socket, p2_socket, p1_addr, p2_addr), daemon=True).start()

# ========== KHỞI ĐỘNG SERVER ==========
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[MÁY CHỦ] Đang lắng nghe tại {HOST}:{PORT}")

    while True:
        client_socket, addr = server.accept()
        threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True).start()

if __name__ == "__main__":
    start_server()
