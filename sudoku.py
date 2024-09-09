import tkinter as tk
from tkinter import filedialog
import json
import threading

class Cell:
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.value = None
        self.memos = []

    def add_value(self, value):
        self.value = value
        self.memos.clear()

    def remove_value(self):
        self.value = None

    def add_memo(self, memo):
        if memo not in self.memos:
            self.memos.append(memo)

    def remove_memo(self, memo):
        if memo in self.memos:
            self.memos.remove(memo)

    def clear(self):
        self.value = None
        self.memos.clear()

    def is_empty(self):
        return self.value is None and not self.memos

class SudokuUI:
    def __init__(self, root):
        self.root = root
        self.root.title("25x25 Sudoku")
        self.selected_number = None
        self.memo_mode = False
        self.selected_cell = None
        self.cells_data = [[Cell(r, c) for c in range(25)] for r in range(25)]
        self.history = []  # 실행 취소를 위한 히스토리 스택
        self.create_widgets()
        self.create_bindings()

    def create_widgets(self):
        self.buttons_frame = tk.Frame(self.root)
        self.buttons_frame.grid(row=0, column=1, padx=10, pady=10, sticky="ns")

        self.memo_button = tk.Button(self.buttons_frame, text="Memo", command=self.toggle_memo, width=10, height=2, bg="lightblue", fg="black")
        self.memo_button.grid(row=0, column=0, padx=5, pady=5)

        self.clear_button = tk.Button(self.buttons_frame, text="Clear Memos", command=self.clear_memos, width=10, height=2, bg="lightgrey", fg="black")
        self.clear_button.grid(row=1, column=0, padx=5, pady=5)

        self.save_button = tk.Button(self.buttons_frame, text="Save", command=self.save_game, width=10, height=2, bg="lightgrey", fg="black")
        self.save_button.grid(row=0, column=1, padx=5, pady=5)

        self.load_button = tk.Button(self.buttons_frame, text="Load", command=self.load_game, width=10, height=2, bg="lightgrey", fg="black")
        self.load_button.grid(row=1, column=1, padx=5, pady=5)

        self.undo_button = tk.Button(self.buttons_frame, text="Undo", command=self.undo_action, width=10, height=2, bg="lightgrey", fg="black")
        self.undo_button.grid(row=6, column=0, columnspan=2, padx=5, pady=5)

        self.numbers_frame = tk.Frame(self.buttons_frame)
        self.numbers_frame.grid(row=5, column=0, columnspan=2, padx=5, pady=5)

        self.number_buttons = []
        for i in range(1, 26):
            btn = tk.Button(self.numbers_frame, text=str(i), command=lambda i=i: self.select_number(i), width=4, height=2, bg="lightgrey", fg="black")
            btn.grid(row=(i-1)//5, column=(i-1)%5, padx=5, pady=5)
            self.number_buttons.append(btn)

        self.canvas = tk.Canvas(self.root, width=910, height=910)
        self.canvas.grid(row=0, column=0, padx=10, pady=10)

        self.cells = [[None for _ in range(25)] for _ in range(25)]
        cell_size = 36  # 20% 증가
        margin = 5

        for r in range(25):
            for c in range(25):
                x1 = margin + c * cell_size
                y1 = margin + r * cell_size
                x2 = x1 + cell_size
                y2 = y1 + cell_size
                self.canvas.create_rectangle(x1, y1, x2, y2, outline="black")

                text_widget = tk.Text(self.canvas, width=2, height=1, font=("Arial", 12), wrap="none", padx=2, pady=2, cursor="none", insertofftime=0)
                text_widget.place(x=x1 + 2, y=y1 + 2, width=cell_size - 4, height=cell_size - 4)
                text_widget.bind("<Button-1>", lambda e, r=r, c=c: self.cell_clicked(r, c))
                text_widget.config(insertbackground="white", inactiveselectbackground="white", selectbackground="white", cursor="none")  # 커서 완전히 숨기기
                self.cells[r][c] = text_widget

        # 굵은 테두리 그리기
        for i in range(6):
            self.canvas.create_line(margin, margin + i * 5 * cell_size, margin + 25 * cell_size, margin + i * 5 * cell_size, width=2, fill="red")
            self.canvas.create_line(margin + i * 5 * cell_size, margin, margin + i * 5 * cell_size, margin + 25 * cell_size, width=2, fill="red")

        # 가장 외곽의 굵은 테두리 그리기
        self.canvas.create_line(margin, margin, margin, margin + 25 * cell_size, width=2, fill="red")
        self.canvas.create_line(margin, margin, margin + 25 * cell_size, margin, width=2, fill="red")
        self.canvas.create_line(margin + 25 * cell_size, margin, margin + 25 * cell_size, margin + 25 * cell_size, width=2, fill="red")
        self.canvas.create_line(margin, margin + 25 * cell_size, margin + 25 * cell_size, margin + 25 * cell_size, width=2, fill="red")

    def create_bindings(self):
        self.root.bind("<KeyPress>", self.key_press)

    def key_press(self, event):
        if self.selected_cell:
            row, col = self.selected_cell[1], self.selected_cell[2]
            if event.char.isdigit():
                num = int(event.char)
                if 1 <= num <= 25:
                    self.select_number(num)
                    self.apply_number_to_cell(row, col)

    def toggle_memo(self):
        self.memo_mode = not self.memo_mode
        self.memo_button.config(relief="sunken" if self.memo_mode else "raised")

    def select_number(self, number):
        if self.selected_number == number:
            self.selected_number = None
            for btn in self.number_buttons:
                btn.config(relief="raised")
            self.remove_highlight()
        else:
            self.selected_number = number
            for btn in self.number_buttons:
                btn.config(relief="raised")
            self.number_buttons[number-1].config(relief="sunken")
            self.apply_highlight()

    def cell_clicked(self, row, col):
        if self.selected_cell:
            self.selected_cell[0].config(bg="white")

        self.selected_cell = self.cells[row][col], row, col
        self.selected_cell[0].config(bg="lightblue")
        if self.selected_number:
            self.apply_number_to_cell(row, col)
        elif self.memo_mode:
            key = f"{row}_{col}"
            if self.selected_number in self.cells_data[row][col].memos:
                self.cells_data[row][col].remove_memo(self.selected_number)
                self.update_visuals()
        else:
            cell = self.cells_data[row][col]
            if cell.value is not None:
                self.history.append((row, col, cell.value, list(cell.memos)))
                cell.remove_value()
                self.update_visuals()

    def apply_number_to_cell(self, row, col):
        cell = self.cells_data[row][col]
        if self.memo_mode and self.selected_number:
            self.history.append((row, col, cell.value, list(cell.memos)))
            if self.selected_number in cell.memos:
                cell.remove_memo(self.selected_number)
            else:
                cell.add_memo(self.selected_number)
        elif self.selected_number:
            self.history.append((row, col, cell.value, list(cell.memos)))
            if cell.value == self.selected_number:
                cell.remove_value()
            else:
                cell.add_value(self.selected_number)

        self.update_visuals()
        self.apply_highlight()

    def apply_highlight(self):
        self.remove_highlight()
        if self.selected_number:
            for row in range(25):
                for col in range(25):
                    cell = self.cells_data[row][col]
                    text_widget = self.cells[row][col]
                    if cell.value == self.selected_number or self.selected_number in cell.memos:
                        text_widget.tag_configure("highlight", foreground="red")
                        text_widget.tag_add("highlight", "1.0", "end")
                    else:
                        text_widget.tag_remove("highlight", "1.0", "end")

        self.check_duplicates_async()

    def remove_highlight(self):
        for row in self.cells:
            for text_widget in row:
                text_widget.tag_remove("highlight", "1.0", "end")
                text_widget.tag_remove("duplicate", "1.0", "end")

    def update_visuals(self):
        for row in range(25):
            for col in range(25):
                cell = self.cells_data[row][col]
                text_widget = self.cells[row][col]
                text_widget.delete("1.0", tk.END)
                if cell.value is not None:
                    text_widget.insert(tk.END, str(cell.value))
                    text_widget.tag_configure("center", justify='center')
                    text_widget.tag_add("center", "1.0", "end")
                    text_widget.config(font=("Arial", 20))
                elif cell.memos:
                    memo_text = self.format_memo_text(cell.memos)
                    text_widget.insert(tk.END, memo_text)
                    text_widget.config(font=("Arial", 5))
                else:
                    text_widget.insert(tk.END, "")

    def format_memo_text(self, memos):
        memo_text = ""
        for i, memo in enumerate(memos):
            memo_text += str(memo)
            if (i + 1) % 3 == 0:
                memo_text += "\n"
            else:
                memo_text += " "
        return memo_text.strip()

    def clear_memos(self):
        self.history.append({(cell.row, cell.col): (cell.value, list(cell.memos)) for row in self.cells_data for cell in row})
        for row in self.cells_data:
            for cell in row:
                cell.memos.clear()
        self.update_visuals()

    def check_duplicates_async(self):
        thread = threading.Thread(target=self.check_duplicates)
        thread.start()

    def check_duplicates(self):
        duplicates = set()

        # 행과 열 중복 확인
        for i in range(25):
            row_counts = {}
            col_counts = {}
            for j in range(25):
                cell_row = self.cells_data[i][j]
                cell_col = self.cells_data[j][i]
                if cell_row.value is not None:
                    if cell_row.value in row_counts:
                        duplicates.add(cell_row)
                        duplicates.add(row_counts[cell_row.value])
                    else:
                        row_counts[cell_row.value] = cell_row
                if cell_col.value is not None:
                    if cell_col.value in col_counts:
                        duplicates.add(cell_col)
                        duplicates.add(col_counts[cell_col.value])
                    else:
                        col_counts[cell_col.value] = cell_col

        # 5x5 블록 중복 확인
        for block_row in range(5):
            for block_col in range(5):
                block_counts = {}
                for i in range(5):
                    for j in range(5):
                        row = block_row * 5 + i
                        col = block_col * 5 + j
                        cell = self.cells_data[row][col]
                        if cell.value is not None:
                            if cell.value in block_counts:
                                duplicates.add(cell)
                                duplicates.add(block_counts[cell.value])
                            else:
                                block_counts[cell.value] = cell

        # 중복된 셀들 하이라이팅
        for cell in duplicates:
            self.highlight_cell(cell.row, cell.col, "duplicate", "blue")

    def highlight_cell(self, row, col, tag, color):
        def apply_tag():
            text_widget = self.cells[row][col]
            text_widget.tag_configure(tag, foreground=color)
            text_widget.tag_add(tag, "1.0", "end")

        self.root.after(0, apply_tag)

    def save_game(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if not file_path:
            return
        save_data = {}
        for row in self.cells_data:
            for cell in row:
                if cell.value is not None or cell.memos:
                    save_data[f"{cell.row}_{cell.col}"] = {"value": cell.value, "memos": cell.memos}
        with open(file_path, "w") as f:
            json.dump(save_data, f)

    def load_game(self):
        file_path = filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if not file_path:
            return
        with open(file_path, "r") as f:
            json_data = json.load(f)
            for key, data in json_data.items():
                row, col = map(int, key.split("_"))
                cell = self.cells_data[row][col]
                cell.value = data["value"]
                cell.memos = data["memos"]
        self.update_visuals()
        self.apply_highlight()

    def undo_action(self):
        if not self.history:
            return
        last_action = self.history.pop()
        if isinstance(last_action, tuple):
            row, col, value, memos = last_action
            cell = self.cells_data[row][col]
            cell.value = value
            cell.memos = memos
        elif isinstance(last_action, dict):
            for (row, col), (value, memos) in last_action.items():
                cell = self.cells_data[row][col]
                cell.value = value
                cell.memos = memos
        self.update_visuals()
        self.apply_highlight()

if __name__ == "__main__":
    root = tk.Tk()
    app = SudokuUI(root)
    root.mainloop()
