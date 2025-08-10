import pymysql
import os
from dotenv import load_dotenv

# تحميل المتغيرات البيئية
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# الاتصال بقاعدة البيانات
def get_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

# تنفيذ استعلام SELECT
def query(sql, params=None):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params or ())
            result = cursor.fetchall()
        return result
    finally:
        connection.close()

# تنفيذ استعلام INSERT أو UPDATE أو DELETE
def execute(sql, params=None):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql, params or ())
        connection.commit()
    finally:
        connection.close()
