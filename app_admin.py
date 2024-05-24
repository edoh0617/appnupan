# 관리자가 사용자 정보를 조회하는 라우트들을 모아둔 app_admin.py
# 이 모듈의 라우트들은 GET방식을 사용하지 않을거임
import os
import pymysql

from flask_cors import CORS
from flask import Blueprint, jsonify, request
from marshmallow import Schema, fields, validate
# from werkzeug.utils import secure_filename

from dbconn import dbcon, dbclose


app_admin = Blueprint('admin', __name__)
CORS(app_admin)


# JSON 데이터 직렬화
class UserSchema(Schema):
    userid = fields.String(required=True, validate=[validate.Length(min=1, max=45)])
    username = fields.String(required=True, validate=[validate.Length(min=1, max=45)])
    password = fields.String(required=True, validate=[validate.Length(min=1)])
    usercontact = fields.String(validate=[validate.Length(max=45)])


user_schema = UserSchema()
users_schema = UserSchema(many=True)


# 모든 사용자의 정보를 조회하는 라우트
@app_admin.route('/view/users', methods=['POST'])
def get_all_users():
    conn = dbcon()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cur = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        cur.execute("SELECT userid, username, usercontact FROM users")
        users = cur.fetchall()
        return jsonify(users), 200
    
    except pymysql.MySQLError as e:
        return jsonify({'error': str(e)}), 500

    finally:
        cur.close()
        dbclose(conn)


# 특정 사용자의 정보를 조회하는 라우트
@app_admin.route('/view/user', methods=['POST'])
def get_user():
    data = request.get_json()
    
    # userid와 username 중 하나는 반드시 있어야 함
    if not data or ('userid' not in data and 'username' not in data):
        return jsonify({'error': 'Either userid or username must be provided'}), 400

    userid = data.get('userid')
    username = data.get('username')

    # 조건에 맞는 SQL 쿼리 작성
    query = "SELECT userid, username, usercontact FROM users WHERE"
    conditions = []
    values = []

    if userid:
        conditions.append(" userid = %s")
        values.append(userid)
    if username:
        conditions.append(" username = %s")
        values.append(username)

    # 조건을 OR로 결합
    query += " OR".join(conditions)

    conn = dbcon()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cur = conn.cursor(pymysql.cursors.DictCursor)
        cur.execute(query, values)
        users = cur.fetchall()

        if not users:
            return jsonify({'message': 'No user found'}), 404

        return jsonify(users_schema.dump(users)), 200

    except pymysql.MySQLError as e:
        return jsonify({'error': str(e)}), 500

    finally:
        cur.close()
        dbclose(conn)





# JSON 데이터 직렬화
class OwnerSchema(Schema):
    ownerid = fields.String(required=True, validate=[validate.Length(min=1, max=45)])
    ownername = fields.String(required=True, validate=[validate.Length(min=1, max=45)])
    ownercontact = fields.String(validate=[validate.Length(max=45)])
    storeid = fields.String(required=True, validate=[validate.Length(min=1, max=100)])
    storename = fields.String(required=True, validate=[validate.Length(min=1, max=45)])
    address = fields.String(validate=[validate.Length(max=100)])
    storecontact = fields.String(validate=[validate.Length(max=100)])

owner_schema = OwnerSchema()
owners_schema = OwnerSchema(many=True)


# 모든 가맹점주의 정보를 조회하는 라우트
@app_admin.route('/view/owners', methods=['POST'])
def get_all_owners():
    conn = dbcon()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cur = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        query = """
            SELECT o.ownerid, o.ownername, o.ownercontact, s.storeid, s.storename, s.address, s.storecontact
            FROM owners o
            LEFT JOIN stores s ON o.ownerid = s.ownerid
        """
        cur.execute(query)
        owners = cur.fetchall()
        return jsonify(owners_schema.dump(owners)), 200
    
    except pymysql.MySQLError as e:
        return jsonify({'error': str(e)}), 500

    finally:
        cur.close()
        dbclose(conn)


# 특정 점주에 대한 정보를 조회하는 라우트
@app_admin.route('/view/owner', methods=['POST'])
def get_owner():
    pass