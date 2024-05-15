# # 라우트 정보를 담은 app.py
# from flask  import Flask, jsonify, request
# from flask_cors import CORS
# from flask_bcrypt import Bcrypt

# import os
# import uuid
# import pymysql
# from werkzeug.utils import secure_filename

# from dbconn import dbcon, dbclose
# from model_regist import Registration


# app = Flask(__name__)
# CORS(app)
# # Bcrypt 인스턴스 초기화
# bcrypt = Bcrypt(app)


# # user 회원가입 라우트
# @app.route('/user/register', methods=['POST', 'GET'])
# def user_register():
#     # POST 요청시 회원가입 로직 처리
#     if request.method == 'POST':
#         userID = request.json.get('userid')  
#         password = request.json.get('password')
#         userName = request.json.get('username')
#         userContact = request.json.get('usercontact')

#         # 인자값이 누락 되었을 경우
#         if not all([userID, userName, password, userContact]): 
#             return jsonify({'error': 'Missing fields'}), 400
        
#         response = Registration.register(bcrypt, userID, password, userName, userContact, 'users')
#         return jsonify({'message': response}), 201
        
#     elif request.method == 'GET':
#         # GET 요청 시, userid 중복 체크 로직
#         userID = request.args.get('userid')
        
#         # 인자 값이 누락되었다면
#         if not userID:
#             return jsonify({'error': 'userid is required for duplication check'}), 400

#         conn = dbcon()
#         cur = conn.cursor()
#         # 데이터베이스에서 userid 확인
#         cur.execute("SELECT userid FROM users WHERE userid = %s", (userID,))
#         user_exists = cur.fetchone()
#         dbclose(conn)

#         if user_exists:
#             return jsonify({'message': 'This userid is already taken'}), 409
#         else:
#             return jsonify({'message': 'This userid is available'}), 200
            

# # user 로그인 라우트
# @app.route('/user/login', methods=['POST'])
# def user_login():
#     # 클라이언트로부터 userid와 password 받기
#     userid = request.json.get('userid')
#     password = request.json.get('password')

#     # 입력값 검증
#     if not userid or not password:
#         return jsonify({'error': 'Missing fields'}), 400

#     conn = dbcon()
#     cur = conn.cursor()
    
#     try:
#         # 해당 userid에 맞는 userigest 불러오기
#         cur.execute("SELECT userdigest FROM users WHERE userid = %s", (userid,))
#         user = cur.fetchone()
#         # 이미 있는 사용자라면
#         if user:
#             userdigest = user[0]
            
#             # 비밀번호 검증
#             if bcrypt.check_password_hash(userdigest, password):
#                 return jsonify({'message': 'Login success!'}), 200
                
#             else:
#                 return jsonify({'error': 'Please check your password'}), 401
#         # 가입 안한  사용자라면
#         else:
#             return jsonify({'error': 'Join APP-nupan first'}), 404
            
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500
        
#     finally:
#         dbclose(conn)


# # 점주 회원가입 라우트
# @app.route('/owner/register', methods=['POST'])
# def owner_register():
#     ownerID = request.json.get('ownerid')
#     password = request.json.get('password')
#     ownerName = request.json.get('ownername')
#     ownerContact = request.json.get('ownercontact')
    
#     # 인자값이 누락 되었을 경우
#     if not all([ownerID, password, ownerName, ownerContact]): 
#         return jsonify({'error': 'Missing fields'}), 400
    
#     response = Registration.register(bcrypt, ownerID, password, ownerName, ownerContact, 'owners')
#     return jsonify({'message': response}), 201


# # 점주 로그인 라우트
# @app.route('/owner/login', methods=['POST'])
# def owner_login():
#     ownerid = request.json.get('ownerid')
#     password = request.json.get('password')

#     # 입력값 검증
#     if not ownerid or not password:
#         return jsonify({'error': 'Missing fields'}), 400

#     conn = dbcon()
#     cur = conn.cursor()
    
