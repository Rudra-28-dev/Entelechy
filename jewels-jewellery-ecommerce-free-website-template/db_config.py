import os


def get_env_value(*keys, default=None):
    for key in keys:
        value = os.getenv(key)
        if value is not None and value.strip() != "":
            return value
    return default


def get_db_config():
    return {
        "host": get_env_value("MYSQLHOST", "DB_HOST", default="localhost"),
        "port": int(get_env_value("MYSQLPORT", "DB_PORT", default="3306")),
        "user": get_env_value("MYSQLUSER", "DB_USER", default="root"),
        "password": get_env_value("MYSQLPASSWORD", "DB_PASSWORD", default="Rudra28"),
        "database": get_env_value("MYSQLDATABASE", "DB_NAME", default="JEWELRY"),
    }
