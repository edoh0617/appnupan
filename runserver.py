# 앱 실행부 runserver.py
from flask import Flask
from app import app

if __name__ == "__main__":
    app.run(host='0.0.0.0', port='8000', debug=True)
			# port : 웹서버를 8000포트에서 실행하겠다는 설정