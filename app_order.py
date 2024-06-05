# 주문과 결제에 관련된 라우트들을 모아둔 모듈 파일 app_order.py
import os
import pymysql
import uuid
import logging

from flask_cors import CORS
from flask import Blueprint, jsonify, request
from marshmallow import Schema, fields, post_load, ValidationError
from dbconn import dbcon, dbclose


app_order = Blueprint('order', __name__)
CORS(app_order)


# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# QR스캔 스키마
class QRScanSchema(Schema):
    ownerid = fields.String(required=True)
    tablenumber = fields.Integer(required=True)
    userid = fields.String(required=False)  # userid 없어도 상관없음

    @post_load
    def make_qrscan(self, data, **kwargs):
        return QRScan(**data)

class MenuItemSchema(Schema):
    productid = fields.Integer()
    productname = fields.String()
    price = fields.String()  # price를 문자열로 수정
    imageurl = fields.String()
    category = fields.String()
    description = fields.String()

class MenuResponseSchema(Schema):
    storeid = fields.String()
    tablenumber = fields.Integer()
    menu_items = fields.List(fields.Nested(MenuItemSchema))
    orderid = fields.String()

class PaymentSchema(Schema):
    merchant_uid = fields.String(required=False)  # 클라이언트가 보내주는 주문번호
    amount = fields.Decimal(required=False)  # 총 결제 금액
    buyer_email = fields.String(required=False)
    buyer_name = fields.String(required=False)  # 사용자 아이디
    buyer_tel = fields.String(required=False)  # 사용자 전화번호
    buyer_addr = fields.String(required=False)  # 사용자 주소
    buyer_postcode = fields.String(required=False)  # 몰?루
    pay_method = fields.String(required=False)  # 결제방법
    pg = fields.String(required=False)  # 몰?루
    order_details = fields.Dict(required=True)  # 딕셔너리로 변경
    userid = fields.String(required=True)  # 사용자 아이디
    orderid = fields.String(required=True)  # 주문 아이디

# QR 스캔 클래스 생성자
class QRScan:
    def __init__(self, ownerid, tablenumber, userid=None): # userid를 선택적으로 처리
        self.ownerid = ownerid
        self.tablenumber = tablenumber
        self.userid = userid


qr_scan_schema = QRScanSchema()
menu_response_schema = MenuResponseSchema()
payment_schema = PaymentSchema()


# QR스캔 라우트
# 가게메뉴 반환 & orders테이블에 레코드 생성
@app_order.route('/scan', methods=['POST'])
def scan_qr():
    json_data = request.get_json()
    logger.info(f"Received JSON data: {json_data}")
    
    try:
        data = qr_scan_schema.load(json_data)
    except ValidationError as err:
        logger.error(f"Validation error: {err.messages}")
        return jsonify(err.messages), 400
    
    ownerid = data.ownerid
    tablenumber = data.tablenumber
    userid = data.userid
    logger.info(f"Parsed data - ownerid: {ownerid}, tablenumber: {tablenumber}, userid: {userid}")

    conn = dbcon()
    if not conn:
        logger.error("Database connection failed")
        return jsonify({"error": "Database connection failed"}), 500

    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            query_menu = """
                SELECT productid, productname, price, imageurl, category, description FROM storemenu WHERE storeid = %s
            """
            cursor.execute(query_menu, (ownerid,))
            menu_items = cursor.fetchall()
            logger.info(f"Fetched menu items: {menu_items}")

            if not menu_items:
                logger.warning(f"No menu items found for storeid: {ownerid}")
                return jsonify({"error": "No menu items found for the given storeid"}), 404

            # 문자열 가격에서 콤마를 제거하고 정수형으로 변환
            for item in menu_items:
                item['price'] = int(item['price'].replace(',', ''))

            # orderid 생성
            orderid = str(uuid.uuid4())
            logger.info(f"Generated orderid: {orderid}")

            # orders 테이블에 레코드 생성
            query_order = """
                INSERT INTO orders (orderid, ownerid, tablenumber, userid, order_status)
                VALUES (%s, %s, %s, %s, 0)
            """
            cursor.execute(query_order, (orderid, ownerid, tablenumber, userid))
            conn.commit()
            logger.info("Inserted new order into orders table")

            menu_response = {
                "storeid": ownerid,
                "tablenumber": tablenumber,
                "menu_items": menu_items,
                "orderid": orderid
            }

            result = menu_response_schema.dump(menu_response)

            return jsonify(result)

    except pymysql.MySQLError as e:
        logger.error(f"Query failed: {e}")
        return jsonify({"error": "Query failed"}), 500

    finally:
        dbclose(conn)


