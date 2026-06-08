import pymysql
from pymysql import Error


class Database:
    def __init__(self):
        try:
            self.conn = pymysql.connect(host='localhost', user='root', password='root', database='shoes')
            self.cur = self.conn.cursor()
        except Error as e:
            print(f"Ошибка подключения к БД: {e}")
            raise

    def auth(self, login, passw):
        try:
            self.cur.execute(f"select * from users where login = '{login.strip()}' and passw = '{passw.strip()}'")
            data = self.cur.fetchall()
            return data if data else False
        except Error as e:
            print(f"Ошибка авторизации: {e}")
            return False

    def main_data(self, sort_order, filter_by, search):
        try:
            query = '''select * from main_data'''
            params, where = [], []
            if filter_by and filter_by != 'Все поставщики':
                where.append('provider_name = %s')
                params.append(filter_by)
            if search and search.strip():
                pattern = f"%{search}%"
                where.append('(product_form_name like %s or category_name like %s)')
                params.extend([pattern, pattern])
            if where:
                query += ' where ' + ' AND '.join(where)
            query += ' ORDER BY quantity ' + sort_order
            self.cur.execute(query, params)
            return self.cur.fetchall()
        except Error as e:
            print(f"Ошибка: {e}")
            return []

    def is_product_in_orders(self, article):
        try:
            self.cur.execute("SELECT COUNT(*) FROM orders_products WHERE product_id = %s", (article,))
            return self.cur.fetchone()[0] > 0
        except Error as e:
            print(f"Ошибка: {e}")
            return True

    def delete_product(self, article):
        try:
            self.cur.execute("SELECT image FROM product WHERE article = %s", (article,))
            result = self.cur.fetchone()
            self.cur.execute("DELETE FROM product WHERE article = %s", (article,))
            self.conn.commit()
            if result and result[0]:
                import os
                path = f"res/image/{result[0]}"
                if os.path.exists(path):
                    os.remove(path)
            return True
        except Error as e:
            print(f"Ошибка: {e}")
            self.conn.rollback()
            return False

    def add_product(self, product_form_id, product_form_name, category_id, description,
                    manufacture_id, provider_id, price, unit, quantity, discount, image):
        try:
            self.cur.execute("SELECT id_product_form FROM product_form WHERE product_form_name = %s", (product_form_name,))
            result = self.cur.fetchone()
            if result:
                product_form_id = result[0]
            else:
                self.cur.execute("INSERT INTO product_form (product_form_name) VALUES (%s)", (product_form_name,))
                product_form_id = self.cur.lastrowid

            self.cur.execute("SELECT MAX(CAST(article AS UNSIGNED)) FROM product")
            max_article = self.cur.fetchone()[0]
            new_article = str((max_article or 0) + 1)

            self.cur.execute("""INSERT INTO product 
                               (article, product_form_id, unit, price, provider_id, manufacture_id, category_id, 
                                current_discount, quantity, product_description, image)
                               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                             (new_article, product_form_id, unit, price, provider_id, manufacture_id, category_id,
                              discount, quantity, description, image))
            self.conn.commit()
            return True
        except Error as e:
            print(f"Ошибка: {e}")
            self.conn.rollback()
            return False

    def update_product(self, article, product_form_id, product_form_name, category_id, description,
                       manufacture_id, provider_id, price, unit, quantity, discount, image):
        try:
            self.cur.execute("SELECT id_product_form FROM product_form WHERE product_form_name = %s", (product_form_name,))
            result = self.cur.fetchone()
            if result:
                product_form_id = result[0]
            else:
                self.cur.execute("INSERT INTO product_form (product_form_name) VALUES (%s)", (product_form_name,))
                product_form_id = self.cur.lastrowid

            self.cur.execute("""UPDATE product SET product_form_id = %s, unit = %s, price = %s, provider_id = %s,
                                manufacture_id = %s, category_id = %s, current_discount = %s,
                                quantity = %s, product_description = %s, image = %s WHERE article = %s""",
                             (product_form_id, unit, price, provider_id, manufacture_id, category_id, discount,
                              quantity, description, image, article))
            self.conn.commit()
            return True
        except Error as e:
            print(f"Ошибка: {e}")
            self.conn.rollback()
            return False

    def get_product_by_article(self, article):
        try:
            self.cur.execute("""SELECT p.image, p.product_form_id, p.category_id, p.product_description,
                               p.manufacture_id, p.provider_id, p.price, p.unit, p.quantity, p.current_discount
                               FROM product p WHERE p.article = %s""", (article,))
            return self.cur.fetchone()
        except Error as e:
            print(f"Ошибка: {e}")
            return None

    def get_product_forms(self):
        try:
            self.cur.execute("SELECT id_product_form, product_form_name FROM product_form ORDER BY product_form_name")
            return self.cur.fetchall()
        except Error as e:
            return []

    def get_categories(self):
        try:
            self.cur.execute("SELECT id_product_category, category_name FROM product_category ORDER BY category_name")
            return self.cur.fetchall()
        except Error as e:
            return []

    def get_manufactures(self):
        try:
            self.cur.execute("SELECT id_manufacture, manufacture_name FROM manufactures ORDER BY manufacture_name")
            return self.cur.fetchall()
        except Error as e:
            return []

    def get_providers(self):
        try:
            self.cur.execute("SELECT id_provider, provider_name FROM providers ORDER BY provider_name")
            return self.cur.fetchall()
        except Error as e:
            return []

    def get_orders(self, search=None):
        try:
            query = """SELECT o.id_order, o.order_date, o.delivery_date, s.city, s.street, s.house,
                              u.last_name, u.first_name, u.family_name, st.status_name, o.code_for_get
                       FROM orders o JOIN order_station s ON o.order_station_id = s.id_station
                       JOIN users u ON o.client_id = u.id_user JOIN order_statuses st ON o.status_id = st.id_status"""
            params, where = [], []
            if search and search.strip():
                where.append("(CAST(o.id_order AS CHAR) LIKE %s OR o.code_for_get LIKE %s)")
                params.extend([f"%{search}%", f"%{search}%"])
            if where:
                query += " WHERE " + " AND ".join(where)
            query += " ORDER BY o.id_order DESC"
            self.cur.execute(query, params)
            return self.cur.fetchall()
        except Error as e:
            print(f"Ошибка получения заказов: {e}")
            return []

    def get_order_products(self, order_id):
        try:
            self.cur.execute("""SELECT op.product_id, p.article, pf.product_form_name, op.quantity, p.price
                FROM orders_products op JOIN product p ON op.product_id = p.article
                JOIN product_form pf ON p.product_form_id = pf.id_product_form WHERE op.order_id = %s""", (order_id,))
            return self.cur.fetchall()
        except Error as e:
            return []

    def get_order_stations(self):
        try:
            self.cur.execute("SELECT id_station, city, street, house, indexes FROM order_station ORDER BY city, street, house")
            return self.cur.fetchall()
        except Error as e:
            return []

    def get_order_statuses(self):
        try:
            self.cur.execute("SELECT id_status, status_name FROM order_statuses ORDER BY status_name")
            return self.cur.fetchall()
        except Error as e:
            return []

    def get_clients(self):
        try:
            self.cur.execute("SELECT id_user, last_name, first_name, family_name, login FROM users ORDER BY last_name")
            return self.cur.fetchall()
        except Error as e:
            return []

    def get_products(self):
        try:
            self.cur.execute("""SELECT article, pf.product_form_name, p.price, p.quantity
                FROM product p JOIN product_form pf ON p.product_form_id = pf.id_product_form WHERE p.quantity > 0""")
            return self.cur.fetchall()
        except Error as e:
            return []

    def add_order(self, client_id, station_id, delivery_date, status_id, code_for_get, products):
        try:
            self.cur.execute("""INSERT INTO orders (client_id, order_station_id, delivery_date, status_id, code_for_get, order_date)
                VALUES (%s, %s, %s, %s, %s, CURDATE())""", (client_id, station_id, delivery_date, status_id, code_for_get))
            order_id = self.cur.lastrowid
            for product_id, quantity in products:
                self.cur.execute("INSERT INTO orders_products (order_id, product_id, quantity) VALUES (%s, %s, %s)",
                                 (order_id, product_id, quantity))
                self.cur.execute("UPDATE product SET quantity = quantity - %s WHERE article = %s", (quantity, product_id))
            self.conn.commit()
            return True
        except Error as e:
            print(f"Ошибка добавления заказа: {e}")
            self.conn.rollback()
            return False

    def update_order(self, order_id, client_id, station_id, delivery_date, status_id, code_for_get):
        try:
            self.cur.execute("""UPDATE orders SET client_id = %s, order_station_id = %s, delivery_date = %s,
                status_id = %s, code_for_get = %s WHERE id_order = %s""",
                (client_id, station_id, delivery_date, status_id, code_for_get, order_id))
            self.conn.commit()
            return True
        except Error as e:
            print(f"Ошибка обновления заказа: {e}")
            self.conn.rollback()
            return False

    def delete_order(self, order_id):
        try:
            self.cur.execute("SELECT product_id, quantity FROM orders_products WHERE order_id = %s", (order_id,))
            for product_id, quantity in self.cur.fetchall():
                self.cur.execute("UPDATE product SET quantity = quantity + %s WHERE article = %s", (quantity, product_id))
            self.cur.execute("DELETE FROM orders_products WHERE order_id = %s", (order_id,))
            self.cur.execute("DELETE FROM orders WHERE id_order = %s", (order_id,))
            self.conn.commit()
            return True
        except Error as e:
            print(f"Ошибка удаления заказа: {e}")
            self.conn.rollback()
            return False

    def get_order_by_id(self, order_id):
        try:
            self.cur.execute("""SELECT o.id_order, o.order_date, o.delivery_date, o.order_station_id,
                o.client_id, o.status_id, o.code_for_get FROM orders o WHERE o.id_order = %s""", (order_id,))
            return self.cur.fetchone()
        except Error as e:
            return None

    def get_order_total(self, order_id):
        try:
            self.cur.execute("""SELECT SUM(p.price * op.quantity) FROM orders_products op JOIN product p ON op.product_id = p.article
                WHERE op.order_id = %s""", (order_id,))
            result = self.cur.fetchone()
            return result[0] if result and result[0] else 0
        except Error as e:
            return 0

    def __del__(self):
        try:
            if hasattr(self, 'cur'): self.cur.close()
            if hasattr(self, 'conn'): self.conn.close()
        except:
            pass