#     try:
#         # Owners 테이블에서 해당 ownerid 검색
#         cur.execute("SELECT ownerdigest FROM owners WHERE ownerid = %s", (ownerid,))
#         owner = cur.fetchone()

#         if owner:
#             ownerdigest = owner[0]
            
#             # 비밀번호 검증
#             if bcrypt.check_password_hash(ownerdigest, password):
#                 # Stores 테이블에서 ownerid에 해당하는 storeid 검색
#                 cur.execute("SELECT storeid, storename FROM stores WHERE ownerid = %s", (ownerid,))
#                 store = cur.fetchone()

#                 if store:
#                     storeid = store[0]
#                     storename = store[1]
#                     return jsonify({'message': 'Login success!', 'storeid': storeid, 'storename': storename}), 200
#                 else:
#                     # 해당 ownerid로 등록된 가게가 없는 경우
#                     return jsonify({'error': 'No store found for this owner'}), 404

#             else:
#                 return jsonify({'error': 'Please check your password'}), 401
                
#         else:
#             return jsonify({'error': 'Please join APP-nupan first'}), 404
            
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500
        
#     finally:
#         dbclose(conn)


# # 내가 들렀던 가게의 메뉴 불러오는 라우트(하드코딩)
# @app.route('/store/<string:storeid>/menu', methods=['GET'])
# def get_menu():
#     # 데이터베이스 연결
#     conn = dbcon()  # 수정된 함수 호출
#     if conn is None:
#         return jsonify({"error": "Database connection failed"}), 500

#     try:
#         # 커서 생성
#         cursor = conn.cursor(pymysql.cursors.DictCursor)  # 결과를 딕셔너리 형태로 받기 위한 설정

#         # SQL 쿼리 실행
#         query = "SELECT * FROM storemenu WHERE storeid = %s"
#         cursor.execute(query)

#         # 모든 데이터를 변수에 저장
#         rows = cursor.fetchall()

#         # 커서와 데이터베이스 연결 종료
#         cursor.close()
#         dbclose(conn)  # 수정된 함수 호출

#         # 결과를 JSON 형태로 클라이언트에 보내기
#         return jsonify(rows)

#     except pymysql.MySQLError as e:
#         print(f"Query failed: {e}")
#         return jsonify({"error": "Query failed"}), 500


# # 내가 들렀던 가게 호출 (하드코딩)
# @app.route('/store/11111', methods=['GET'])
# def get_stores():
#     # 데이터베이스 연결
#     conn = dbcon()  # 수정된 함수 호출
#     if conn is None:
#         return jsonify({"error": "Database connection failed"}), 500

#     try:
#         # 커서 생성
#         cursor = conn.cursor(pymysql.cursors.DictCursor)  # 결과를 딕셔너리 형태로 받기 위한 설정

#         # SQL 쿼리 실행
#         query = "SELECT * FROM stores"
#         cursor.execute(query)

#         # 모든 데이터를 변수에 저장
#         rows = cursor.fetchall()

#         # 커서와 데이터베이스 연결 종료
#         cursor.close()
#         dbclose(conn)  # 수정된 함수 호출

#         # 결과를 JSON 형태로 클라이언트에 보내기
#         return jsonify(rows)

#     except pymysql.MySQLError as e:
#         print(f"Query failed: {e}")
#         return jsonify({"error": "Query failed"}), 500


# # 점주가 처음 가맹점 신청을 하는 라우트
# @app.route('/store/regist', methods=['POST'])
# def store_regist():
#     data = request.get_json()
#     storename = data.get('storename')
#     address = data.get('address')
#     contact = data.get('contact')
#     ownerid = data.get('ownerid')

#     conn = dbcon()
#     if conn is None:
#         return jsonify({"error": "Database connection failed"}), 500

#     try:
#         with conn.cursor() as cursor:
#             sql = """
#             INSERT INTO pendingstores (storename, address, contact, ownerid, memo, status)
#             VALUES (%s, %s, %s, %s, NULL, NULL)
#             """
#             cursor.execute(sql, (storename, address, contact, ownerid))
#             conn.commit()

