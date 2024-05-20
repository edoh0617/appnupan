# 가맹점 신청과 관련한 라우트들을 모아둔 app_franchise.py
import uuid
import pymysql
from flask_cors import CORS
from flask import Blueprint, jsonify, request
from marshmallow import Schema, fields, validate, ValidationError

from dbconn import dbcon, dbclose


app_franchise = Blueprint('franchise', __name__)
CORS(app_franchise)


# 마쉬멜로 스키마 정의
class PendingstoresSchema(Schema):
    tempstoreid = fields.Int(dump_only=True)  # tempstoreid는 읽기 전용
    storename = fields.Str(required=True, validate=validate.Length(max=200))
    address = fields.Str(validate=validate.Length(max=200))
    contact = fields.Str(validate=validate.Length(max=50))
    memo = fields.Str()
    status = fields.Int()
    ownerid = fields.Str(required=True, validate=validate.Length(max=45))
    businessnumber = fields.Str(validate=validate.Length(max=45))
    businessdate = fields.Str(validate=validate.Length(max=45))
    bossname = fields.Str(validate=validate.Length(max=45))


# 단일 가맹점 신청을 위한 객체
franchise_schema = PendingstoresSchema()
# 가맹점 조회시 복수의 가맹점 신청 목록을 가져오기 위한 객체
franchises_schema = PendingstoresSchema(many=True)


# 점주가 처음 가맹점 신청을 하는 라우트
@app_franchise.route('/regist', methods=['POST'])
def store_regist():
    data = request.get_json()
    
    try:
        validated_data = franchise_schema.load(data)
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    # 필수 입력 데이터
    storename = validated_data['storename']
    ownerid = validated_data['ownerid']
    
    # 선택사항
    address = validated_data.get('address', None)
    contact = validated_data.get('contact', None)
    businessnumber = validated_data.get('businessnumber', None)
    businessdate = validated_data.get('businessdate', None)
    bossname = validated_data.get('bossname', None)

    conn = dbcon()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        with conn.cursor() as cursor:
            # 가맹점 신청 정보를 pendingstores 테이블에 저장
            sql = """
            INSERT INTO pendingstores (storename, address, contact, ownerid, memo, status, businessnumber, businessdate, bossname)
            VALUES (%s, %s, %s, %s, NULL, NULL, %s, %s, %s)
            """
            cursor.execute(sql, (storename, address, contact, ownerid, businessnumber, businessdate, bossname))
            conn.commit()

        return jsonify({"success": "Store added successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        dbclose(conn)


# 승인 여부를 기다리는 모든 가게 정보를 호출하는 라우트
@app_franchise.route('', methods=['GET'])
def get_pendingstores():
    # DB 연결
    conn = dbcon()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        with conn.cursor() as cursor:
            # status가 NULL인 pendingstores에서 데이터 조회
            sql = """
            SELECT tempstoreid, ownerid, storename, address, contact, businessnumber
            FROM pendingstores
            WHERE status IS NULL
            """
            cursor.execute(sql)
            results = cursor.fetchall()
            
            # 결과가 없는 경우
            if not results:
                return jsonify({'error': 'No pending stores found'}), 404
            
            # 결과를 JSON 형식으로 변환
            pending_stores = []
            for result in results:
                tempstoreid, ownerid, storename, address, contact, businessnumber = result
                pending_stores.append({
                    'tempstoreid': tempstoreid,
                    'ownerid': ownerid,
                    'storename': storename,
                    'address': address,
                    'contact': contact,
                    'businessnumber': businessnumber
                })

            return jsonify({'pendingStores': franchises_schema.dump(pending_stores)}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        # DB 연결 종료
        dbclose(conn)


# 가맹점 신청 승인 라우트
@app_franchise.route('/confirm', methods=['POST'])
def store_confirm():
    # JSON 데이터로부터 tempstoreid 받아오기
    data = request.get_json()
    try:
        tempstore_id = data['tempstoreid']
    except KeyError:
        return jsonify({'error': 'tempstoreid is required'}), 400
    
    # DB 연결
    conn = dbcon()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        with conn.cursor() as cursor:
            # pendingstores에서 승인되지 않은 데이터 조회
            sql = """
            SELECT ownerid, storename, address, contact
            FROM pendingstores
            WHERE tempstoreid = %s AND status IS NULL
            """
            cursor.execute(sql, (tempstore_id,))
            result = cursor.fetchone()
            if result:
                ownerid, storename, address, contact = result

                # storeid로 사용할 랜덤 UID 생성
                storeid = str(uuid.uuid4())

                # stores 테이블에 데이터 저장
                insert_sql = """
                INSERT INTO stores (storeid, ownerid, storename, address, storecontact)
                VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(insert_sql, (storeid, ownerid, storename, address, contact))
                
                # pendingstores 테이블의 status 업데이트
                update_sql = """
                UPDATE pendingstores
                SET status = 1
                WHERE tempstoreid = %s
                """
                cursor.execute(update_sql, (tempstore_id,))
                
                conn.commit()

                return jsonify({'success': 'Store confirmed', 'storeid': storeid}), 200
            else:
                return jsonify({'error': 'No data found with provided tempstoreid or already processed'}), 404
    
    except pymysql.MySQLError as e:
        print(f"SQL Error: {e}")
        return jsonify({'error': str(e)}), 500
    
    finally:
        # DB 연결 종료
        dbclose(conn)


# 가맹점 신청거부하는 라우트
@app_franchise.route('/deny', methods=['PUT'])
def store_deny():
    # JSON 데이터로부터 tempstoreid 받아오기
    data = request.get_json()
    tempstore_id = data['tempstoreid']
    
    # DB 연결
    conn = dbcon()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        with conn.cursor() as cursor:
            # pendingstores 테이블의 status를 0으로 업데이트
            update_sql = """
            UPDATE pendingstores
            SET status = 0
            WHERE tempstoreid = %s AND status IS NULL
            """
            affected_rows = cursor.execute(update_sql, (tempstore_id,))
            conn.commit()

            if affected_rows == 0:
                # 해당 ID가 이미 처리되었거나 존재하지 않는 경우
                return jsonify({'error': 'No pending store found with provided tempstoreid or already processed'}), 404
            return jsonify({'success': 'Store application has been denied'}), 200
    except pymysql.MySQLError as e:
        print(f"SQL Error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        # DB 연결 종료
        dbclose(conn)

