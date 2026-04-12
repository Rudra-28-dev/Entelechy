import random
from decimal import Decimal

import mysql.connector

from db_config import get_db_config


TARGET_COUNT = 30

IMAGE_FILES = [
    "product-item1.jpg",
    "product-item2.jpg",
    "product-item3.jpg",
    "product-item4.jpg",
    "product-item5.jpg",
    "product-item6.jpg",
    "product-item7.jpg",
    "product-item8.jpg",
    "product-item9.jpg",
    "product-item10.jpg",
    "product-item11.jpg",
    "product-item12.jpg",
]

FIRST_NAMES = [
    "Aarav", "Diya", "Vivaan", "Anaya", "Krish", "Myra", "Ishaan", "Kiara",
    "Reyansh", "Saanvi", "Arjun", "Aadhya", "Rohan", "Meera", "Kabir", "Naina",
    "Yash", "Riya", "Dev", "Tara", "Aryan", "Simran", "Neel", "Pihu",
    "Om", "Ira", "Shaurya", "Avni", "Parth", "Trisha",
]

LAST_NAMES = [
    "Patel", "Shah", "Mehta", "Rao", "Nair", "Kapoor", "Desai", "Joshi",
    "Iyer", "Agarwal", "Bose", "Jain", "Bhatt", "Verma", "Malhotra",
]

PRODUCT_PREFIXES = [
    "Aurora", "Regal", "Celeste", "Opal", "Imperial", "Luxe", "Twilight",
    "Radiant", "Noor", "Velvet", "Solstice", "Heritage",
]

PRODUCT_TYPES = {
    "Women": ["Earrings", "Bracelet", "Pendant", "Anklet", "Ring"],
    "Men": ["Band", "Chain", "Bracelet", "Brooch", "Ring"],
    "Classic": ["Necklace", "Ring", "Pendant", "Bracelet", "Studs"],
}

ORDER_STATUSES = ["PENDING", "SHIPPED", "DELIVERED", "CANCELLED"]
PAYMENT_METHODS = ["COD", "UPI", "CARD", "NET_BANKING"]
PAYMENT_STATUSES = ["PENDING", "COMPLETED", "FAILED"]
SHIPPING_STATUSES = ["PENDING", "IN_TRANSIT", "DELIVERED"]


def fetch_count(cursor, table_name):
    cursor.execute(f"SELECT COUNT(*) AS total FROM {table_name}")
    return cursor.fetchone()["total"]


def next_seed_number(cursor, table_name, column_name, prefix):
    cursor.execute(
        f"SELECT {column_name} AS value FROM {table_name} "
        f"WHERE {column_name} LIKE %s ORDER BY {column_name}",
        (f"{prefix}%",),
    )
    max_number = 0
    for row in cursor.fetchall():
        suffix = str(row["value"]).replace(prefix, "")
        if suffix.isdigit():
            max_number = max(max_number, int(suffix))
    return max_number + 1


def seed_users(cursor, conn):
    current_count = fetch_count(cursor, "USERS")
    to_add = max(0, TARGET_COUNT - current_count)
    if to_add == 0:
        return

    start_number = next_seed_number(cursor, "USERS", "USERNAME", "seed_user_")

    insert_sql = """
        INSERT INTO USERS
        (USERNAME, EMAIL, PASSWORD, PHONE, ADDRESS, FIRST_NAME, LAST_NAME, GENDER, PROFILE_PICTURE)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    for offset in range(to_add):
        number = start_number + offset
        first_name = FIRST_NAMES[offset % len(FIRST_NAMES)]
        last_name = LAST_NAMES[offset % len(LAST_NAMES)]
        gender = ["MALE", "FEMALE", "OTHER"][offset % 3]
        username = f"seed_user_{number:03d}"
        email = f"seed_user_{number:03d}@entelechy.demo"
        phone = f"900000{number:04d}"
        address = f"House {number}, Jewel Avenue, Gandhinagar, Gujarat"
        profile_picture = f"profile_{(offset % 6) + 1}.png"

        cursor.execute(
            insert_sql,
            (
                username,
                email,
                "demo123",
                phone,
                address,
                first_name,
                last_name,
                gender,
                profile_picture,
            ),
        )

    conn.commit()


def seed_products(cursor, conn):
    current_count = fetch_count(cursor, "JEWELRY_PRODUCT")
    to_add = max(0, TARGET_COUNT - current_count)
    if to_add == 0:
        return

    cursor.execute("SELECT CATEGORY_ID, CATEGORY_NAME FROM CATEGORY ORDER BY CATEGORY_ID")
    categories = cursor.fetchall()
    cursor.execute("SELECT MATERIAL_ID, MATERIAL_NAME FROM MATERIAL ORDER BY MATERIAL_ID")
    materials = cursor.fetchall()

    if not categories or not materials:
        raise RuntimeError("CATEGORY and MATERIAL must contain data before seeding products.")

    start_number = next_seed_number(cursor, "JEWELRY_PRODUCT", "PRODUCT_NAME", "Seed Product ")

    insert_sql = """
        INSERT INTO JEWELRY_PRODUCT
        (PRODUCT_NAME, DESCRIPTION, PRICE, STOCK_QUANTITY, IMAGE_URL, WEIGHT, CATEGORY_ID, MATERIAL_ID)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    for offset in range(to_add):
        number = start_number + offset
        category = categories[offset % len(categories)]
        material = materials[offset % len(materials)]
        product_type = PRODUCT_TYPES[category["CATEGORY_NAME"]][offset % len(PRODUCT_TYPES[category["CATEGORY_NAME"]])]
        prefix = PRODUCT_PREFIXES[offset % len(PRODUCT_PREFIXES)]
        product_name = f"Seed Product {number:03d} {prefix} {product_type}"
        description = (
            f"{prefix} {product_type.lower()} for the {category['CATEGORY_NAME'].lower()} collection, "
            f"crafted in {material['MATERIAL_NAME'].lower()} with a polished premium finish."
        )
        price = Decimal(str(1499 + (offset * 185)))
        stock_quantity = 6 + (offset % 20)
        image_url = IMAGE_FILES[offset % len(IMAGE_FILES)]
        weight = Decimal(f"{4 + (offset % 8)}.{(offset * 7) % 10}0")

        cursor.execute(
            insert_sql,
            (
                product_name,
                description,
                price,
                stock_quantity,
                image_url,
                weight,
                category["CATEGORY_ID"],
                material["MATERIAL_ID"],
            ),
        )

    conn.commit()


