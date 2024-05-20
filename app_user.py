# 앱 사용자의 회원가입, 로그인, ID 중복체크 라우트들을 모아둔 모듈 파일 app_user.py
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


# 회원가입 라우트 실제로는 baseURL/user/regist
@app_user.route('/register', methods=['POST'])
def register_user():
    user_schema = UserSchema()
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

    finally:
        dbclose(conn)