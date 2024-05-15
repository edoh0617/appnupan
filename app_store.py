# 가게의 메뉴와 QR코드를 저장하고 조회하는 라우트들을 모아둔 app_store.py
import os
import base64
import pymysql
from flask_cors import CORS
from flask import Blueprint, jsonify, request
from marshmallow import Schema, fields, validate
from werkzeug.utils import secure_filename

from dbconn import dbcon, dbclose


app_store = Blueprint('store', __name__)
CORS(app_store)


# 마쉬멜로 스키마 정의
class StoremenuSchema(Schema):
    productid = fields.Int(dump_only=True)
    productname = fields.Str(validate=validate.Length(max=100))
    storeid = fields.Str(validate=validate.Length(max=100))
    storename = fields.Str(validate=validate.Length(max=100))
    price = fields.Str(validate=validate.Length(max=20))
    available = fields.Int()
    menuimage = fields.Method("load_image")
    category = fields.Str(validate=validate.Length(max=50))
    description = fields.Str(validate=validate.Length(max=200))

    def load_image(self, obj):
        # 이미지 데이터를 base64로 인코딩
        if 'menuimage' in obj and obj['menuimage']:
            return base64.b64encode(obj['menuimage']).decode('utf-8')
        return None


# 가게 메뉴 등록을 위한 스키마 객체 생성
storemenu_schema = StoremenuSchema()
# 복수의 가게 메뉴들을 담기 위한 스키마 객체 생성
storemenus_schema = StoremenuSchema(many=True)


# 가게 메뉴 등록하는 라우트
# 멀티파트/폼으로 보내기
@app_store.route('/<string:ownerid>/menu', methods=['POST'])
def storemenu_post(ownerid):
    productname = request.values.get('productname')
    storename = request.values.get('storename')
    price = request.values.get('price')
    category = request.values.get('category')
    menuimage = request.files.get('menuimage')

    if not menuimage:
        return jsonify({'error': 'No image provided'}), 400

    filename = secure_filename(menuimage.filename)
    temp_path = os.path.join('/home/ubuntu/appnupan/tmp', filename)
    os.makedirs(os.path.dirname(temp_path), exist_ok=True)
    menuimage.save(temp_path)

    with open(temp_path, 'rb') as file:
        binary_data = file.read()

    conn = dbcon()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        with conn.cursor() as cursor:
            sql = """
            INSERT INTO storemenu (storeid, productname, storename, price, menuimage, category)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (ownerid, productname, storename, price, binary_data, category))
            conn.commit()
            return jsonify({'success': 'Menu item added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        os.remove(temp_path)
        dbclose(conn)


# 해당 가게의 가게 메뉴들을 반환하는 라우트
@app_store.route('/<string:storeid>/menu', methods=['GET'])
def storemenu_get(storeid):
    conn = dbcon()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            sql = """
            SELECT productid, productname, storeid, storename, price, available, menuimage, category, description
            FROM storemenu
            WHERE storeid = %s
            """
            cursor.execute(sql, (storeid,))
            results = cursor.fetchall()
            
            if not results:
                return jsonify({'error': 'No menu items found for the given storeid'}), 404
            
            return jsonify({'menu': storemenus_schema.dump(results)}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        dbclose(conn)