def seed_orders_related(cursor, conn):
    order_count = fetch_count(cursor, "ORDERS")
    payment_count = fetch_count(cursor, "PAYMENT")
    shipping_count = fetch_count(cursor, "SHIPPING")
    target_existing = max(order_count, payment_count, shipping_count)
    to_add = max(0, TARGET_COUNT - target_existing)
    if to_add == 0:
        return

    cursor.execute("SELECT USER_ID, ADDRESS FROM USERS ORDER BY USER_ID")
    users = cursor.fetchall()
    cursor.execute("SELECT PRODUCT_ID, PRICE FROM JEWELRY_PRODUCT ORDER BY PRODUCT_ID")
    products = cursor.fetchall()

    if not users or not products:
        raise RuntimeError("USERS and JEWELRY_PRODUCT must contain data before seeding orders.")

    order_sql = """
        INSERT INTO ORDERS
        (USER_ID, TOTAL_PRICE, ORDER_STATUS, PAYMENT_METHOD, PAYMENT_STATUS)
        VALUES (%s, %s, %s, %s, %s)
    """
    order_item_sql = """
        INSERT INTO ORDER_ITEM
        (ORDER_ID, PRODUCT_ID, QUANTITY, PRICE_AT_PURCHASE)
        VALUES (%s, %s, %s, %s)
    """
    payment_sql = """
        INSERT INTO PAYMENT
        (ORDER_ID, AMOUNT, PAYMENT_METHOD, PAYMENT_STATUS)
        VALUES (%s, %s, %s, %s)
    """
    shipping_sql = """
        INSERT INTO SHIPPING
        (ORDER_ID, SHIPPING_ADDRESS, SHIPPING_STATUS)
        VALUES (%s, %s, %s)
    """

    for offset in range(to_add):
        user = users[offset % len(users)]
        product = products[offset % len(products)]
        quantity = (offset % 3) + 1
        price_at_purchase = Decimal(str(product["PRICE"]))
        total_price = price_at_purchase * quantity
        payment_method = PAYMENT_METHODS[offset % len(PAYMENT_METHODS)]
        payment_status = PAYMENT_STATUSES[offset % len(PAYMENT_STATUSES)]

        if payment_status == "COMPLETED":
            order_status = ORDER_STATUSES[(offset + 1) % 3]
            shipping_status = SHIPPING_STATUSES[(offset + 1) % len(SHIPPING_STATUSES)]
        elif payment_status == "FAILED":
            order_status = "CANCELLED"
            shipping_status = "PENDING"
        else:
            order_status = "PENDING"
            shipping_status = "PENDING"

        cursor.execute(
            order_sql,
            (
                user["USER_ID"],
                total_price,
                order_status,
                payment_method,
                payment_status,
            ),
        )
        order_id = cursor.lastrowid

        cursor.execute(
            order_item_sql,
            (
                order_id,
                product["PRODUCT_ID"],
                quantity,
                price_at_purchase,
            ),
        )
        cursor.execute(
            payment_sql,
            (
                order_id,
                total_price,
                payment_method,
                payment_status,
            ),
        )
        cursor.execute(
            shipping_sql,
            (
                order_id,
                user["ADDRESS"],
                shipping_status,
            ),
        )

    conn.commit()


def main():
    random.seed(42)
    conn = mysql.connector.connect(**get_db_config())
    cursor = conn.cursor(dictionary=True)

    try:
        seed_users(cursor, conn)
        seed_products(cursor, conn)
        seed_orders_related(cursor, conn)

        print("Final counts:")
        for table in ["USERS", "JEWELRY_PRODUCT", "ORDERS", "ORDER_ITEM", "PAYMENT", "SHIPPING"]:
            print(f"  {table}: {fetch_count(cursor, table)}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
