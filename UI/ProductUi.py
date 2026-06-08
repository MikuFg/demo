import os, shutil
from PyQt6.QtWidgets import QDialog, QFormLayout, QVBoxLayout, QHBoxLayout, QLabel, \
    QLineEdit, QComboBox, QTextEdit, QSpinBox, QDoubleSpinBox, QFileDialog, QMessageBox, QPushButton
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt
from DB.db import Database


class ProductForm(QDialog):
    def __init__(self, parent=None, db=None, article=None):
        super().__init__(parent)
        self.db = db or Database()
        self.article = article
        self.image_path = None
        self.old_image = None

        self.setWindowIcon(QIcon("res/icon/icon.png"))
        self.resize(600, 550)
        self.setWindowTitle("Редактирование товара" if article else "Добавление товара")

        self.init_ui()
        self.load_combo_boxes()
        if article:
            self.load_product_data()

    def init_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()

        self.image_label = QLabel("Нет изображения")
        self.image_label.setFixedSize(300, 200)
        self.image_label.setStyleSheet("border:1px solid gray")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form.addRow("Фото:", self.image_label)

        self.select_image_btn = QPushButton("Выбрать")
        self.select_image_btn.clicked.connect(self.select_image)
        form.addRow("", self.select_image_btn)

        self.name = QComboBox()
        self.name.setEditable(True)
        form.addRow("Наименование:", self.name)

        self.category = QComboBox()
        form.addRow("Категория:", self.category)

        self.desc = QTextEdit()
        self.desc.setMaximumHeight(80)
        form.addRow("Описание:", self.desc)

        self.manufacture = QComboBox()
        form.addRow("Производитель:", self.manufacture)

        self.provider = QComboBox()
        form.addRow("Поставщик:", self.provider)

        self.price = QDoubleSpinBox()
        self.price.setRange(0, 999999)
        self.price.setDecimals(2)
        form.addRow("Цена:", self.price)

        self.unit = QLineEdit()
        form.addRow("Ед.измерения:", self.unit)

        self.quantity = QSpinBox()
        self.quantity.setRange(0, 999999)
        form.addRow("Количество:", self.quantity)

        self.discount = QSpinBox()
        self.discount.setRange(0, 100)
        self.discount.setSuffix("%")
        form.addRow("Скидка:", self.discount)

        self.article_edit = QLineEdit()
        self.article_edit.setReadOnly(True)
        form.addRow("Артикул:", self.article_edit)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(QPushButton("Назад", clicked=self.reject))
        btn_layout.addWidget(QPushButton("Сохранить", clicked=self.save_data))
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_combo_boxes(self):
        for data, combo in [(self.db.get_product_forms(), self.name),
                            (self.db.get_categories(), self.category),
                            (self.db.get_manufactures(), self.manufacture),
                            (self.db.get_providers(), self.provider)]:
            for item in data:
                combo.addItem(item[1], item[0])

    def select_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите изображение", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            pixmap = QPixmap(path)
            if pixmap.width() != 300 or pixmap.height() != 200:
                if QMessageBox.question(self, "Размер", f"Изменить до 300x200?") == QMessageBox.StandardButton.Yes:
                    pixmap = pixmap.scaled(300, 200)
                else:
                    return
            self.image_path = path
            self.image_label.setPixmap(pixmap)

    def save_image(self):
        if self.image_path:
            os.makedirs("res/image", exist_ok=True)
            new_name = f"prod_{self.article or 'new'}_{os.path.basename(self.image_path)}"
            new_path = os.path.join("res/image", new_name)
            shutil.copy2(self.image_path, new_path)
            if self.old_image and os.path.exists(f"res/image/{self.old_image}"):
                os.remove(f"res/image/{self.old_image}")
            return new_name
        return self.old_image

    def load_product_data(self):
        p = self.db.get_product_by_article(self.article)
        if p:
            if p[0] and os.path.exists(f"res/image/{p[0]}"):
                self.image_label.setPixmap(QPixmap(f"res/image/{p[0]}").scaled(300, 200))
                self.old_image = p[0]
            for combo, val in [(self.name, p[1]), (self.category, p[2]),
                               (self.manufacture, p[4]), (self.provider, p[5])]:
                idx = combo.findData(val)
                if idx >= 0: combo.setCurrentIndex(idx)
            self.desc.setText(str(p[3] or ""))
            self.price.setValue(float(p[6] or 0))
            self.unit.setText(str(p[7] or ""))
            self.quantity.setValue(int(p[8] or 0))
            self.discount.setValue(int(p[9] or 0))
            self.article_edit.setText(str(self.article))

    def save_data(self):
        if not self.name.currentText().strip():
            return QMessageBox.warning(self, "Ошибка", "Введите наименование!")
        if self.price.value() <= 0:
            return QMessageBox.warning(self, "Ошибка", "Цена > 0!")

        img = self.save_image()

        kwargs = {
            'product_form_id': self.name.currentData(),
            'product_form_name': self.name.currentText(),
            'category_id': self.category.currentData(),
            'description': self.desc.toPlainText(),
            'manufacture_id': self.manufacture.currentData(),
            'provider_id': self.provider.currentData(),
            'price': self.price.value(),
            'unit': self.unit.text(),
            'quantity': self.quantity.value(),
            'discount': self.discount.value(),
            'image': img
        }

        if self.article:
            kwargs['article'] = self.article
            ok = self.db.update_product(**kwargs)
        else:
            ok = self.db.add_product(**kwargs)

        if ok:
            QMessageBox.information(self, "Успех", "Товар сохранен!")
            self.accept()
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось сохранить!")