@app_order.route('/payments', methods=['POST'])
def order_payment():
    json_data = request.get_json()

    logger.info(f"Received JSON data: {json_data}")

    try:
        data = payment_schema.load(json_data)
        logger.info(f"Parsed data: {data}")
    except ValidationError as err:
        logger.error(f"Validation error: {err.messages}")
        return jsonify(err.messages), 400

    order_details = data['order_details']
    userid = data.get('userid')
    orderid = data.get('orderid')
    amount = data['order_details'].get('amount')  # order_details에서 amount 가져오기

    if not userid or not orderid:
        logger.error("User ID and Order ID are required")
        return jsonify({"error": "User ID and Order ID are required"}), 400

    menu_items = order_details['menu_items']

    conn = dbcon()
    if not conn:
        logger.error("Database connection failed")
        return jsonify({"error": "Database connection failed"}), 500

    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # 트랜잭션 시작
            conn.begin()
            logger.info("Transaction started")

            # orders 테이블에서 order_status가 0인 레코드를 orderid로 조회하여 ownerid 확보
            query_get_order = """
                SELECT ownerid FROM orders WHERE order_status = 0 AND orderid = %s LIMIT 1
            """
            cursor.execute(query_get_order, (orderid,))
            result = cursor.fetchone()
            if result:
                ownerid = result['ownerid']
                logger.info(f"Owner ID found: {ownerid}")
            else:
                logger.error("Order not found or already processed")
                return jsonify({"error": "Order not found or already processed"}), 404

            # 주문 상세 정보 저장
            query_order_details = """
                INSERT INTO order_details (orderid, menu_name, quantity, menu_price, total_price)
                VALUES (%s, %s, %s, %s, %s)
            """
            for item in menu_items:
                cursor.execute(query_order_details, (
                    orderid,
                    item['productname'],
                    int(item.get('quantity', 1)),
                    int(item['price']),
                    amount
                ))

            # 주문 상태 업데이트 (결제 완료로 변경)
            query_update_order = """
                UPDATE orders SET order_status = %s WHERE orderid = %s
            """
            cursor.execute(query_update_order, (1, orderid))
            logger.info(f"Order status updated for order ID: {orderid}")

            # 트랜잭션 커밋
            conn.commit()
            logger.info("Transaction committed")

            return jsonify({'message': 'Payment information saved successfully', 'orderid': orderid}), 200

    except pymysql.MySQLError as e:
        # 트랜잭션 롤백
        conn.rollback()
        logger.error(f"Query failed: {e}")
        return jsonify({"error": "Query failed", "details": str(e)}), 500

    finally:
        dbclose(conn)
        logger.info("Database connection closed")



class StoreServeListSchema(Schema):
    ownerid = fields.String(required=True)

store_serve_list_schema = StoreServeListSchema()


# 가맹점에서 사용할 주문현황 조회 라우트
@app_order.route('/serve_list', methods=['POST'])
def store_serve_list():
    json_data = request.get_json()

    try:
        data = store_serve_list_schema.load(json_data)
    except ValidationError as err:
        return jsonify(err.messages), 400

    ownerid = data['ownerid']

    conn = dbcon()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # orders 테이블에서 order_status가 1이고 ownerid가 일치하는 모든 orderid 조회
            query_get_orders = """
                SELECT orderid, tablenumber, staffcall, ordertime FROM orders WHERE order_status = 1 AND ownerid = %s
            """
            cursor.execute(query_get_orders, (ownerid,))
            orders = cursor.fetchall()

            if not orders:
                return jsonify({"error": "No orders found"}), 404

            order_details_list = []
            for order in orders:
                orderid = order['orderid']
                tablenumber = order['tablenumber']
                staffcall = order['staffcall']
                ordertime = order['ordertime']

                # order_details 테이블에서 해당 orderid의 모든 레코드 조회
                query_get_order_details = """
                    SELECT menu_name, quantity, total_price, menu_price FROM order_details WHERE orderid = %s
                """
                cursor.execute(query_get_order_details, (orderid,))
                order_details = cursor.fetchall()

                if order_details:
                    order_details_list.append({
                        "orderid": orderid,
                        "tablenumber": tablenumber,
                        "staffcall": staffcall,
                        "ordertime": ordertime,
                        "order_details": order_details
                    })

            return jsonify(order_details_list), 200

    except pymysql.MySQLError as e:
        return jsonify({"error": "Query failed", "details": str(e)}), 500

    finally:
        dbclose(conn)


# 서빙완료 라우트
@app_order.route('/serve_done', methods=['POST'])
def store_serve_done():
    json_data = request.get_json()

    logger.info(f"Received JSON data: {json_data}")

    orderid = json_data.get('orderid')
    
    if not orderid:
        logger.error("Order ID is required")
        return jsonify({"error": "Order ID is required"}), 400

    conn = dbcon()
    if not conn:
        logger.error("Database connection failed")
        return jsonify({"error": "Database connection failed"}), 500

    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            # orders 테이블에서 order_status가 3으로 업데이트
            query_update_order = """
                UPDATE orders SET order_status = %s WHERE orderid = %s
            """
            cursor.execute(query_update_order, (3, orderid))
            logger.info(f"Order status updated to 3 for order ID: {orderid}")

            # 트랜잭션 커밋
            conn.commit()
            logger.info("Transaction committed")

            return jsonify({'message': 'Order status updated successfully', 'orderid': orderid}), 200

    except pymysql.MySQLError as e:
        # 트랜잭션 롤백
        conn.rollback()
        logger.error(f"Query failed: {e}")
        return jsonify({"error": "Query failed", "details": str(e)}), 500

    finally:
        dbclose(conn)
        logger.info("Database connection closed")

