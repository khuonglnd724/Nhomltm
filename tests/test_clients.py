import socket
import json
import random
import time
import threading

HOST = '127.0.0.1'
PORT = 9009

MOVES = ["rock", "paper", "scissors"]

def send_json(sock, obj):
    """Gửi JSON tới server"""
    try:
        sock.sendall((json.dumps(obj) + "\n").encode("utf-8"))
        return True
    except Exception as e:
        return False

def recv_json(sock):
    """Nhận JSON từ server"""
    try:
        sock.settimeout(5)  # Timeout 5s cho mỗi lần recv
        data = b""
        while b"\n" not in data:
            part = sock.recv(4096)
            if not part:
                return None
            data += part
        line, _, _ = data.partition(b"\n")
        return json.loads(line.decode("utf-8"))
    except socket.timeout:
        return {"type": "timeout"}
    except Exception as e:
        return None

def client_simulator(client_id):
    """Mô phỏng một client chơi game"""
    s = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        print(f"[Client {client_id}] ✅ Kết nối thành công!")

        player_name = f"Tester_{client_id}"
        
        # Bước 1: Gửi yêu cầu join
        if not send_json(s, {"type": "join", "player": player_name}):
            print(f"[Client {client_id}] ❌ Không thể gửi join")
            return
        print(f"[Client {client_id}] 📝 Đã join với tên: {player_name}")
        
        time.sleep(0.1)

        # Bước 2: Join queue để chờ ghép cặp
        if not send_json(s, {"type": "join_queue"}):
            print(f"[Client {client_id}] ❌ Không thể join queue")
            return
        print(f"[Client {client_id}] ⏳ Đang chờ ghép cặp...")

        rounds_played = 0
        consecutive_timeouts = 0
        match_started = False
        max_rounds = 10  # Chơi tối đa 10 round

        # Vòng lặp nhận message từ server
        while consecutive_timeouts < 3 and rounds_played < max_rounds:
            resp = recv_json(s)
            
            if resp is None:
                print(f"[Client {client_id}] ❌ Mất kết nối với server")
                break

            msg_type = resp.get("type")

            if msg_type == "timeout":
                consecutive_timeouts += 1
                print(f"[Client {client_id}] ⏱️ Timeout {consecutive_timeouts}/3 - Đang chờ...")
                
                # Nếu đã match nhưng timeout, có thể server đang xử lý
                if match_started and rounds_played > 0:
                    print(f"[Client {client_id}] ✅ Đã chơi {rounds_played} lượt, kết thúc game")
                    break
                continue

            # Reset timeout counter khi nhận được message
            consecutive_timeouts = 0

            if msg_type == "match_found":
                opponent = resp.get("opponent", "Unknown")
                print(f"[Client {client_id}] 🎮 Ghép cặp với: {opponent}")
                match_started = True

            elif msg_type == "request_move":
                # Server yêu cầu gửi nước đi
                move = random.choice(MOVES)
                if send_json(s, {"type": "move", "move": move}):
                    print(f"[Client {client_id}] ✊ Gửi nước đi: {move}")
                else:
                    print(f"[Client {client_id}] ❌ Không thể gửi nước đi")
                    break

            elif msg_type == "round_result":
                result = resp.get("result", "unknown")
                your_move = resp.get("your_move", "?")
                opponent_move = resp.get("opponent_move", "?")
                rounds_played += 1
                
                # In kết quả với emoji
                emoji = "🏆" if result == "win" else "💀" if result == "lose" else "🤝"
                print(f"[Client {client_id}] {emoji} Lượt {rounds_played}: {result.upper()} | Bạn: {your_move} vs Đối thủ: {opponent_move}")
                
                # Sau round_result, chờ request_move tiếp theo hoặc game_over
                # Nếu không có gì sau 5s thì coi như game kết thúc

            elif msg_type == "game_over":
                winner = resp.get("winner", "Unknown")
                your_score = resp.get("your_score", 0)
                opponent_score = resp.get("opponent_score", 0)
                print(f"[Client {client_id}] 🎯 GAME OVER! Winner: {winner} | Score: {your_score}-{opponent_score}")
                break

            elif msg_type == "opponent_disconnected":
                print(f"[Client {client_id}] ⚠️ Đối thủ đã ngắt kết nối")
                break

            elif msg_type == "error":
                error_msg = resp.get("message", "Unknown error")
                print(f"[Client {client_id}] ⚠️ Lỗi từ server: {error_msg}")
                break

            else:
                print(f"[Client {client_id}] ❓ Message: {msg_type} | Data: {resp}")

        if rounds_played > 0:
            print(f"[Client {client_id}] ✅ Đã hoàn thành {rounds_played} lượt chơi")
        else:
            print(f"[Client {client_id}] ⚠️ Không chơi được lượt nào")

    except ConnectionRefusedError:
        print(f"[Client {client_id}] ❌ Không thể kết nối - Server có đang chạy không?")
    except Exception as e:
        print(f"[Client {client_id}] ⚠️ Lỗi: {e}")
    finally:
        if s:
            try:
                s.close()
                print(f"[Client {client_id}] 🔌 Đã đóng kết nối")
            except:
                pass

def run_test(num_clients=4, delay=0.5):
    """Chạy test với số lượng client chỉ định"""
    print(f"\n{'='*60}")
    print(f"🚀 BẮT ĐẦU TEST VỚI {num_clients} CLIENTS")
    print(f"{'='*60}\n")
    
    threads = []
    
    for i in range(num_clients):
        t = threading.Thread(target=client_simulator, args=(i,), daemon=True)
        threads.append(t)
        t.start()
        time.sleep(delay)

    # Chờ tất cả threads hoàn thành
    for t in threads:
        t.join(timeout=30)

    print(f"\n{'='*60}")
    print("✅ TEST HOÀN TẤT")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    # Test với 4 clients (tạo 2 cặp)
    run_test(num_clients=4, delay=0.5)