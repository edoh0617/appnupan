# 라우트 정보를 담은 app.py
from flask  import Flask, jsonify, request
from flask_cors import CORS
from flask_bcrypt import Bcrypt

import pymysql
from dbconn import dbcon, dbclose
from regist_model import Registration

app = Flask(__name__)
CORS(app)
# Bcrypt 인스턴스 초기화
bcrypt = Bcrypt(app)

# user 회원가입 라우트
@app.route('/user/register', methods=['POST', 'GET'])
def user_register():
    # POST 요청시 회원가입 로직 처리
    if request.method == 'POST':
        userID = request.json.get('userid')  
        password = request.json.get('password')
        userName = request.json.get('username')
        userContact = request.json.get('usercontact')

        # 인자값이 누락 되었을 경우
        if not all([userID, userName, password, userContact]): 
            return jsonify({'error': 'Missing fields'}), 400
        
        response = Registration.register(bcrypt, userID, password, userName, userContact, 'users')
        return jsonify({'message': response}), 201
        
    elif request.method == 'GET':
        # GET 요청 시, userid 중복 체크 로직
        userID = request.args.get('userid')
        
        # 인자 값이 누락되었다면
        if not userID:
            return jsonify({'error': 'userid is required for duplication check'}), 400

        conn = dbcon()
        cur = conn.cursor()
        # 데이터베이스에서 userid 확인
        cur.execute("SELECT userid FROM users WHERE userid = %s", (userID,))
        user_exists = cur.fetchone()
        dbclose(conn)

        if user_exists:
            return jsonify({'message': 'This userid is already taken'}), 409
        else:
            return jsonify({'message': 'This userid is available'}), 200
            

# user 로그인 라우트
@app.route('/user/login', methods=['POST'])
def user_login():
    # 클라이언트로부터 userid와 password 받기
    userid = request.json.get('userid')
    password = request.json.get('password')

    # 입력값 검증
    if not userid or not password:
        return jsonify({'error': 'Missing fields'}), 400

    conn = dbcon()
    cur = conn.cursor()
    
    try:
        # 해당 userid에 맞는 userigest 불러오기
        cur.execute("SELECT userdigest FROM users WHERE userid = %s", (userid,))
        user = cur.fetchone()
        # 이미 있는 사용자라면
        if user:
            userdigest = user[0]
            
            # 비밀번호 검증
            if bcrypt.check_password_hash(userdigest, password):
                return jsonify({'message': 'Login success!'}), 200
                
            else:
                return jsonify({'error': 'Please check your password'}), 401
        # 가입 안한  사용자라면
        else:
            return jsonify({'error': 'Join APP-nupan first'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        
    finally:
        dbclose(conn)


# 점주 회원가입 라우트
@app.route('/owner/register', methods=['POST'])
def owner_register():
    ownerID = request.json.get('ownerid')
    password = request.json.get('password')
    ownerName = request.json.get('ownername')
    ownerContact = request.json.get('ownercontact')
    
    # 인자값이 누락 되었을 경우
    if not all([ownerID, password, ownerName, ownerContact]): 
        return jsonify({'error': 'Missing fields'}), 400
    
    response = Registration.register(bcrypt, ownerID, password, ownerName, ownerContact, 'owners')
    return jsonify({'message': response}), 201


@app.route('/owner/login', methods=['POST'])
def owner_login():
    ownerid = request.json.get('ownerid')
    password = request.json.get('password')

    # 입력값 검증
    if not ownerid or not password:
        return jsonify({'error': 'Missing fields'}), 400

    conn = dbcon()
    cur = conn.cursor()
    
    try:
        # Owners 테이블에서 해당 ownerid 검색
        cur.execute("SELECT ownerdigest FROM owners WHERE ownerid = %s", (ownerid,))
        owner = cur.fetchone()

        if owner:
            ownerdigest = owner[0]
            
            if bcrypt.check_password_hash(ownerdigest, password):
                return jsonify({'message': 'Login success!'}), 200
                
            else:
                return jsonify({'error': 'Please check your password'}), 401
                
        else:
            return jsonify({'error': 'Please join APP-nupan first'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        
    finally:
        dbclose(conn)


@app.route('/store/11111/menu', methods=['GET'])
def get_menu():
    # 데이터베이스 연결
    conn = dbcon()  # 수정된 함수 호출
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        # 커서 생성
        cursor = conn.cursor(pymysql.cursors.DictCursor)  # 결과를 딕셔너리 형태로 받기 위한 설정

        # SQL 쿼리 실행
        query = "SELECT * FROM storemenu"
        cursor.execute(query)

        # 모든 데이터를 변수에 저장
        rows = cursor.fetchall()

        # 커서와 데이터베이스 연결 종료
        cursor.close()
        dbclose(conn)  # 수정된 함수 호출

        # 결과를 JSON 형태로 클라이언트에 보내기
        return jsonify(rows)

    except pymysql.MySQLError as e:
        print(f"Query failed: {e}")
        return jsonify({"error": "Query failed"}), 500
        
        
@app.route('/store/11111', methods=['GET'])
def get_stores():
    # 데이터베이스 연결
    conn = dbcon()  # 수정된 함수 호출
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        # 커서 생성
        cursor = conn.cursor(pymysql.cursors.DictCursor)  # 결과를 딕셔너리 형태로 받기 위한 설정

        # SQL 쿼리 실행
        query = "SELECT * FROM stores"
        cursor.execute(query)

        # 모든 데이터를 변수에 저장
        rows = cursor.fetchall()

        # 커서와 데이터베이스 연결 종료
        cursor.close()
        dbclose(conn)  # 수정된 함수 호출

        # 결과를 JSON 형태로 클라이언트에 보내기
        return jsonify(rows)

    except pymysql.MySQLError as e:
        print(f"Query failed: {e}")
        return jsonify({"error": "Query failed"}), 500