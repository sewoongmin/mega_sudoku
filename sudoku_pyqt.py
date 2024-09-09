import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QTextEdit, QGridLayout, QWidget, QVBoxLayout, QFileDialog
from PyQt5.QtGui import QFont, QTextCursor
from PyQt5.QtCore import Qt

class Cell:
    def __init__(self):
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

class SudokuUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.selected_number = None
        self.memo_mode = False
        self.cells_data = [[Cell() for _ in range(25)] for _ in range(25)]
        self.history = []
        self.initUI()

    def initUI(self):
        self.setWindowTitle('25x25 Sudoku')
        self.setGeometry(100, 100, 1200, 1000)

        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        self.grid_widget = QWidget(main_widget)
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(2)
        main_layout.addWidget(self.grid_widget)

        self.cells = [[None for _ in range(25)] for _ in range(25)]
        self.cell_widgets = [[None for _ in range(25)] for _ in range(25)]
        for r in range(25):
            for c in range(25):
                cell_widget = QTextEdit(self)
                cell_widget.setFont(QFont('Arial', 12))
                cell_widget.setAlignment(Qt.AlignCenter)
                cell_widget.setFixedSize(36, 36)
                cell_widget.setStyleSheet("border: 1px solid black;")
                cell_widget.installEventFilter(self)
                self.grid_layout.addWidget(cell_widget, r, c)
                self.cell_widgets[r][c] = cell_widget

        self.init_buttons(main_layout)

    def init_buttons(self, layout):
        buttons_layout = QGridLayout()

        self.memo_button = QPushButton("Memo", self)
        self.memo_button.setCheckable(True)
        self.memo_button.clicked.connect(self.toggle_memo)
        buttons_layout.addWidget(self.memo_button, 0, 0)

        self.clear_button = QPushButton("Clear Memos", self)
        self.clear_button.clicked.connect(self.clear_memos)
        buttons_layout.addWidget(self.clear_button, 1, 0)

        self.save_button = QPushButton("Save", self)
        self.save_button.clicked.connect(self.save_game)
        buttons_layout.addWidget(self.save_button, 0, 1)

        self.load_button = QPushButton("Load", self)
        self.load_button.clicked.connect(self.load_game)
        buttons_layout.addWidget(self.load_button, 1, 1)

        self.undo_button = QPushButton("Undo", self)
        self.undo_button.clicked.connect(self.undo_action)
        buttons_layout.addWidget(self.undo_button, 2, 0, 1, 2)

        self.number_buttons = []
        for i in range(1, 26):
            btn = QPushButton(str(i), self)
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, i=i: self.select_number(i))
            self.number_buttons.append(btn)
            buttons_layout.addWidget(btn, 3 + (i-1)//5, (i-1)%5)

        layout.addLayout(buttons_layout)

    def toggle_memo(self):
        self.memo_mode = self.memo_button.isChecked()

    def select_number(self, number):
        if self.selected_number == number:
            self.selected_number = None
            for btn in self.number_buttons:
                btn.setChecked(False)
            self.remove_highlight()
        else:
            self.selected_number = number
            for btn in self.number_buttons:
                btn.setChecked(False)
            self.number_buttons[number-1].setChecked(True)
            self.apply_highlight()

    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.FocusIn:
            row, col = self.get_cell_position(source)
            if row is not None and col is not None:
                self.cell_clicked(row, col)
        return super().eventFilter(source, event)

    def get_cell_position(self, cell_widget):
        for r in range(25):
            for c in range(25):
                if self.cell_widgets[r][c] == cell_widget:
                    return r, c
        return None, None

    def cell_clicked(self, row, col):
        cell = self.cells_data[row][col]
        if self.selected_number:
            if self.memo_mode:
                if self.selected_number in cell.memos:
                    cell.remove_memo(self.selected_number)
                else:
                    cell.add_memo(self.selected_number)
            else:
                if cell.value == self.selected_number:
                    cell.remove_value()
                else:
                    cell.add_value(self.selected_number)
            self.update_visuals()
            self.apply_highlight()
        else:
            if cell.value is not None:
                cell.remove_value()
                self.update_visuals()

    def apply_highlight(self):
        self.remove_highlight()
        if self.selected_number:
            for r in range(25):
                for c in range(25):
                    cell = self.cells_data[r][c]
                    cell_widget = self.cell_widgets[r][c]
                    if cell.value == self.selected_number or self.selected_number in cell.memos:
                        cell_widget.setStyleSheet("color: red;")
        self.check_duplicates()

    def remove_highlight(self):
        for r in range(25):
            for c in range(25):
                cell_widget = self.cell_widgets[r][c]
                cell_widget.setStyleSheet("color: black;")

    def update_visuals(self):
        for r in range(25):
            for c in range(25):
                cell = self.cells_data[r][c]
                cell_widget = self.cell_widgets[r][c]
                cell_widget.clear()
                if cell.value is not None:
                    cell_widget.setFontPointSize(20)
                    cell_widget.setPlainText(str(cell.value))
                elif cell.memos:
                    cell_widget.setFontPointSize(5)
                    cell_widget.setPlainText(" ".join(map(str, cell.memos)))

    def clear_memos(self):
        for r in range(25):
            for c in range(25):
                self.cells_data[r][c].memos.clear()
        self.update_visuals()

    def check_duplicates(self):
        # 중복된 셀들을 찾아서 하이라이팅하는 함수 구현
        pass

    def save_game(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Game", "", "JSON Files (*.json)")
        if file_path:
            save_data = {}
            for r in range(25):
                for c in range(25):
                    cell = self.cells_data[r][c]
                    if cell.value is not None or cell.memos:
                        save_data[f"{r}_{c}"] = {"value": cell.value, "memos": cell.memos}
            with open(file_path, "w") as f:
                json.dump(save_data, f)

    def load_game(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Load Game", "", "JSON Files (*.json)")
        if file_path:
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
        # 실행 취소 기능 구현
        pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    sudoku = SudokuUI()
    sudoku.show()
    sys.exit(app.exec_())
