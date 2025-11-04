import json
from leaderboard import update_score

def send_json(conn, obj):
    """Gửi dữ liệu JSON tới client"""
    conn.sendall((json.dumps(obj) + '\n').encode())

def recv_json(conn):
    """Nhận dữ liệu JSON từ client"""
    data = b''
    while b'\n' not in data:
        part = conn.recv(4096)
        if not part:
            return None
        data += part
    line, _, _ = data.partition(b'\n')
    return json.loads(line.decode())

def calc_result(move1, move2):
    """Tính kết quả giữa hai lượt chơi"""
    if move1 == move2:
        return "draw", "draw"

    rules = {"rock": "scissors", "scissors": "paper", "paper": "rock"}
    if rules[move1] == move2:
        return "win", "lose"
    else:
        return "lose", "win"

def handle_match(p1, p2):
    """Xử lý một trận đấu giữa 2 người chơi"""
    c1, n1 = p1  # socket và tên người chơi 1
    c2, n2 = p2  # socket và tên người chơi 2

    # Gửi thông báo tìm được đối thủ
    send_json(c1, {"type": "match_found", "opponent": n2})
    send_json(c2, {"type": "match_found", "opponent": n1})

    # Yêu cầu người chơi chọn
    send_json(c1, {"type": "request_move"})
    send_json(c2, {"type": "request_move"})

    # Nhận kết quả lựa chọn
    m1 = recv_json(c1)
    m2 = recv_json(c2)

    if not m1 or not m2:
        return

    move1 = m1["move"]
    move2 = m2["move"]

    # Tính kết quả thắng/thua/hòa
    r1, r2 = calc_result(move1, move2)

    # Gửi kết quả về cho cả hai
    send_json(c1, {
        "type": "round_result",
        "your_move": move1,
        "opponent_move": move2,
        "result": r1
    })
    send_json(c2, {
        "type": "round_result",
        "your_move": move2,
        "opponent_move": move1,
        "result": r2
    })

    # ✅ Cập nhật điểm cho leaderboard
    update_score(n1, r1)
    update_score(n2, r2)

    print(f"[INFO] Kết quả trận: {n1} ({r1}) vs {n2} ({r2})")
