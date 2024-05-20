# 회원가입 모듈 model_regist.py
from dbconn import dbcon, dbclose
from flask_bcrypt import Bcrypt


class Registration:
    # 생성자
    def __init__(self, bcrypt):
        self.bcrypt = bcrypt


    # 비밀번호 해시 생성 메서드
    def _create_digest(self, password):
        return self.bcrypt.generate_password_hash(password).decode('utf-8')


    # DB에 삽입 하는 메서드
    def _insert_to_db(self, sql, data):
        conn = dbcon()
        try:
            cur = conn.cursor()
            cur.execute(sql, data)
            conn.commit()
        finally:
            dbclose(conn)


    # 고객(앱) 사용자 회원가입 메서드
    def register_user(self, userid, password, username, usercontact):
        # 해시된 비밀번호
        digest = self._create_digest(password)
        sql = """
        INSERT INTO users(userid, username, userdigest, usercontact) VALUES(%s, %s, %s, %s)
        """
        data = (userid, username, digest, usercontact)
        self._insert_to_db(sql, data)
        return f"{username} registered successfully in users table!"


    # 점주(웹) 사용자 회원가입 메서드
    def register_owner(self, ownerid, password, ownername, ownercontact):
        # 해시된 비밀번호
        digest = self._create_digest(password)
        sql = """
        INSERT INTO owners(ownerid, ownername, ownerdigest, ownercontact) VALUES(%s, %s, %s, %s)
        """
        data = (ownerid, ownername, digest, ownercontact)
        self._insert_to_db(sql, data)
        return f"{ownername} registered successfully in owners table!"






'''
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
'''