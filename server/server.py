import socket
import threading
import json
from datetime import datetime

from game_manager import handle_move, match_players, clients, queue, matches, moves, lock
from leaderboard import update_score, save_leaderboard_file

HOST = '127.0.0.1'
PORT = 9009

def save_log(msg):
    """Lưu log vào file"""
    try:
        with open("game_log.txt", "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")
    except:
        pass

def send_json(client_socket, obj):
    """Gửi JSON tới client"""
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
                match_players()  # gọi trực tiếp hàm match_players từ game_manager

            elif msg_type == "move":
                move = msg.get("move")
                if move in ["rock", "paper", "scissors"]:
                    handle_move(client_socket, move)  # gọi trực tiếp

    finally:
        # Khi client ngắt kết nối
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
