# 앱 실행부 runserver.py
from flask import Flask
from app_user import app_user, init_bcrypt
from app_owner import app_owner, init_bcrypt
from app_franchise import app_franchise
from app_store import app_store


# 앱서버 초기화
app = Flask(__name__)


# 각 Blueprint를 URL 접두어와 함께 등록
# 여기서 라우트들의 첫번째 엔드포인트 지정
app.register_blueprint(app_user, url_prefix='/user')
app.register_blueprint(app_owner, url_prefix='/owner')
app.register_blueprint(app_franchise, url_prefix='/franchise')
app.register_blueprint(app_store, url_prefix='/store')


# Bcrypt 초기화
init_bcrypt(app)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port='8000', debug=True)
# host : 서버 IP, 0.0.0.0은 로컬 호스트를 지칭함
# port : 웹서버를 8000포트에서 실행하겠다는 설정
# debug : 직접 실행부를 실행했을때 터미널창에서 오류 로그 출력해줌