#         return jsonify({"success": "Store added successfully"}), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

#     finally:
#         dbclose(conn)


# # 승인 여부를 기다리는 모든 가게 정보를 호출하는 라우트
# @app.route('/store', methods=['GET'])
# def get_pendingstores():
#     # DB 연결
#     conn = dbcon()
#     if conn is None:
#         return jsonify({'error': 'Database connection failed'}), 500

#     try:
#         with conn.cursor() as cursor:
#             # status가 NULL인 pendingstores에서 데이터 조회
#             sql = """
#             SELECT tempstoreid, ownerid, storename, address, contact
#             FROM pendingstores
#             WHERE status IS NULL
#             """
#             cursor.execute(sql)
#             results = cursor.fetchall()
            
#             # 결과가 없는 경우
#             if not results:
#                 return jsonify({'error': 'No pending stores found'}), 404
            
#             # 결과를 JSON 형식으로 변환
#             pending_stores = []
#             for result in results:
#                 tempstoreid, ownerid, storename, address, contact = result
#                 pending_stores.append({
#                     'tempstoreid': tempstoreid,
#                     'ownerid': ownerid,
#                     'storename': storename,
#                     'address': address,
#                     'contact': contact
#                 })

#             return jsonify({'pendingStores': pending_stores}), 200
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500
#     finally:
#         # DB 연결 종료
#         dbclose(conn)


# # 가맹점 신청 승락하는 라우트
# @app.route('/store/confirm', methods=['POST'])
# def store_confirm():
#     # JSON 데이터로부터 tempstoreid 받아오기
#     data = request.get_json()
#     tempstore_id = data['tempstoreid']
    
#     # DB 연결
#     conn = dbcon()
#     if conn is None:
#         return jsonify({'error': 'Database connection failed'}), 500

#     try:
#         with conn.cursor() as cursor:
#             # pendingstores에서 승인되지 않은 데이터 조회
#             sql = """
#             SELECT ownerid, storename, address, contact
#             FROM pendingstores
#             WHERE tempstoreid = %s AND status IS NULL
#             """
#             cursor.execute(sql, (tempstore_id,))
#             result = cursor.fetchone()
#             if result:
#                 ownerid, storename, address, contact = result

#                 # storeid로 사용할 랜덤 UID 생성
#                 storeid = str(uuid.uuid4())

#                 # stores 테이블에 데이터 저장
#                 insert_sql = """
#                 INSERT INTO stores (storeid, ownerid, storename, address, storecontact)
#                 VALUES (%s, %s, %s, %s, %s)
#                 """
#                 cursor.execute(insert_sql, (storeid, ownerid, storename, address, contact))
                
#                 # pendingstores 테이블의 status 업데이트
#                 update_sql = """
#                 UPDATE pendingstores
#                 SET status = 1
#                 WHERE tempstoreid = %s
#                 """
#                 cursor.execute(update_sql, (tempstore_id,))
                
#                 conn.commit()

#                 return jsonify({'success': 'Store confirmed', 'storeid': storeid}), 200
#             else:
#                 return jsonify({'error': 'No data found with provided tempstoreid or already processed'}), 404
    
#     except pymysql.MySQLError as e:
#         print(f"SQL Error: {e}")
#         return jsonify({'error': str(e)}), 500
    
#     finally:
#         # DB 연결 종료
#         dbclose(conn)


# # 가맹점 신청거부하는 라우트
# @app.route('/store/deny', methods=['PUT'])
# def store_deny():
#     # JSON 데이터로부터 tempstoreid 받아오기
#     data = request.get_json()
#     tempstore_id = data['tempstoreid']
    
#     # DB 연결
#     conn = dbcon()
#     if conn is None:
#         return jsonify({'error': 'Database connection failed'}), 500

#     try:
#         with conn.cursor() as cursor:
#             # pendingstores 테이블의 status를 0으로 업데이트
#             update_sql = """
#             UPDATE pendingstores
#             SET status = 0
#             WHERE tempstoreid = %s AND status IS NULL
#             """
#             affected_rows = cursor.execute(update_sql, (tempstore_id,))
#             conn.commit()

