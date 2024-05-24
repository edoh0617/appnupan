# 주문내역의 총가격을 계산해주는 모듈파일 model_amounts.py
import pymysql
from dbconn import dbcon, dbclose

def calculate_total_price(orderid):
    conn = dbcon()
    if not conn:
        raise Exception("Database connection failed")

    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            query = """
                SELECT quantity, menu_price
                FROM order_details
                WHERE orderid = %s
            """
            cursor.execute(query, (orderid,))
            order_items = cursor.fetchall()

            total_price = 0
            for item in order_items:
                quantity = item['quantity']
                menu_price = int(item['menu_price'])  # 문자열로 저장된 가격을 정수형으로 변환
                total_price += quantity * menu_price

            return total_price

    except pymysql.MySQLError as e:
        print(f"Query failed: {e}")
        raise

    finally:
        dbclose(conn)