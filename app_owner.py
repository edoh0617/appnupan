# 점주가 접근하는 라우트들을 모아둔 app_owner.py
import pymysql

from flask_cors import CORS
from flask import Blueprint, jsonify, request
from flask_bcrypt import Bcrypt
from marshmallow import Schema, fields, validate, ValidationError, post_load

from dbconn import dbcon, dbclose


app_owner = Blueprint('owner', __name__)
CORS(app_owner, resources={r"/*": {"origins": "*", "allow_headers": ["Content-Type"]}})
bcrypt = Bcrypt()


# Bcrypt 인스턴스 초기화 함수
def init_bcrypt(app):
    global bcrypt
    bcrypt = Bcrypt(app)


# 마쉬멜로 스키마 정의
class OwnerSchema(Schema):
    ownerid = fields.Str(required=True)
    ownername = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)
    ownercontact = fields.String(validate=[validate.Length(max=45)])

    @post_load
    def make_owner(self, data, **kwargs):
        data['ownerdigest'] = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        return data


# 직원 호출 스키마
class DoneStaffSchema(Schema):
    orderid = fields.String(required=True)


owner_schema = OwnerSchema()
# 직원 호출 스키마 객체
done_staff_schema = DoneStaffSchema()


# 점주의 회원가입 라우트
@app_owner.route('/register', methods=['POST'])
def register_owner():
    try:
        owner_data = owner_schema.load(request.get_json())
        conn = dbcon()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO owners(ownerid, ownername, ownerdigest, ownercontact) VALUES(%s, %s, %s, %s)
            """, (owner_data['ownerid'], owner_data['ownername'], owner_data['ownerdigest'], owner_data['ownercontact']))
        conn.commit()
        dbclose(conn)
        return jsonify({"message": "Owner registered successfully"}), 201
    except ValidationError as err:
        return jsonify(err.messages), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 점주의 로그인 라우트
@app_owner.route('/login', methods=['POST'])
def login_owner():
    try:
        login_data = request.get_json()
        conn = dbcon()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        # managers 테이블에서 관리자 계정 확인
        cur.execute("""
            SELECT managerid
            FROM managers
            WHERE managerid = %s AND managerdigest = AES_ENCRYPT(%s, %s)
        """, (login_data['ownerid'], login_data['password'], '1234'))
        
        manager = cur.fetchone()
        if manager:
            return jsonify({
                'message': 'Login successful!',
                'role': 'manager'
            }), 200

        # ownerid로 owner 정보 조회
        cur.execute("""
            SELECT ownerdigest
            FROM owners
            WHERE ownerid = %s
        """, (login_data['ownerid'],))
        
        owner = cur.fetchone()
        
        if owner and bcrypt.check_password_hash(owner['ownerdigest'], login_data['password']):
            storeid = None
            storename = None
            
            # ownerid로 stores 테이블 조회
            cur.execute("""
                SELECT storeid, storename
                FROM stores
                WHERE ownerid = %s
            """, (login_data['ownerid'],))
            
            store = cur.fetchone()
            if store:
                storeid = store.get('storeid')
                storename = store.get('storename')
            
            return jsonify({
                'message': 'Login successful!',
                'storeid': storeid,
                'storename': storename,
                'role': 'owner'
            }), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        dbclose(conn)


# ID 중복검사 라우트 실제로는 baseURL/user/check?ownerid=실제로 클라이언트가 요청하는 점주의id
# ownerid는 클라이언트에서 서버로 보내는 실제 사용자 id
@app_owner.route('/check', methods=['GET'])
def check_ownerid():
    ownerID = request.args.get('ownerid')

    if not ownerID:
        return jsonify({'error': 'ownerid parameter is required'}), 400
    
    try:
        conn = dbcon()
        cur = conn.cursor()
        cur.execute("SELECT ownerid FROM owners WHERE ownerid = %s", (ownerID,))

        if cur.fetchone():
            return jsonify({'isAvailable': False, 'message': 'This ownerid is already taken'}), 200
        
        else:
            return jsonify({'isAvailable': True, 'message': 'This ownerid is available'}), 200
        
    finally:
        dbclose(conn)


# 직원호출 용무가 끝났을때
@app_owner.route('/done', methods=['POST'])
def done_staff():
    json_data = request.get_json()
    
    try:
        data = done_staff_schema.load(json_data)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    orderid = data['orderid']
    
    conn = dbcon()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        with conn.cursor() as cursor:
            # orders 테이블에서 staffcall 값을 1로 업데이트
            query_update_staffcall = """
                UPDATE orders SET staffcall = 0 WHERE orderid = %s
            """
            cursor.execute(query_update_staffcall, (orderid,))
            
            # 변경사항 커밋
            conn.commit()
            
            return jsonify({"message": "Staff call updated successfully"}), 200

    except pymysql.MySQLError as e:
        # 오류 발생 시 롤백
        conn.rollback()
        return jsonify({"error": "Query failed", "details": str(e)}), 500

    finally:
        dbclose(conn)