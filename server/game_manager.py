import json
from leaderboard import update_score

def send_json(conn, obj):
    conn.sendall((json.dumps(obj)+'\n').encode())

def recv_json(conn):
    data = b''
    while b'\n' not in data:
        part = conn.recv(4096)
        if not part: return None
        data += part
    line, _, _ = data.partition(b'\n')
    return json.loads(line.decode())

def calc_result(move1, move2):
    if move1 == move2:
        return "draw", "draw"
    rules = {"rock":"scissors", "scissors":"paper", "paper":"rock"}
    if rules[move1] == move2:
        return "win", "lose"
    else:
        return "lose", "win"

def handle_match(p1, p2):
    c1, n1 = p1
    c2, n2 = p2
    send_json(c1, {"type":"match_found", "opponent": n2})
    send_json(c2, {"type":"match_found", "opponent": n1})

    send_json(c1, {"type":"request_move"})
    send_json(c2, {"type":"request_move"})

    m1 = recv_json(c1)
    m2 = recv_json(c2)
    if not m1 or not m2:
        return

    move1 = m1["move"]
    move2 = m2["move"]
    r1, r2 = calc_result(move1, move2)

    send_json(c1, {"type":"round_result","your_move":move1,"opponent_move":move2,"result":r1})
    send_json(c2, {"type":"round_result","your_move":move2,"opponent_move":move1,"result":r2})

    # Cập nhật điểm
    update_score(n1, r1)
    update_score(n2, r2)
