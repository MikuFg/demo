from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QComboBox, \
    QDateEdit, QPushButton, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox, \
    QLineEdit, QGroupBox, QFrame, QScrollArea, QWidget
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QDate
from DB.db import Database


class OrderForm(QDialog):
    def __init__(self, parent=None, db=None, order_id=None):
        super().__init__(parent)
        self.db = db or Database()
        self.order_id = order_id
        self.products_list = []

        self.setWindowIcon(QIcon("res/icon/icon.png"))
        self.resize(700, 600)
        self.setWindowTitle("Редактирование заказа" if order_id else "Новый заказ")
        self.init_ui()
        if order_id:
            self.load_order_data()

    def init_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()

        self.client_combo = QComboBox()
        for c in self.db.get_clients():
            self.client_combo.addItem(f"{c[1]} {c[2]} {c[3]}", c[0])
        form.addRow("Клиент:", self.client_combo)

        self.status_combo = QComboBox()
        for s in self.db.get_order_statuses():
            self.status_combo.addItem(s[1], s[0])
        form.addRow("Статус:", self.status_combo)

        self.delivery_date = QDateEdit()
        self.delivery_date.setDate(QDate.currentDate().addDays(3))
        self.delivery_date.setCalendarPopup(True)
        form.addRow("Дата доставки:", self.delivery_date)

        self.station_combo = QComboBox()
        for st in self.db.get_order_stations():
            self.station_combo.addItem(f"{st[1]}, {st[2]}, {st[3]}", st[0])
        form.addRow("Пункт выдачи:", self.station_combo)

        self.code_edit = QLineEdit()
        form.addRow("Код получения:", self.code_edit)

        layout.addLayout(form)

        products_group = QGroupBox("Товары")
        prod_layout = QVBoxLayout()

        add_layout = QHBoxLayout()
        self.product_combo = QComboBox()
        self.products_data = {}
        for p in self.db.get_products():
            self.product_combo.addItem(f"{p[1]} ({p[0]}) - {p[2]}₽", p[0])
            self.products_data[p[0]] = {'name': p[1], 'price': p[2], 'qty': p[3]}
        add_layout.addWidget(self.product_combo)

        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 100)
        add_layout.addWidget(QLabel("Кол-во:"))
        add_layout.addWidget(self.quantity_spin)

        add_btn = QPushButton("Добавить")
        add_btn.clicked.connect(self.add_product)
        add_layout.addWidget(add_btn)
        prod_layout.addLayout(add_layout)

        self.products_table = QTableWidget()
        self.products_table.setColumnCount(4)
        self.products_table.setHorizontalHeaderLabels(["Арт", "Товар", "Цена", "Кол-во"])
        self.products_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        prod_layout.addWidget(self.products_table)

        products_group.setLayout(prod_layout)
        layout.addWidget(products_group)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(QPushButton("Отмена", clicked=self.reject))
        btn_layout.addWidget(QPushButton("Сохранить", clicked=self.save_order))
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_order_data(self):
        order = self.db.get_order_by_id(self.order_id)
        if order:
            idx = self.client_combo.findData(order[4])
            if idx >= 0: self.client_combo.setCurrentIndex(idx)
            idx = self.status_combo.findData(order[5])
            if idx >= 0: self.status_combo.setCurrentIndex(idx)
            if order[2]: self.delivery_date.setDate(order[2])
            idx = self.station_combo.findData(order[3])
            if idx >= 0: self.station_combo.setCurrentIndex(idx)
            if order[6]: self.code_edit.setText(str(order[6]))

            for prod in self.db.get_order_products(self.order_id):
                self.products_list.append({'article': prod[1], 'name': prod[2], 'price': prod[4], 'quantity': prod[3]})
            self.update_products_table()

    def add_product(self):
        pid = self.product_combo.currentData()
        if pid in self.products_data:
            p = self.products_data[pid]
            qty = self.quantity_spin.value()
            existing = next((x for x in self.products_list if x['article'] == pid), None)
            total = (existing['quantity'] if existing else 0) + qty
            if total > p['qty']:
                return QMessageBox.warning(self, "Ошибка", f"Недостаточно: {p['qty']}")
            if existing:
                existing['quantity'] = total
            else:
                self.products_list.append({'article': pid, 'name': p['name'], 'price': p['price'], 'quantity': qty})
            self.update_products_table()

    def update_products_table(self):
        self.products_table.setRowCount(len(self.products_list))
        for row, p in enumerate(self.products_list):
            self.products_table.setItem(row, 0, QTableWidgetItem(p['article']))
            self.products_table.setItem(row, 1, QTableWidgetItem(p['name']))
            self.products_table.setItem(row, 2, QTableWidgetItem(f"{p['price']} ₽"))
            self.products_table.setItem(row, 3, QTableWidgetItem(str(p['quantity'])))

    def save_order(self):
        if not self.products_list:
            return QMessageBox.warning(self, "Ошибка", "Добавьте товары!")
        products = [(p['article'], p['quantity']) for p in self.products_list]
        if self.order_id:
            ok = self.db.update_order(self.order_id, self.client_combo.currentData(),
                self.station_combo.currentData(), self.delivery_date.date().toString("yyyy-MM-dd"),
                self.status_combo.currentData(), self.code_edit.text().strip() or None)
        else:
            ok = self.db.add_order(self.client_combo.currentData(), self.station_combo.currentData(),
                self.delivery_date.date().toString("yyyy-MM-dd"), self.status_combo.currentData(),
                self.code_edit.text().strip() or None, products)
        if ok:
            QMessageBox.information(self, "Успех", "Заказ сохранен!")
            self.accept()
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось сохранить!")


