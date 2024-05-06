'''
# 가게나 메뉴 정보들을 반환해줄 라우트들을 모아둔 storeapp.py
from flask import Blueprint, jsonify, request
from dbconn import dbcon, dbclose

from flask_marshmallow import Marshmallow
from marshmallow import fields

import pymysql


ma = Marshmallow(app)
store_bp = Blueprint('store', __name__)


class StoreSchema(ma.Schema):
    storeid = fields.String(required=True)
    storename = fields.String(required=True)
    ownerid = fields.String(required=True)
    address = fields.String()
    storecontact = fields.String()
    tablenumber = fields.Integer()

class StoreMenuSchema(ma.Schema):
    productid = fields.String(required=True)
    productname = fields.String()
    storeid = fields.String()
    storename = fields.String()
    price = fields.Integer()
    available = fields.Boolean()


# 가게의 메뉴 불러오기
@store_bp.route('/<string:storeid>/menu', methods=['GET'])
def get_menu(storeid):
    conn = dbcon()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        query = "SELECT * FROM storemenu WHERE storeid = %s"
        cursor.execute(query, (storeid,))  # storeid를 파라미터로 사용하여 쿼리 실행
        rows = cursor.fetchall()
        cursor.close()
        dbclose(conn)
        return jsonify(rows)
    except pymysql.MySQLError as e:
        return jsonify({"error": "Query failed: " + str(e)}), 500


# 고객이 들렀던 가게 불러오기
@store_bp.route('/<string:userid>', methods=['GET'])
def get_stores(userid):
    conn = dbcon()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        query = "SELECT DISTINCT stores.* FROM stores JOIN orders ON stores.storeid = orders.storeid WHERE orders.userid = %s"
        cursor.execute(query, (userid,))  # userid를 파라미터로 사용하여 쿼리 실행
        rows = cursor.fetchall()
        cursor.close()
        dbclose(conn)
        return jsonify(rows)
    except pymysql.MySQLError as e:
        return jsonify({"error": "Query failed: " + str(e)}), 500
'''