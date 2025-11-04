## Bảng xếp hạng (Leaderboard)

- File lưu trữ: `server/leaderboard.json`
- Module: `server/leaderboard.py`
- Hàm chính:
  - `update_score(player_name, result)` — cập nhật điểm (result: "win" | "lose" | "draw")
  - `get_leaderboard()` — trả về danh sách đã sắp xếp theo điểm
  - `print_leaderboard()` — in ra terminal
- Quy ước điểm: win = 3, draw = 1, lose = 0
- Cách dùng:
  - Server gọi `update_score()` sau khi trận đấu kết thúc.
