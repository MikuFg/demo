from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QPushButton, QDialog, \
    QMessageBox
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt
from DB.db import Database


class Auth(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Обувной магазин")
        self.setWindowIcon(QIcon("res/icon/icon.png"))
        self.setFixedSize(500, 300)

        self.db = Database()

        self.userName = "Гость"
        self.userRole = None
        self.userId = 0

        central_layout = QVBoxLayout()

        login_layout = QHBoxLayout()
        passw_layout = QHBoxLayout()
        buttons_layout = QHBoxLayout()

        main_lbl = QLabel("Обувной магазин. Авторизация")
        main_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_lbl.setStyleSheet("font-size: 15px; font-weight: bold;")

        login_lbl = QLabel("Логин:")
        passw_lbl = QLabel("Пароль:")

        central_layout.addWidget(main_lbl)
        central_layout.addLayout(login_layout)
        central_layout.addLayout(passw_layout)
        central_layout.addLayout(buttons_layout)

        self.login_line = QLineEdit()
        self.login_line.setPlaceholderText("Введите логин")
        login_layout.addWidget(login_lbl)
        login_layout.addWidget(self.login_line)

        self.passw_line = QLineEdit()
        self.passw_line.setPlaceholderText("Введите пароль")
        self.passw_line.setEchoMode(QLineEdit.EchoMode.Password)
        passw_layout.addWidget(passw_lbl)
        passw_layout.addWidget(self.passw_line)

        self.enter_btn = QPushButton("Войти")
        self.enter_btn.clicked.connect(self.enter_user)

        self.guest_btn = QPushButton("Войти как гость")
        self.guest_btn.clicked.connect(self.enter_guest)

        buttons_layout.addWidget(self.enter_btn)
        buttons_layout.addWidget(self.guest_btn)

        self.setLayout(central_layout)

    def get_user_info(self):
        return self.userName, self.userRole, self.userId

    def enter_guest(self):
        self.userName = "Гость"
        self.userRole = None
        self.userId = 0
        QMessageBox.information(self, "Успех", f"Гостевой режим")
        self.accept()

    def enter_user(self):
        login = self.login_line.text()
        passw = self.passw_line.text()
        data = self.db.auth(login, passw)
        print(f'data: {data}')

        if not login:
            QMessageBox.warning(self, "Ошибка", "Введите логин")
            return

        if not passw:
            QMessageBox.warning(self, "Ошибка", "Введите пароль")
            return

        if not data:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль. Попробуйте снова!")
            return

        for item in data:
            if login.strip() in item and passw.strip() in item:
                self.userName = f"{item[1]} {item[2]} {item[3]}"
                self.userId = item[0]

                if item[4] == 1:
                    self.userRole = "Администратор"
                    QMessageBox.information(self, "Успех", f"Успешная регистрация: {self.userRole}")
                    self.accept()
                    return
                if item[4] == 2:
                    self.userRole = "Менеджер"
                    QMessageBox.information(self, "Успех", f"Успешная регистрация: {self.userRole}")
                    self.accept()
                    return
                if item[4] == 3:
                    self.userRole = "Авторизованный клиент"
                    QMessageBox.information(self, "Успех", f"Успешная регистрация: {self.userRole}")
                    self.accept()
                    return

        QMessageBox.critical(self, "Ошибка", "Отказ работы программы")
        self.reject()