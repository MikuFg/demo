from PyQt6.QtWidgets import QMainWindow, QWidget, QScrollArea, QStackedWidget, QHBoxLayout, QVBoxLayout, QLabel, \
    QLineEdit, QComboBox, QPushButton, QRadioButton, QFrame, QMessageBox
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt
from DB.db import Database
from UI.ProductUi import ProductForm
from UI.OrderUi import OrdersWindow


class UserWindow(QMainWindow):
    def __init__(self, userName=None, userRole=None, userId=None):
        super().__init__()

        self.userName = userName
        self.userRole = userRole
        self.userId = userId

        self.db = Database()

        print(self.userName, self.userRole, self.userId)

        self.setWindowTitle("Обувной магазин")
        self.setWindowIcon(QIcon("res/icon/icon.png"))
        self.resize(900, 700)

        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        name_lbl = QLabel(f"{self.userRole} {self.userName}")
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        name_lbl.setStyleSheet("font-size: 14px; font-weight:bold;")
        main_layout.addWidget(name_lbl)

        # Админ панель
        admin_panel_widget = QWidget()
        admin_panel_layout = QHBoxLayout(admin_panel_widget)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Поиск")

        self.asc_rb = QRadioButton("Сортировка по возрастанию")
        self.asc_rb.setChecked(True)
        self.desc_rb = QRadioButton("Сортировка по убыванию")

        self.filter_combo = QComboBox()

        self.add_product_btn = QPushButton("Добавить товар")
        self.to_order_btn = QPushButton("Заказы")

        admin_panel_layout.addWidget(self.search)
        admin_panel_layout.addWidget(self.asc_rb)
        admin_panel_layout.addWidget(self.desc_rb)
        admin_panel_layout.addWidget(self.filter_combo)
        admin_panel_layout.addWidget(self.add_product_btn)
        admin_panel_layout.addWidget(self.to_order_btn)

        main_layout.addWidget(admin_panel_widget)

        # Скрываем панель для гостей и клиентов
        if self.userRole not in ["Администратор", "Менеджер"]:
            admin_panel_widget.hide()

        # Для менеджера скрываем кнопку добавления товара
        if self.userRole == "Менеджер":
            self.add_product_btn.hide()

        # Стек для страниц
        self.stack = QStackedWidget()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll.setWidget(self.stack)

        main_layout.addWidget(scroll)

        # Подключаем сигналы
        self.search.textChanged.connect(self.apply_filters)
        self.asc_rb.toggled.connect(self.apply_filters)
        self.desc_rb.toggled.connect(self.apply_filters)
        self.filter_combo.currentTextChanged.connect(self.apply_filters)
        self.add_product_btn.clicked.connect(self.open_add_form)
        self.to_order_btn.clicked.connect(self.open_orders)

        self.setCentralWidget(central_widget)

        self.fill_filters()
        self.apply_filters()

    def fill_filters(self):
        """Заполнение фильтра поставщиков"""
        data = self.db.get_providers()

        self.filter_combo.addItem("Все поставщики")
        try:
            for item in data:
                self.filter_combo.addItem(item[1])
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить поставщиков: {str(e)}")

    def apply_filters(self):
        """Применение фильтров и сортировки"""
        sort_order = 'ASC' if self.asc_rb.isChecked() else 'DESC'
        filter_by = self.filter_combo.currentText()
        search = self.search.text()

        self.filtered_data = self.db.main_data(sort_order, filter_by, search)
        self.show_page()

    def show_page(self):
        """Отображение товаров"""
        # Очищаем стек
        while self.stack.count():
            widget = self.stack.widget(0)
            self.stack.removeWidget(widget)
            widget.deleteLater()

        page_widget = QWidget()
        page_layout = QVBoxLayout(page_widget)

        for item in self.filtered_data:
            image = item[0]
            if image is None or image == "":
                image = "res/picture.png"
            else:
                image = f"res/image/{image}"

            self.get_data(image, item[1], item[2], item[3], item[4], item[5],
                          item[6], item[7], item[8], item[9], item[10], page_layout)

        self.stack.addWidget(page_widget)

    def get_data(self, image, category, name, description, manufacture, provider,
                 price, unit, quantity, current_discount, article, current_layout):
        """Создание карточки товара"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.Box)
        layout = QHBoxLayout()
        frame.setLayout(layout)

        # Фото товара
        photo_lbl = QLabel()
        photo_lbl.setMaximumSize(300, 200)
        try:
            photo = QPixmap(image)
            if not photo.isNull():
                photo = photo.scaled(300, 200, Qt.AspectRatioMode.KeepAspectRatio,
                                     Qt.TransformationMode.SmoothTransformation)
                photo_lbl.setPixmap(photo)
            else:
                photo = QPixmap("res/picture.png").scaled(300, 200)
                photo_lbl.setPixmap(photo)
        except:
            photo = QPixmap("res/picture.png").scaled(300, 200)
            photo_lbl.setPixmap(photo)
        photo_lbl.setFrameStyle(QFrame.Shape.Box)

        # Информация о товаре
        prod_frame = QFrame()
        prod_frame.setMaximumWidth(500)
        prod_frame.setFrameStyle(QFrame.Shape.Box)
        prod_desc_layout = QVBoxLayout(prod_frame)

        category_name_lbl = QLabel(f"{str(category)} | {str(name)}")
        category_name_lbl.setStyleSheet("font-size: 14px; font-weight:bold;")

        desc_lbl = QLabel(f"Описание товара: {str(description)}")
        desc_lbl.setWordWrap(True)
        man_lbl = QLabel(f"Производитель: {str(manufacture)}")
        prov_lbl = QLabel(f"Поставщик: {str(provider)}")

        price_layout = QHBoxLayout()
        price_lbl = QLabel(f"Цена: {str(price)}")
        price_layout.addWidget(price_lbl)

        unit_lbl = QLabel(f"Единица измерения: {str(unit)}")
        quantity_lbl = QLabel(f"Количество на складе: {str(quantity)}")

        discount_lbl = QLabel(f"Скидка: {str(current_discount)}%")

        # Применяем стили в зависимости от скидки
        if current_discount > 15:
            frame.setStyleSheet("background-color: #2E8B57;")
        elif current_discount > 0:
            price_lbl.setStyleSheet("text-decoration: line-through; color:red")
            new_price = float(price) - (float(price) * float(current_discount) / 100)
            price_new_lbl = QLabel(f"Новая цена: {str(round(new_price, 2))}")
            price_layout.addWidget(price_new_lbl)

        prod_desc_layout.addWidget(category_name_lbl)
        prod_desc_layout.addWidget(desc_lbl)
        prod_desc_layout.addWidget(man_lbl)
        prod_desc_layout.addWidget(prov_lbl)
        prod_desc_layout.addLayout(price_layout)
        prod_desc_layout.addWidget(unit_lbl)
        prod_desc_layout.addWidget(quantity_lbl)

        # Блок скидки и кнопок
        discount_frame = QFrame()
        discount_frame.setMaximumWidth(100)
        discount_frame.setFrameStyle(QFrame.Shape.Box)
        discount_layout = QVBoxLayout(discount_frame)

        if quantity == 0:
            frame.setStyleSheet("background-color: #87CEEB;")

        discount_layout.addWidget(discount_lbl)

        # Кнопка удаления для администратора
        if self.userRole == "Администратор":
            delete_btn = QPushButton("Удалить")
            delete_btn.clicked.connect(lambda checked, a=article: self.delete_product(a))
            discount_layout.addWidget(delete_btn)

        layout.addWidget(photo_lbl)
        layout.addWidget(prod_frame)
        layout.addWidget(discount_frame)

        # Двойной клик для редактирования (только админ)
        if self.userRole == "Администратор":
            frame.mouseDoubleClickEvent = lambda event, a=article: self.open_edit_form(a)

        current_layout.addWidget(frame)
        return frame

    def delete_product(self, article):
        """Удаление товара"""
        if self.db.is_product_in_orders(article):
            QMessageBox.warning(self, "Предупреждение",
                                "Невозможно удалить товар, так как он присутствует в заказах!\n"
                                "Сначала удалите все заказы с этим товаром.")
            return

        reply = QMessageBox.question(self, "Подтверждение удаления",
                                     f"Вы действительно хотите удалить товар с артикулом {article}?\n"
                                     "Это действие невозможно отменить!",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            if self.db.delete_product(article):
                QMessageBox.information(self, "Успех", "Товар успешно удален!")
                self.apply_filters()
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось удалить товар!")

    def open_add_form(self):
        """Открытие формы добавления товара"""
        dialog = ProductForm(self, self.db, None)
        if dialog.exec():
            self.apply_filters()

    def open_edit_form(self, article):
        """Открытие формы редактирования товара"""
        dialog = ProductForm(self, self.db, article)
        if dialog.exec():
            self.apply_filters()

    def open_orders(self):
        """Открытие окна заказов"""
        dialog = OrdersWindow(self, self.db, self.userRole)
        dialog.exec()