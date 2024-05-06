'''
# 가게 사용자들이 접근하는 라우트들을 모아둔 ownerapp.py
from flask import Blueprint, jsonify, request
from flask_bcrypt import Bcrypt
from marshmallow import Schema, fields, post_load, ValidationError
from dbconn import dbcon, dbclose

owner_bp = Blueprint('owner', __name__)

bcrypt = Bcrypt()

class OwnerSchema(Schema):
    ownerid = fields.Str(required=True)
    ownername = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)
    ownercontact = fields.Str()

    @post_load
    def make_owner(self, data, **kwargs):
        data['ownerdigest'] = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        return data

owner_schema = OwnerSchema()

@owner_bp.route('/register', methods=['POST'])
def register():
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

@owner_bp.route('/login', methods=['POST'])
def login():
    try:
        login_data = request.get_json()
        conn = dbcon()
        cur = conn.cursor()
        cur.execute("SELECT ownerdigest FROM owners WHERE ownerid = %s", (login_data['ownerid'],))
        owner = cur.fetchone()
        if owner and bcrypt.check_password_hash(owner['ownerdigest'], login_data['password']):
            return jsonify({'message': 'Login successful!'}), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        dbclose(conn)
'''