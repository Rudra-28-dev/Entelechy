import mysql.connector

from db_config import get_db_config


class Database:
    def __init__(self):
        self.db = mysql.connector.connect(**get_db_config())
        self.cursor = self.db.cursor(dictionary=True)
        self.ensure_subadmin_table()

    # ---------------- USERS ---------------- #

    def register_user(self, data):
        try:
            query = """
            INSERT INTO USERS 
            (USERNAME, EMAIL, PASSWORD, PHONE, ADDRESS, FIRST_NAME, LAST_NAME, GENDER, PROFILE_PICTURE)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """

            values = (
                data.get('username'),
                data.get('email'),
                data.get('password'),
                data.get('phone'),
                data.get('address'),
                data.get('first_name'),
                data.get('last_name'),
                data.get('gender'),
                data.get('profile_picture')
            )

            self.cursor.execute(query, values)
            self.db.commit()
            return True

        except mysql.connector.Error as err:
            print("REGISTER ERROR:", err)
            return False

    def login_user(self, email, password):
        try:
            query = "SELECT * FROM USERS WHERE EMAIL=%s AND PASSWORD=%s"
            self.cursor.execute(query, (email, password))
            return self.cursor.fetchone()

        except mysql.connector.Error as err:
            print("LOGIN ERROR:", err)
            return None

    def get_user_by_id(self, user_id):
        try:
            query = "SELECT * FROM USERS WHERE USER_ID=%s"
            self.cursor.execute(query, (user_id,))
            return self.cursor.fetchone()

        except mysql.connector.Error as err:
            print("GET USER ERROR:", err)
            return None

    # ---------------- SUB ADMINS ---------------- #

    def ensure_subadmin_table(self):
        try:
            query = """
            CREATE TABLE IF NOT EXISTS SUBADMINS (
                SUBADMIN_ID INT AUTO_INCREMENT PRIMARY KEY,
                USERNAME VARCHAR(50) NOT NULL UNIQUE,
                EMAIL VARCHAR(100) NOT NULL UNIQUE,
                PASSWORD VARCHAR(255) NOT NULL,
                CREATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            self.cursor.execute(query)
            self.db.commit()

        except mysql.connector.Error as err:
            print("SUBADMIN TABLE ERROR:", err)

    def register_subadmin(self, data):
        try:
            query = """
            INSERT INTO SUBADMINS (USERNAME, EMAIL, PASSWORD)
            VALUES (%s,%s,%s)
            """
            self.cursor.execute(
                query,
                (
                    data.get('username'),
                    data.get('email'),
                    data.get('password')
                )
            )
            self.db.commit()
            return True

        except mysql.connector.Error as err:
            print("REGISTER SUBADMIN ERROR:", err)
            return False

    def login_subadmin(self, email, password):
        try:
            query = "SELECT * FROM SUBADMINS WHERE EMAIL=%s AND PASSWORD=%s"
            self.cursor.execute(query, (email, password))
            return self.cursor.fetchone()

        except mysql.connector.Error as err:
            print("LOGIN SUBADMIN ERROR:", err)
            return None

    def get_subadmin_by_id(self, subadmin_id):
        try:
            query = "SELECT * FROM SUBADMINS WHERE SUBADMIN_ID=%s"
            self.cursor.execute(query, (subadmin_id,))
            return self.cursor.fetchone()

        except mysql.connector.Error as err:
            print("GET SUBADMIN ERROR:", err)
            return None

    # ---------------- PRODUCTS ---------------- #

    def get_products(self):
        try:
            query = """
            SELECT p.*, c.CATEGORY_NAME, m.MATERIAL_NAME
            FROM JEWELRY_PRODUCT p
            JOIN CATEGORY c ON p.CATEGORY_ID = c.CATEGORY_ID
            JOIN MATERIAL m ON p.MATERIAL_ID = m.MATERIAL_ID
            """
            self.cursor.execute(query)
            return self.cursor.fetchall()

        except mysql.connector.Error as err:
            print("GET PRODUCTS ERROR:", err)
            return []

    def get_product(self, product_id):
        try:
            query = """
            SELECT p.*, c.CATEGORY_NAME, m.MATERIAL_NAME
            FROM JEWELRY_PRODUCT p
            JOIN CATEGORY c ON p.CATEGORY_ID = c.CATEGORY_ID
            JOIN MATERIAL m ON p.MATERIAL_ID = m.MATERIAL_ID
            WHERE p.PRODUCT_ID=%s
            """
            self.cursor.execute(query, (product_id,))
            return self.cursor.fetchone()

        except mysql.connector.Error as err:
            print("GET PRODUCT ERROR:", err)
            return None

    def get_or_create_category(self, category_name):
        try:
            cleaned_name = category_name.strip()
            self.cursor.execute(
                "SELECT CATEGORY_ID FROM CATEGORY WHERE LOWER(CATEGORY_NAME)=LOWER(%s)",
                (cleaned_name,)
            )
            category = self.cursor.fetchone()

            if category:
                return category['CATEGORY_ID']

            self.cursor.execute(
                "INSERT INTO CATEGORY (CATEGORY_NAME) VALUES (%s)",
                (cleaned_name,)
            )
            self.db.commit()
            return self.cursor.lastrowid

        except mysql.connector.Error as err:
            print("CATEGORY UPSERT ERROR:", err)
            return None

    def get_or_create_material(self, material_name):
        try:
            cleaned_name = material_name.strip()
            self.cursor.execute(
                "SELECT MATERIAL_ID FROM MATERIAL WHERE LOWER(MATERIAL_NAME)=LOWER(%s)",
                (cleaned_name,)
            )
            material = self.cursor.fetchone()

            if material:
                return material['MATERIAL_ID']

            self.cursor.execute(
                "INSERT INTO MATERIAL (MATERIAL_NAME) VALUES (%s)",
                (cleaned_name,)
            )
            self.db.commit()
            return self.cursor.lastrowid

        except mysql.connector.Error as err:
            print("MATERIAL UPSERT ERROR:", err)
            return None

    def create_product(self, data):
        try:
            category_id = self.get_or_create_category(data.get('category', ''))
            material_id = self.get_or_create_material(data.get('material', ''))

            if not category_id or not material_id:
                return False

            query = """
            INSERT INTO JEWELRY_PRODUCT
            (PRODUCT_NAME, DESCRIPTION, PRICE, STOCK_QUANTITY, IMAGE_URL, WEIGHT, CATEGORY_ID, MATERIAL_ID)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """
            self.cursor.execute(
                query,
                (
                    data.get('product_name'),
                    data.get('description'),
                    data.get('price'),
                    data.get('stock_quantity'),
                    data.get('image_url'),
                    data.get('weight'),
                    category_id,
                    material_id
                )
            )
            self.db.commit()
            return True

        except mysql.connector.Error as err:
            print("CREATE PRODUCT ERROR:", err)
            return False

    def update_product(self, product_id, data):
        try:
            category_id = self.get_or_create_category(data.get('category', ''))
            material_id = self.get_or_create_material(data.get('material', ''))

            if not category_id or not material_id:
                return False

            query = """
            UPDATE JEWELRY_PRODUCT
            SET PRODUCT_NAME=%s,
                DESCRIPTION=%s,
                PRICE=%s,
                STOCK_QUANTITY=%s,
                IMAGE_URL=%s,
                WEIGHT=%s,
                CATEGORY_ID=%s,
                MATERIAL_ID=%s
            WHERE PRODUCT_ID=%s
            """
            self.cursor.execute(
                query,
                (
                    data.get('product_name'),
                    data.get('description'),
                    data.get('price'),
                    data.get('stock_quantity'),
                    data.get('image_url'),
                    data.get('weight'),
                    category_id,
                    material_id,
                    product_id
                )
            )
            self.db.commit()
            return True

        except mysql.connector.Error as err:
            print("UPDATE PRODUCT ERROR:", err)
            return False

    def delete_product(self, product_id):
        try:
            self.cursor.execute(
                "DELETE FROM SHOPPING_CART WHERE PRODUCT_ID=%s",
                (product_id,)
            )
            self.cursor.execute(
                "DELETE FROM ORDER_ITEM WHERE PRODUCT_ID=%s",
                (product_id,)
            )
            self.cursor.execute(
                "DELETE FROM JEWELRY_PRODUCT WHERE PRODUCT_ID=%s",
                (product_id,)
            )
            self.db.commit()
            return True

        except mysql.connector.Error as err:
            print("DELETE PRODUCT ERROR:", err)
            return False

    # ---------------- CART ---------------- #

    def add_to_cart(self, user_id, product_id, quantity):
        try:
            self.cursor.execute(
                "SELECT CART_ID, QUANTITY FROM SHOPPING_CART WHERE USER_ID=%s AND PRODUCT_ID=%s",
                (user_id, product_id)
            )
            existing_item = self.cursor.fetchone()

            if existing_item:
                self.cursor.execute(
                    "UPDATE SHOPPING_CART SET QUANTITY=%s WHERE CART_ID=%s",
                    (existing_item['QUANTITY'] + quantity, existing_item['CART_ID'])
                )
            else:
                self.cursor.execute(
                    "INSERT INTO SHOPPING_CART (USER_ID, PRODUCT_ID, QUANTITY) VALUES (%s,%s,%s)",
                    (user_id, product_id, quantity)
                )

            self.db.commit()
            return True

        except mysql.connector.Error as err:
            print("ADD TO CART ERROR:", err)
            return False

    def get_cart(self, user_id):
        try:
            query = """
            SELECT 
                c.CART_ID,
                c.USER_ID,
                c.PRODUCT_ID,
                c.QUANTITY,
                p.PRODUCT_NAME,
                p.PRICE,
                p.IMAGE_URL
            FROM SHOPPING_CART c
            JOIN JEWELRY_PRODUCT p 
                ON c.PRODUCT_ID = p.PRODUCT_ID
            WHERE c.USER_ID = %s
            """
            self.cursor.execute(query, (user_id,))
            return self.cursor.fetchall()

        except mysql.connector.Error as err:
            print("GET CART ERROR:", err)
            return []

    def clear_cart(self, user_id):
        try:
            self.cursor.execute(
                "DELETE FROM SHOPPING_CART WHERE USER_ID=%s",
                (user_id,)
            )
            self.db.commit()

        except mysql.connector.Error as err:
            print("CLEAR CART ERROR:", err)

    def get_order_count(self, user_id):
        try:
            self.cursor.execute(
                "SELECT COUNT(*) AS TOTAL_ORDERS FROM ORDERS WHERE USER_ID=%s",
                (user_id,)
            )
            result = self.cursor.fetchone()
            return result['TOTAL_ORDERS'] if result else 0

        except mysql.connector.Error as err:
            print("ORDER COUNT ERROR:", err)
            return 0

    # ---------------- ORDER FLOW ---------------- #

    def create_order(self, user_id, total_price, payment_method):
        try:
            query = """
            INSERT INTO ORDERS (USER_ID, TOTAL_PRICE, ORDER_STATUS, PAYMENT_METHOD, PAYMENT_STATUS)
            VALUES (%s,%s,'PENDING',%s,'PENDING')
            """
            self.cursor.execute(query, (user_id, total_price, payment_method))
            self.db.commit()
            return self.cursor.lastrowid

        except mysql.connector.Error as err:
            print("CREATE ORDER ERROR:", err)
            return None

    def add_order_items(self, order_id, cart_items):
        try:
            for item in cart_items:
                query = """
                INSERT INTO ORDER_ITEM (ORDER_ID, PRODUCT_ID, QUANTITY, PRICE_AT_PURCHASE)
                VALUES (%s,%s,%s,%s)
                """
                self.cursor.execute(query, (
                    order_id,
                    item['PRODUCT_ID'],
                    item['QUANTITY'],
                    item['PRICE']
                ))
            self.db.commit()

        except mysql.connector.Error as err:
            print("ORDER ITEMS ERROR:", err)

    # ---------------- PAYMENT ---------------- #

    def add_payment(self, order_id, amount, method):
        try:
            query = """
            INSERT INTO PAYMENT (ORDER_ID, AMOUNT, PAYMENT_METHOD, PAYMENT_STATUS)
            VALUES (%s,%s,%s,'COMPLETED')
            """
            self.cursor.execute(query, (order_id, amount, method))
            self.db.commit()

        except mysql.connector.Error as err:
            print("PAYMENT ERROR:", err)

    # ---------------- SHIPPING ---------------- #

    def add_shipping(self, order_id, address):
        try:
            query = """
            INSERT INTO SHIPPING (ORDER_ID, SHIPPING_ADDRESS, SHIPPING_STATUS)
            VALUES (%s,%s,'PENDING')
            """
            self.cursor.execute(query, (order_id, address))
            self.db.commit()

        except mysql.connector.Error as err:
            print("SHIPPING ERROR:", err)
