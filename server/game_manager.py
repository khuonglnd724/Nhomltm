import threading
import json
from datetime import datetime
from leaderboard import update_score

lock = threading.Lock()
clients = {}   # {socket: player_name}
queue = []     # client chờ ghép cặp
matches = {}   # {socket: opponent_socket}
moves = {}     # {socket: move}


def save_log(msg: str):
    """Lưu log vào file"""
    try:
        with open("game_log.txt", "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")
    except:
        pass


def send_json(sock, obj):
    """Gửi dữ liệu JSON đến client"""
    try:
        sock.sendall((json.dumps(obj) + "\n").encode())
    except:
        pass


def recv_json(sock):
    """Nhận dữ liệu JSON từ client"""
    try:
        data = b""
        while b"\n" not in data:
            part = sock.recv(4096)
            if not part:
                return None
            data += part
        line, _, _ = data.partition(b"\n")
        return json.loads(line.decode())
    except:
        return None


def match_players():
    """Ghép 2 người chơi"""
    with lock:
        while len(queue) >= 2:
            p1 = queue.pop(0)
            p2 = queue.pop(0)
            matches[p1] = p2
            matches[p2] = p1
            p1_name = clients.get(p1, "Unknown")
            p2_name = clients.get(p2, "Unknown")
            send_json(p1, {"type": "match_found", "opponent": p2_name})
            send_json(p2, {"type": "match_found", "opponent": p1_name})
            print(f"[MATCH] {p1_name} vs {p2_name}")
            save_log(f"[MATCH] {p1_name} vs {p2_name}")

            # Yêu cầu chọn nước đi
            send_json(p1, {"type": "request_move"})
            send_json(p2, {"type": "request_move"})


def handle_move(player_sock, move):
    """Xử lý nước đi"""
    opponent_sock = matches.get(player_sock)
    if not opponent_sock:
        return

    player_name = clients.get(player_sock, "Unknown")
    opponent_name = clients.get(opponent_sock, "Unknown")

    with lock:
        moves[player_sock] = move
        if opponent_sock in moves:
            p_move = moves[player_sock]
            o_move = moves[opponent_sock]

            # Tính kết quả
            if p_move == o_move:
                p_result = o_result = "draw"
            elif (p_move == "rock" and o_move == "scissors") or \
                 (p_move == "scissors" and o_move == "paper") or \
                 (p_move == "paper" and o_move == "rock"):
                p_result, o_result = "win", "lose"
            else:
                p_result, o_result = "lose", "win"

            # Gửi kết quả
            send_json(player_sock, {
                "type": "round_result",
                "your_move": p_move,
                "opponent_move": o_move,
                "result": p_result})
            
            send_json(opponent_sock, {
                "type": "round_result",
                "your_move": o_move,
                "opponent_move": p_move,
                "result": o_result})

            log_msg = f"{player_name}({p_move}) vs {opponent_name}({o_move}) => P1:{p_result}, P2:{o_result}"
            print(f"[RESULT] {log_msg}")
            save_log(log_msg)

            # Cập nhật leaderboard
            update_score(player_name, p_result)
            update_score(opponent_name, o_result)

            # Gọi hàm lưu file
            from leaderboard import save_leaderboard_file
            save_leaderboard_file()

            # Xóa moves
            del moves[player_sock]
            del moves[opponent_sock]