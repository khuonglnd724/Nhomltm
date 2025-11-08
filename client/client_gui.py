import threading
import tkinter as tk
from tkinter import messagebox
from client_logic import client_logic
import os

class RPSClientGUI:
    def __init__(self, master):
        self.master = master
        master.title("Rock Paper Scissors Game")
        master.geometry("500x650")
        master.resizable(False, False)
        master.configure(bg="#f8fafc")

        self.network = client_logic()
        self.name = ""
        self.opponent = None

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.rock_img = tk.PhotoImage(file=os.path.join(BASE_DIR, "rock.png")).subsample(4, 4)
        self.paper_img = tk.PhotoImage(file=os.path.join(BASE_DIR, "paper.png")).subsample(4, 4)
        self.scissors_img = tk.PhotoImage(file=os.path.join(BASE_DIR, "scissors.png")).subsample(4, 4)

        # --- Header ---
        header_frame = tk.Frame(master, bg="#6366f1", height=80)
        header_frame.pack(fill="x", pady=(0, 20))
        header_frame.pack_propagate(False)
        tk.Label(header_frame, text="🎮 ROCK PAPER SCISSORS", font=("Arial", 20, "bold"),
                 fg="white", bg="#6366f1").pack(expand=True)

        # --- Connection Section ---
        conn_frame = tk.Frame(master, bg="#f8fafc")
        conn_frame.pack(pady=10)
        tk.Label(conn_frame, text="Player Name:", font=("Arial", 11, "bold"),
                 fg="#475569", bg="#f8fafc").pack(pady=5)
        self.name_entry = tk.Entry(conn_frame, font=("Arial", 13), width=25,
                                   bg="white", fg="#1e293b", insertbackground="#6366f1",
                                   relief="solid", borderwidth=2)
        self.name_entry.pack(pady=5, ipady=8)

        self.connect_btn = tk.Button(conn_frame, text="🔗 CONNECT TO SERVER",
                                     font=("Arial", 12, "bold"), bg="#6366f1",
                                     fg="white", relief="flat", cursor="hand2",
                                     command=self.connect_server, padx=20, pady=10)
        self.connect_btn.pack(pady=10)

        # --- Status Section ---
        status_frame = tk.Frame(master, bg="white", height=120, relief="solid", borderwidth=1)
        status_frame.pack(fill="x", pady=15, padx=20)
        status_frame.pack_propagate(False)
        self.status_label = tk.Label(status_frame, text="⚪ Not Connected",
                                     fg="#64748b", bg="white", font=("Arial", 12, "bold"))
        self.status_label.pack(pady=5)
        self.opponent_label = tk.Label(status_frame, text="Opponent: Waiting...",
                                       font=("Arial", 11), fg="#94a3b8", bg="white")
        self.opponent_label.pack(pady=5)

        # --- Game Buttons ---
        game_frame = tk.Frame(master, bg="#f8fafc")
        game_frame.pack(pady=20)
        tk.Label(game_frame, text="Choose Your Move:", font=("Arial", 13, "bold"),
                 fg="#334155", bg="#f8fafc").pack(pady=10)
        btn_container = tk.Frame(game_frame, bg="#f8fafc")
        btn_container.pack()

        btn_config = {"relief": "flat", "cursor": "hand2", "borderwidth": 0,
                      "bg": "#f8fafc", "activebackground": "#e2e8f0"}

        self.rock_btn = tk.Button(btn_container, image=self.rock_img,
                                  command=lambda: self.send_move("rock"), **btn_config)
        self.rock_btn.grid(row=0, column=0, padx=8, pady=5)
        self.paper_btn = tk.Button(btn_container, image=self.paper_img,
                                   command=lambda: self.send_move("paper"), **btn_config)
        self.paper_btn.grid(row=0, column=1, padx=8, pady=5)
        self.scissors_btn = tk.Button(btn_container, image=self.scissors_img,
                                      command=lambda: self.send_move("scissors"), **btn_config)
        self.scissors_btn.grid(row=0, column=2, padx=8, pady=5)

        # --- Result Section ---
        result_frame = tk.Frame(master, bg="white", height=120, relief="solid", borderwidth=1)
        result_frame.pack(fill="x", pady=15, padx=20)
        result_frame.pack_propagate(False)
        self.result_label = tk.Label(result_frame, text="Waiting for match...",
                                     font=("Arial", 14, "bold"), fg="#64748b",
                                     bg="white", wraplength=450, justify="center")
        self.result_label.pack(expand=True)

        self.disable_game_buttons()
        self.add_hover_effect(self.connect_btn, "#6366f1", "#4f46e5")
        master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def add_hover_effect(self, button, normal_color, hover_color):
        button.bind("<Enter>", lambda e: button.config(bg=hover_color))
        button.bind("<Leave>", lambda e: button.config(bg=normal_color))

    def connect_server(self):
        self.name = self.name_entry.get().strip()
        if not self.name:
            messagebox.showwarning("Error", "Please enter your name!")
            return
        try:
            self.network.connect()
            self.status_label.config(text="🟢 Connected to Server", fg="#10b981")
            self.connect_btn.config(state="disabled")
            self.name_entry.config(state="disabled")
            self.network.send_json({"type": "join", "player": self.name})
            self.network.send_json({"type": "join_queue"})
            self.status_label.config(text="🟡 Searching for Opponent...", fg="#f59e0b")
            threading.Thread(target=self.listen_server, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Connection Error", f"Cannot connect to server:\n{str(e)}")

    def listen_server(self):
        try:
            while self.network.is_connected():
                msg = self.network.recv_json()
                if not msg:
                    continue
                
                msg_type = msg.get("type")

                if msg_type == "match_found":
                    self.opponent = msg.get("opponent")
                    self.master.after(0, lambda opp=self.opponent: self.opponent_label.config(
                        text=f"⚔️ Opponent: {opp}", fg="#f43f5e"))
                    self.master.after(0, lambda: self.status_label.config(
                        text="🟣 Match Started!", fg="#a855f7"))

                elif msg_type == "request_move":
                    self.master.after(0, self.enable_move_request)

                elif msg_type == "round_result":
                    your_move = msg.get("your_move", "")
                    opponent_move = msg.get("opponent_move", "")
                    result = msg.get("result", "draw")
                    
                    # Hiển thị kết quả NGAY LẬP TỨC
                    self.master.after(0, lambda r=result, ym=your_move, om=opponent_move: 
                                     self.show_result(r, ym, om))
                    
                    # Sau 3 giây, tự động chuyển sang vòng mới
                    self.master.after(3000, self.enable_move_request)

                elif msg_type == "game_over":
                    # Thay vì dừng vòng lắng nghe, hiển thị thông báo và tự động vào lại hàng đợi
                    self.master.after(0, lambda: messagebox.showinfo("Game Over", "The game has ended!"))
                    # reset trạng thái đối thủ và giao diện
                    self.opponent = None
                    self.master.after(0, lambda: self.opponent_label.config(text="Opponent: Waiting...", fg="#94a3b8"))
                    # Gửi yêu cầu vào lại hàng đợi để được ghép trận
                    try:
                        self.network.send_json({"type": "join_queue"})
                        self.master.after(0, lambda: self.status_label.config(text="🟡 Searching for Opponent...", fg="#f59e0b"))
                    except:
                        pass

                elif msg_type == "opponent_disconnected":
                    # Khi server thông báo đối thủ rời — hành xử giống như trên
                    self.master.after(0, lambda: messagebox.showinfo("Opponent Left", "Your opponent disconnected. Rejoining queue..."))
                    self.opponent = None
                    self.master.after(0, lambda: self.opponent_label.config(text="Opponent: Waiting...", fg="#94a3b8"))
                    try:
                        self.network.send_json({"type": "join_queue"})
                        self.master.after(0, lambda: self.status_label.config(text="🟡 Searching for Opponent...", fg="#f59e0b"))
                    except:
                        pass
        except Exception as e:
            if self.network.is_connected():
                self.master.after(0, lambda err=str(e): self.status_label.config(
                    text=f"🔴 Connection Lost: {err}", fg="#ef4444"))

    def show_result(self, result, your_move, opponent_move):
        """Hiển thị kết quả lên giao diện"""
        self.disable_game_buttons()
        
        # Xác định emoji, text và màu
        if result == "win":
            emoji, text, color = "🎉", "YOU WIN!", "#10b981"
        elif result == "lose":
            emoji, text, color = "😔", "YOU LOSE", "#ef4444"
        else:
            emoji, text, color = "🤝", "IT'S A DRAW", "#3b82f6"
        
        # Tạo text kết quả
        result_text = f"{emoji} {text}\n\nYou: {your_move.upper()} | Opponent: {opponent_move.upper()}"
        
        # HIỂN THỊ POPUP ĐỂ DEBUG
        messagebox.showinfo("Round Result", result_text)
        
        # CẬP NHẬT GIAO DIỆN - QUAN TRỌNG!
        self.result_label.config(
            text=result_text, 
            fg=color,
            font=("Arial", 16, "bold")  # Font to hơn để dễ thấy
        )
        
        # Force update
        self.result_label.update()
        self.master.update()

    def enable_move_request(self):
        """Enable buttons và yêu cầu chọn nước đi mới"""
        self.enable_game_buttons()
        self.result_label.config(
            text="⏰ Make Your Move!", 
            fg="#6366f1",
            font=("Arial", 14, "bold")
        )

    def send_move(self, move):
        if not self.network.is_connected():
            messagebox.showerror("Error", "Not connected to server!")
            return
        try:
            self.network.send_json({"type": "move", "move": move})
            move_emoji = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}
            self.result_label.config(
                text=f"You chose: {move_emoji[move]} {move.upper()}\n\nWaiting for opponent...",
                fg="#64748b",
                font=("Arial", 13)
            )
            self.disable_game_buttons()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send move:\n{str(e)}")

    def enable_game_buttons(self):
        self.rock_btn.config(state="normal")
        self.paper_btn.config(state="normal")
        self.scissors_btn.config(state="normal")

    def disable_game_buttons(self):
        self.rock_btn.config(state="disabled")
        self.paper_btn.config(state="disabled")
        self.scissors_btn.config(state="disabled")

    def on_closing(self):
        if self.network.is_connected():
            self.network.disconnect()
        self.master.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = RPSClientGUI(root)
    root.mainloop()