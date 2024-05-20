import os
import pymysql
import qrcode
from flask_cors import CORS
from flask import Flask, Blueprint, jsonify, request, send_file
from werkzeug.utils import secure_filename
from marshmallow import Schema, fields, validate

from dbconn import dbcon, dbclose


app_store = Blueprint('store', __name__)
CORS(app_store)


# 이미지 파일 허용 확장자와 크기 제한
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB


# 마쉬멜로 스키마 정의
class StoremenuSchema(Schema):
    productid = fields.Int(dump_only=True)
    productname = fields.Str(validate=validate.Length(max=100))
    storeid = fields.Str(validate=validate.Length(max=100))
    storename = fields.Str(validate=validate.Length(max=100))
    price = fields.Str(validate=validate.Length(max=20))
    available = fields.Int()
    menuimage = fields.Str(dump_only=True)  # 읽기 전용 필드로 설정
    imageurl = fields.Str()  # 이미지 URL을 저장
    category = fields.Str(validate=validate.Length(max=50))
    description = fields.Str(validate=validate.Length(max=200))


# 가게메뉴를 저장하기 위한 스키마 객체
storemenu_schema = StoremenuSchema()
# 복수의 가게 메뉴를 반환하기 위한 스키마 객체
storemenus_schema = StoremenuSchema(many=True)


# 파일 확장자 확인 함수
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


ELASTIC_IP = "43.201.92.62"


# 가게 메뉴 등록하는 라우트
@app_store.route('/<string:ownerid>/menu', methods=['POST'])
def storemenu_post(ownerid):
    productname = request.values.get('productname')
    storename = request.values.get('storename')
    price = request.values.get('price')
    category = request.values.get('category')
    menuimage = request.files.get('menuimage')

    if not menuimage:
        return jsonify({'error': 'No image provided'}), 400

    if not allowed_file(menuimage.filename):
        return jsonify({'error': 'Unsupported file type'}), 400

    filename = secure_filename(menuimage.filename)
    # ownerid를 파일명에 추가하여 고유하게 만듦
    filename = f"{ownerid}_{filename}"
    save_path = os.path.join('/home/ubuntu/appnupan/tmp', filename)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    menuimage.save(save_path)

    image_url = f"http://{ELASTIC_IP}/images/{filename}"

    conn = dbcon()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        with conn.cursor() as cursor:
            sql = """
            INSERT INTO storemenu (storeid, productname, storename, price, imageurl, category)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (ownerid, productname, storename, price, image_url, category))
            conn.commit()
            return jsonify({'success': 'Menu item added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        dbclose(conn)


# 해당 가게의 메뉴들을 반환하는 라우트
@app_store.route('/<string:ownerid>/menu', methods=['GET'])
def storemenu_get(ownerid):
    conn = dbcon()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            sql = """
            SELECT productid, productname, storeid, storename, price, available, imageurl, category, description
            FROM storemenu
            WHERE storeid = %s
            """
            cursor.execute(sql, (ownerid,))
            results = cursor.fetchall()

            if not results:
                return jsonify({'error': 'No menu items found for the given storeid'}), 404

            return jsonify({'menu': results}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        dbclose(conn)


# qr_code를 담을 storetable 테이블을 직렬화
class StoretableSchema(Schema):
    tableid = fields.Int(dump_only=True)
    storeid = fields.Str(validate=validate.Length(max=100))
    tablenumber = fields.Int(validate=validate.Range(min=1))
    qr_path = fields.Str(validate=validate.Length(max=255))


# 가게좌석마다 QR코드 생성을 위한 스키마 객체 생성
storetable_schema = StoretableSchema()
storetables_schema = StoretableSchema(many=True)


def generate_qr_code(ownerid, tablenumber):
    qr_data = f"{ownerid}-{tablenumber}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')
    directory = '/home/ubuntu/appnupan/QR'
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    filename = f'{ownerid}_{tablenumber}.png'
    file_path = os.path.join(directory, filename)
    img.save(file_path)
    
    return file_path  # 파일 경로만 반환


# 좌석마다 qr코드 저장
@app_store.route('/<string:ownerid>/qr', methods=['POST'])
def qr_post(ownerid):
    data = request.json
    table_count = data.get('table_count')

    if not table_count or not isinstance(table_count, int):
        return jsonify({'error': 'Table count must be an integer'}), 400

    conn = dbcon()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT MAX(tablenumber) FROM storetable WHERE storeid = %s FOR UPDATE", (ownerid,))
            last_table_number = cursor.fetchone()[0] or 0

            sql = """
            INSERT INTO storetable (storeid, tablenumber, qr_path)
            VALUES (%s, %s, %s)
            """
            successful_inserts = 0
            qr_urls = []
            for i in range(1, table_count + 1):
                table_number = last_table_number + i
                qr_code_path = generate_qr_code(ownerid, table_number)
                qr_url = f'http://{ELASTIC_IP}/qr/{os.path.basename(qr_code_path)}'
                qr_urls.append(qr_url)

                cursor.execute(sql, (ownerid, table_number, qr_url))  # URL을 바로 저장
                successful_inserts += 1

            conn.commit()
            return jsonify({'success': 'QR codes saved successfully', 'count': successful_inserts, 'qr_urls': qr_urls}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        dbclose(conn)
        

# 해당 가게의 QR코드들을 조회하는 라우트
@app_store.route('/<string:ownerid>/qr', methods=['GET'])
def qr_get(ownerid):
    conn = dbcon()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT tablenumber, qr_path FROM storetable WHERE storeid = %s", (ownerid,))
            qr_codes = cursor.fetchall()

            if not qr_codes:
                return jsonify({'error': 'No QR codes found for the given ownerid'}), 404

            return jsonify({'qr_codes': qr_codes}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        dbclose(conn)

