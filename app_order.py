# 주문과 결제에 관련된 라우트들을 모아둔 모듈 파일 app_order.py
import os
import pymysql

from flask_cors import CORS
from flask import Blueprint, jsonify, request
from marshmallow import Schema, fields, post_load, ValidationError

from dbconn import dbcon, dbclose


app_order = Blueprint('order', __name__)
CORS(app_order)


class QRScanSchema(Schema):
    ownerid = fields.String(required=True)
    tablenumber = fields.Integer(required=True)

    @post_load
    def make_qrscan(self, data, **kwargs):
        return QRScan(**data)

class MenuItemSchema(Schema):
    productid = fields.Integer()
    productname = fields.String()
    price = fields.Integer()  # 가격을 정수형으로 반환
    imageurl = fields.String()
    category = fields.String()
    description = fields.String()

class MenuResponseSchema(Schema):
    storeid = fields.String()
    tablenumber = fields.Integer()
    menu_items = fields.List(fields.Nested(MenuItemSchema))

class QRScan:
    def __init__(self, ownerid, tablenumber):
        self.ownerid = ownerid
        self.tablenumber = tablenumber


qr_scan_schema = QRScanSchema()
menu_response_schema = MenuResponseSchema()



# QR스캔 라우트
# 가게메뉴 반환 & orders테이블에 레코드 생성
@app_order.route('/scan', methods=['POST'])
def scan_qr():
    json_data = request.get_json()
    
    try:
        data = qr_scan_schema.load(json_data)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    ownerid = data.ownerid
    tablenumber = data.tablenumber

    conn = dbcon()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            query_menu = """
                SELECT productid, productname, price, imageurl, category, description FROM storemenu WHERE storeid = %s
            """
            cursor.execute(query_menu, (ownerid,))
            menu_items = cursor.fetchall()

            if not menu_items:
                return jsonify({"error": "No menu items found for the given storeid"}), 404

            # 문자열 가격을 정수형으로 변환
            for item in menu_items:
                item['price'] = int(item['price'])

            menu_response = {
                "storeid": ownerid,
                "tablenumber": tablenumber,
                "menu_items": menu_items
            }

            result = menu_response_schema.dump(menu_response)

            return jsonify(result)

    except pymysql.MySQLError as e:
        print(f"Query failed: {e}")
        return jsonify({"error": "Query failed"}), 500

    finally:
        dbclose(conn)
