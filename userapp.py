'''
# 고객 사용자들이 접근하는 라우트들을 모아둔 userapp.py
from flask import Blueprint, jsonify, request
from flask_bcrypt import Bcrypt
from marshmallow import Schema, fields, post_load, ValidationError
from dbconn import dbcon, dbclose

user_bp = Blueprint('user', __name__)

bcrypt = Bcrypt()

class UserSchema(Schema):
    userid = fields.Str(required=True)
    username = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)
    usercontact = fields.Str()

    @post_load
    def make_user(self, data, **kwargs):
        data['password'] = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        return data

user_schema = UserSchema()

@user_bp.route('/register', methods=['POST'])
def register():
    try:
        user = user_schema.load(request.get_json())
        conn = dbcon()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users(userid, username, userdigest, usercontact) VALUES(%s, %s, %s, %s)
            """, (user['userid'], user['username'], user['password'], user['usercontact']))
        conn.commit()
        dbclose(conn)
        return jsonify({"message": "User registered successfully"}), 201
    except ValidationError as err:
        return jsonify(err.messages), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@user_bp.route('/login', methods=['POST'])
def login():
    try:
        login_data = request.get_json()
        conn = dbcon()
        cur = conn.cursor()
        cur.execute("SELECT userdigest FROM users WHERE userid = %s", (login_data['userid'],))
        user = cur.fetchone()
        if user:
            if bcrypt.check_password_hash(user[0], login_data['password']):
                return jsonify({'message': 'Login successful!'}), 200
            else:
                return jsonify({'error': 'Invalid credentials'}), 401
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        dbclose(conn)
'''