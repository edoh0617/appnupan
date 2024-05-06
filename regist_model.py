# 회원가입 모듈 regist_model.py
from dbconn import dbcon, dbclose
from flask_bcrypt import Bcrypt

class Registration():
    @staticmethod
    def register(bcrypt, id, password, name, contact, table):
        conn = dbcon()
        
        # Bcrypt를 사용하여 비밀번호 해시 생성
        digest = bcrypt.generate_password_hash(password).decode('utf-8')

        # SQL 쿼리문 선택
        if table == 'users':
            sql = """
            INSERT INTO users(userid, username, userdigest, usercontact) VALUES(%s, %s, %s, %s)
            """
        
        elif table == 'owners':
            sql = """
            INSERT INTO owners(ownerid, ownername, ownerdigest, ownercontact) VALUES(%s, %s, %s, %s)
            """

        # 데이터를 튜플형식으로 변경
        data = (id, name, digest, contact)
        
        # SQL문 실행
        cur = conn.cursor()
        cur.execute(sql, data)
        conn.commit()
        dbclose(conn)

        return f"{name} registered successfully in {table}!"