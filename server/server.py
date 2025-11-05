import socket
import threading
import json
from datetime import datetime

HOST = '127.0.0.1'
PORT = 9009

clients = {}     # {socket: player_name}
queue = []       # Danh sách client đang chờ ghép cặp
matches = {}     # {socket: opponent_socket}
moves = {}       # {socket: move}
lock = threading.Lock()


def save_log(msg):
    """Lưu log vào file"""
    try:
        with open("game_log.txt", "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")
    except:
        pass


def send_json(client_socket, obj):
    """Gửi dữ liệu JSON đến client"""
    try:
        client_socket.sendall((json.dumps(obj) + "\n").encode())
        return True
    except:
        return False


def recv_json(client_socket):
    """Nhận JSON từ client"""
    try:
        data = b""
        while b"\n" not in data:
            part = client_socket.recv(4096)
            if not part:
                return None
            data += part
        line, _, _ = data.partition(b"\n")
        return json.loads(line.decode())
    except:
        return None


def match_players():
    """Ghép 2 người chơi vào trận đấu"""
    with lock:
        if len(queue) >= 2:
            p1_socket = queue.pop(0)
            p2_socket = queue.pop(0)
            matches[p1_socket] = p2_socket
            matches[p2_socket] = p1_socket
            p1_name = clients.get(p1_socket, "Unknown")
            p2_name = clients.get(p2_socket, "Unknown")
            send_json(p1_socket, {"type": "match_found", "opponent": p2_name})
            send_json(p2_socket, {"type": "match_found", "opponent": p1_name})
            print(f"[MATCH] {p1_name} vs {p2_name}")
            save_log(f"[MATCH] {p1_name} vs {p2_name}")
            # Yêu cầu chọn nước đi
            send_json(p1_socket, {"type": "request_move"})
            send_json(p2_socket, {"type": "request_move"})


def handle_move(player_socket, move):
    """Xử lý nước đi"""
    opponent_socket = matches.get(player_socket)
    if not opponent_socket:
        return
    player_name = clients.get(player_socket, "Unknown")
    opponent_name = clients.get(opponent_socket, "Unknown")

    with lock:
        moves[player_socket] = move
        if opponent_socket in moves:
            p_move = moves[player_socket]
            o_move = moves[opponent_socket]

            # Xác định kết quả
            if p_move == o_move:
                p_result = o_result = "draw"
            elif (p_move == "rock" and o_move == "scissors") or \
                 (p_move == "scissors" and o_move == "paper") or \
                 (p_move == "paper" and o_move == "rock"):
                p_result, o_result = "win", "lose"
            else:
                p_result, o_result = "lose", "win"

            # Gửi kết quả trước
            send_json(player_socket, {"type": "round_result", "result": p_result,
                                      "your_move": p_move, "opponent_move": o_move})
            send_json(opponent_socket, {"type": "round_result", "result": o_result,
                                        "your_move": o_move, "opponent_move": p_move})

            log_msg = f"{player_name}({p_move}) vs {opponent_name}({o_move}) => P1:{p_result}, P2:{o_result}"
            print(f"[RESULT] {log_msg}")
            save_log(log_msg)

            # Xóa moves đã chơi
            del moves[player_socket]
            del moves[opponent_socket]

            # Gửi yêu cầu vòng mới
            send_json(player_socket, {"type": "request_move"})
            send_json(opponent_socket, {"type": "request_move"})


def handle_client(client_socket, addr):
    """Xử lý client"""
    print(f"[CONNECT] {addr} connected")
    player_name = None
    try:
        while True:
            msg = recv_json(client_socket)
            if not msg:
                break
            msg_type = msg.get("type")
            if msg_type == "join":
                player_name = msg.get("player", f"Player_{addr[1]}")
                with lock:
                    clients[client_socket] = player_name
                print(f"[JOIN] {player_name} from {addr}")
                save_log(f"{player_name} joined from {addr}")
            elif msg_type == "join_queue":
                with lock:
                    if client_socket not in queue:
                        queue.append(client_socket)
                match_players()
            elif msg_type == "move":
                move = msg.get("move")
                if move in ["rock", "paper", "scissors"]:
                    handle_move(client_socket, move)
    finally:
        with lock:
            if client_socket in queue:
                queue.remove(client_socket)
            if client_socket in matches:
                opp = matches[client_socket]
                send_json(opp, {"type": "game_over"})
                if opp in matches:
                    del matches[opp]
                del matches[client_socket]
            if client_socket in moves:
                del moves[client_socket]
            if client_socket in clients:
                del clients[client_socket]
        client_socket.close()
        print(f"[DISCONNECT] {player_name or addr}")


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    print(f"[SERVER] Running on {HOST}:{PORT}")
    save_log("Server started")
    try:
        while True:
            client_socket, addr = server.accept()
            threading.Thread(target=handle_client, args=(client_socket, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("[SERVER] Shutting down...")
        save_log("Server stopped")
        server.close()


if __name__ == "__main__":
    start_server()