#             if affected_rows == 0:
#                 # 해당 ID가 이미 처리되었거나 존재하지 않는 경우
#                 return jsonify({'error': 'No pending store found with provided tempstoreid or already processed'}), 404
#             return jsonify({'success': 'Store application has been denied'}), 200
#     except pymysql.MySQLError as e:
#         print(f"SQL Error: {e}")
#         return jsonify({'error': str(e)}), 500
#     finally:
#         # DB 연결 종료
#         dbclose(conn)


# # 가게 메뉴 등록하는 라우트
# # 멀티파트/폼으로 보내기
# @app.route('/store/<string:storeid>/menu', methods=['POST'])
# def storemenu_post(storeid):
#     # URL에서 받은 storeid 사용
#     productname = request.values.get('productname')
#     storename = request.values.get('storename')
#     price = request.values.get('price')
#     category = request.values.get('category')
#     menuimage = request.files.get('menuimage')

#     if not menuimage:
#         return jsonify({'error': 'No image provided'}), 400

#     # 이미지 파일을 안전하게 저장하기 위한 파일명 생성
#     filename = secure_filename(menuimage.filename)
#     # 임시 저장 경로 설정
#     temp_path = os.path.join('/home/ubuntu/appnupan/tmp', filename)
#     os.makedirs(os.path.dirname(temp_path), exist_ok=True)
#     menuimage.save(temp_path)

#     # 파일을 열어 BLOB으로 데이터베이스에 저장
#     with open(temp_path, 'rb') as file:
#         binary_data = file.read()

#     # DB 연결
#     conn = dbcon()
#     if conn is None:
#         return jsonify({'error': 'Database connection failed'}), 500

#     try:
#         with conn.cursor() as cursor:
#             # storemenu 테이블에 데이터 삽입
#             sql = """
#             INSERT INTO storemenu (storeid, productname, storename, price, menuimage, category)
#             VALUES (%s, %s, %s, %s, %s, %s)
#             """
#             cursor.execute(sql, (storeid, productname, storename, price, binary_data, category))
#             conn.commit()
#             return jsonify({'success': 'Menu item added successfully'}), 201
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500
#     finally:
#         # 임시 파일 삭제
#         os.remove(temp_path)
#         # DB 연결 종료
#         dbclose(conn)


# @app.route('/united/register', methods=['POST'])
# def united_register():
#     data = request.get_json()
#     ownerID = data.get('ownerid')
#     password = data.get('password')
#     ownerName = data.get('ownername')
#     ownerContact = data.get('ownercontact')
#     storename = data.get('storename')
#     address = data.get('address')
#     contact = data.get('contact')

#     # 인자값이 누락되었을 경우 검증
#     if not all([ownerID, password, ownerName, ownerContact, storename, address, contact]):
#         return jsonify({'error': 'Missing fields'}), 400
    
#     # 데이터베이스 연결
#     conn = dbcon()
#     if conn is None:
#         return jsonify({"error": "Database connection failed"}), 500

#     try:
#         with conn.cursor() as cursor:
#             # 가게주인 회원가입 처리
#             registration_response = Registration.register(bcrypt, ownerID, password, ownerName, ownerContact, 'owners')

#             # 가맹점 등록 처리
#             store_sql = """
#             INSERT INTO pendingstores (storename, address, contact, ownerid, memo, status)
#             VALUES (%s, %s, %s, %s, NULL, NULL)
#             """
#             cursor.execute(store_sql, (storename, address, contact, ownerID))
#             conn.commit()

#         return jsonify({
#             "message": "Owner registered and store added successfully",
#             "registration_response": registration_response
#         }), 200

#     except Exception as e:
#         conn.rollback()  # 롤백 처리
#         return jsonify({"error": str(e)}), 500

#     finally:
#         dbclose(conn)


# @app.route('/owner/search', methods=['get'])
# def search_owner():
#     pass