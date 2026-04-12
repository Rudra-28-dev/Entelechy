import os


def get_db_config():
    return {
        "host": os.getenv("MYSQLHOST", os.getenv("DB_HOST", "localhost")),
        "port": int(os.getenv("MYSQLPORT", os.getenv("DB_PORT", "3306"))),
        "user": os.getenv("MYSQLUSER", os.getenv("DB_USER", "root")),
        "password": os.getenv("MYSQLPASSWORD", os.getenv("DB_PASSWORD", "Rudra28")),
        "database": os.getenv("MYSQLDATABASE", os.getenv("DB_NAME", "JEWELRY")),
    }