class OrdersWindow(QDialog):
    def __init__(self, parent=None, db=None, user_role=None):
        super().__init__(parent)
        self.db = db or Database()
        self.user_role = user_role
        self.setWindowTitle("Заказы")
        self.setWindowIcon(QIcon("res/icon/icon.png"))
        self.resize(900, 600)
        self.init_ui()
        self.load_orders()

    def init_ui(self):
        layout = QVBoxLayout()
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по номеру или коду...")
        self.search_input.textChanged.connect(self.load_orders)
        search_layout.addWidget(self.search_input)
        if self.user_role == "Администратор":
            search_layout.addWidget(QPushButton("Добавить заказ", clicked=self.add_order))
        layout.addLayout(search_layout)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll)
        layout.addWidget(QPushButton("Назад", clicked=self.reject))
        self.setLayout(layout)

    def load_orders(self):
        orders = self.db.get_orders(self.search_input.text().strip() or None)
        while self.container_layout.count():
            w = self.container_layout.takeAt(0).widget()
            if w: w.deleteLater()
        for o in orders:
            self.create_card(o)

    def create_card(self, order):
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box)
        layout = QHBoxLayout()

        left = QFrame()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel(f"<b>Артикул заказа:</b> {order[0]}"))
        left_layout.addWidget(QLabel(f"<b>Статус заказа:</b> {order[9]}"))
        left_layout.addWidget(QLabel(f"<b>Адрес пункта выдачи:</b> {order[3]}, ул. {order[4]}, д. {order[5]}"))
        left_layout.addWidget(QLabel(f"<b>Дата заказа:</b> {order[1] or '-'}"))
        left_layout.addWidget(QLabel(f"<b>Клиент:</b> {order[6]} {order[7]} {order[8]}".strip()))
        left_layout.addWidget(QLabel(f"<b>Код получения:</b> {order[10] or '-'}"))
        layout.addWidget(left, stretch=3)

        right = QFrame()
        right_layout = QVBoxLayout(right)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(QLabel(f"<b>Дата доставки:</b>\n{order[2] or '-'}"))
        layout.addWidget(right, stretch=1)
        frame.setLayout(layout)

        if order[9] == "Доставлен": frame.setStyleSheet("background-color: #90EE90;")
        elif order[9] == "Отменен": frame.setStyleSheet("background-color: #FFB6C1;")
        elif order[9] == "В обработке": frame.setStyleSheet("background-color: #FFFFE0;")

        if self.user_role == "Администратор":
            frame.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            frame.customContextMenuRequested.connect(lambda p, oid=order[0]: self.show_menu(p, oid))
        else:
            frame.mouseDoubleClickEvent = lambda e, oid=order[0]: self.view_order(oid)
        self.container_layout.addWidget(frame)

    def show_menu(self, pos, order_id):
        from PyQt6.QtWidgets import QMenu
        menu = QMenu()
        view = menu.addAction("Просмотр")
        edit = menu.addAction("Редактировать")
        delete = menu.addAction("Удалить")
        action = menu.exec(self.mapToGlobal(pos))
        if action == view: self.view_order(order_id)
        elif action == edit: self.edit_order(order_id)
        elif action == delete: self.delete_order(order_id)

    def add_order(self):
        if OrderForm(self, self.db, None).exec(): self.load_orders()

    def edit_order(self, order_id):
        if OrderForm(self, self.db, order_id).exec(): self.load_orders()

    def delete_order(self, order_id):
        if QMessageBox.question(self, "Подтверждение", f"Удалить заказ #{order_id}?") == QMessageBox.StandardButton.Yes:
            if self.db.delete_order(order_id):
                QMessageBox.information(self, "Успех", "Заказ удален!")
                self.load_orders()

    def view_order(self, order_id):
        order = self.db.get_order_by_id(order_id)
        if not order: return QMessageBox.warning(self, "Ошибка", "Заказ не найден")

        products = self.db.get_order_products(order_id)
        total = self.db.get_order_total(order_id)

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Заказ #{order_id}")
        dialog.resize(500, 400)
        layout = QVBoxLayout()

        info = QGroupBox("Информация")
        info_layout = QFormLayout()
        info_layout.addRow("ID:", QLabel(str(order_id)))
        info_layout.addRow("Дата заказа:", QLabel(str(order[1]) or "-"))
        info_layout.addRow("Дата доставки:", QLabel(str(order[2]) or "-"))
        info_layout.addRow("Код:", QLabel(str(order[6]) or "-"))
        clients = self.db.get_clients()
        client = next((c for c in clients if c[0] == order[4]), None)
        info_layout.addRow("Клиент:", QLabel(f"{client[1]} {client[2]} {client[3]}" if client else "-"))
        statuses = self.db.get_order_statuses()
        status = next((s for s in statuses if s[0] == order[5]), None)
        info_layout.addRow("Статус:", QLabel(status[1] if status else "-"))
        stations = self.db.get_order_stations()
        station = next((s for s in stations if s[0] == order[3]), None)
        info_layout.addRow("Адрес:", QLabel(f"{station[1]}, {station[2]}, {station[3]}" if station else "-"))
        info.setLayout(info_layout)
        layout.addWidget(info)

        prod_table = QTableWidget()
        prod_table.setColumnCount(4)
        prod_table.setHorizontalHeaderLabels(["Арт", "Товар", "Цена", "Кол-во"])
        prod_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        prod_table.setRowCount(len(products))
        for row, p in enumerate(products):
            prod_table.setItem(row, 0, QTableWidgetItem(p[1]))
            prod_table.setItem(row, 1, QTableWidgetItem(p[2]))
            prod_table.setItem(row, 2, QTableWidgetItem(f"{p[4]} ₽"))
            prod_table.setItem(row, 3, QTableWidgetItem(str(p[3])))
        layout.addWidget(prod_table)
        layout.addWidget(QLabel(f"<b>Итого: {total} ₽</b>"))
        layout.addWidget(QPushButton("Закрыть", clicked=dialog.accept))
        dialog.setLayout(layout)
        dialog.exec()
