# 앱 사용자의 회원가입, 로그인, ID 중복체크 라우트들을 모아둔 모듈 파일 app_user.py
import pymysql
from flask_cors import CORS
from flask import Blueprint, jsonify, request
from flask_bcrypt import Bcrypt
from marshmallow import Schema, fields, validate, ValidationError

from dbconn import dbcon, dbclose
from model_regist import Registration


app_user = Blueprint('app_user', __name__)
CORS(app_user)
# bcrypt 인스턴스 생성, 하지만 나중에 앱과 바인딩
bcrypt = Bcrypt()


# Bcrypt 인스턴스 초기화 함수
def init_bcrypt(app):
    global bcrypt
    bcrypt = Bcrypt(app)


# JSON 데이터 직렬화
class UserSchema(Schema):
    userid = fields.String(required=True, validate=[validate.Length(min=1, max=45)])
    username = fields.String(required=True, validate=[validate.Length(min=1, max=45)])
    password = fields.String(required=True, validate=[validate.Length(min=1)])
    usercontact = fields.String(validate=[validate.Length(max=45)])

# 어플 사용자의 주문이력 확인 스키마
class UserHistorySchema(Schema):
    userid = fields.String(required=True, validate=[validate.Length(min=1, max=45)])

# 직원 호출 스키마
class CallStaffSchema(Schema):
    orderid = fields.String(required=True)


# 회원가입을 위한 마쉬멜로 스키마 객체 생성
user_schema = UserSchema()
# 어플 사용자의 주문이력 확인 스키마 객체 생성
user_history_schema = UserHistorySchema()
# 직원 호출 스키마 객체
call_staff_schema = CallStaffSchema()



# 회원가입 라우트 실제로는 baseURL/user/regist
@app_user.route('/register', methods=['POST'])
def register_user():
    try:
        user_data = user_schema.load(request.json)
        userid = user_data['userid']

        # 데이터베이스에서 중복된 ID 확인
        conn = dbcon()
        cur = conn.cursor()
        cur.execute("SELECT userid FROM users WHERE userid = %s", (userid,))
        if cur.fetchone():
            return jsonify({'message': 'This userid is already taken'}), 409

        registration = Registration(bcrypt)  # 여기서 Registration 인스턴스 생성 근데 bcrypt를 곁들인
        response = registration.register_user(user_data['userid'], user_data['password'], user_data['username'], user_data['usercontact'])
        return jsonify({'message': response}), 201
        
    except ValidationError as err:
        return jsonify(err.messages), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        
    finally:
        dbclose(conn)


# ID 중복검사 라우트 실제로는 baseURL/user/check?userid=실제로 클라이언트가 요청하는 사용자id
# userid는 클라이언트에서 서버로 보내는 실제 사용자 id
@app_user.route('/check', methods=['GET'])
def check_userid():
    userid = request.args.get('userid')

    if not userid:
        return jsonify({'error': 'userid parameter is required'}), 400
    
    try:
        conn = dbcon()
        cur = conn.cursor()
        cur.execute("SELECT userid FROM users WHERE userid = %s", (userid,))

        if cur.fetchone():
            return jsonify({'isAvailable': False, 'message': 'This userid is already taken'}), 200
        else:
            return jsonify({'isAvailable': True, 'message': 'This userid is available'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        
    finally:
        dbclose(conn)


# 로그인 라우트 실제로는 baseURL/user/login
@app_user.route('/login', methods=['POST'])
def login_user():
    userid = request.json.get('userid')
    password = request.json.get('password')
    conn = dbcon()
    cur = conn.cursor()

    try:
        # userdigest를 검색하는 대신 username도 함께 검색
        cur.execute("SELECT userdigest, username FROM users WHERE userid = %s", (userid,))
        row = cur.fetchone()

        if row:
            # 데이터베이스 조회 결과에서 userdigest와 username 추출
            userdigest, username = row

            # 비밀번호 검증
            if bcrypt.check_password_hash(userdigest, password):
                return jsonify({'message': 'Login success!', 'username': username}), 200

        return jsonify({'error': 'Invalid credentials'}), 401
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        dbclose(conn)


# 직원 호출 라우트
@app_user.route('/call', methods=['POST'])
def call_staff():
    json_data = request.get_json()
    
    try:
        data = call_staff_schema.load(json_data)
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
                UPDATE orders SET staffcall = 1 WHERE orderid = %s
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


# 어플 사용자의 주문내역 조회 라우트
@app_user.route('/history', methods=['POST'])
def user_order_history():
    json_data = request.get_json()
    try:
        data = user_history_schema.load(json_data)
    except ValidationError as err:
        return jsonify(err.messages), 400

    userid = data.get('userid')

    conn = dbcon()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            query_get_orders = "SELECT orderid, ordertime FROM orders WHERE userid = %s"
            cursor.execute(query_get_orders, (userid,))
            orders = cursor.fetchall()

            if not orders:
                return jsonify({"message": "No orders found for this user"}), 404

            order_history = []

            for order in orders:
                orderid = order['orderid']
                ordertime = order['ordertime']
                
                # order_details 테이블에서 orderid로 메뉴 정보 조회
                query_get_order_details = """
                    SELECT menu_name, quantity, total_price
                    FROM order_details
                    WHERE orderid = %s
                """
                cursor.execute(query_get_order_details, (orderid,))
                order_details = cursor.fetchall()

                # orders 테이블에서 ownerid 조회
                query_get_owner = "SELECT ownerid FROM orders WHERE orderid = %s"
                cursor.execute(query_get_owner, (orderid,))
                owner = cursor.fetchone()

                if owner:
                    ownerid = owner['ownerid']
                    
                    # stores 테이블에서 storename 조회
                    query_get_store_name = "SELECT storename FROM stores WHERE ownerid = %s"
                    cursor.execute(query_get_store_name, (ownerid,))
                    store = cursor.fetchone()
                    storename = store['storename'] if store else "Unknown Store"
                else:
                    storename = "Unknown Store"

                order_info = {
                    "orderid": orderid,
                    "total_price": order_details[0]['total_price'] if order_details else 0,
                    "ordertime": ordertime,
                    "storename": storename,
                    "items": [{"menu_name": detail["menu_name"], "quantity": detail["quantity"]} for detail in order_details]
                }

                order_history.append(order_info)

            return jsonify(order_history), 200

    except pymysql.MySQLError as e:
        return jsonify({"error": "Query failed", "details": str(e)}), 500

    finally:
        dbclose(conn)


# 비밀번호 변경 라우트
@app_user.route('/<string:userid>/changepw', methods=['PUT'])
def change_user_pw(userid):
    try:
        # 요청에서 비밀번호를 추출
        new_password = request.json.get('password')
        # 비밀번호 해싱
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')

        conn = dbcon()
        cur = conn.cursor()

        # 비밀번호 업데이트
        sql = "UPDATE users SET userdigest = %s WHERE userid = %s"
        cur.execute(sql, (hashed_password, userid))
        conn.commit()
        
        return jsonify({'message': 'Password updated successfully'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        dbclose(conn)
