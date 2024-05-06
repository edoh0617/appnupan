# Dockerfile
# 기본 이미지 설정
FROM ubuntu:latest

# 패키지 목록 업데이트
RUN apt-get update

# Python 설치
RUN apt-get install -y python3

# pip와 가상 환경 패키지 설치
RUN apt-get install -y python3-pip python3-venv

# Nginx 설치
RUN apt-get install -y nginx

# Gunicorn 설치
RUN apt-get install -y gunicorn

# 기타 패키지 관리 명령 (옵션)
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# 가상 환경 설정
RUN python3 -m venv /home/ubuntu/appnupan/anp

# 환경 변수 설정
ENV PATH="/home/ubuntu/appnupan/anp/bin:$PATH"

# 애플리케이션 디렉토리 생성
WORKDIR /home/ubuntu/appnupan

# Python 의존성 파일 복사
COPY requirements.txt /home/ubuntu/appnupan/

# 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 파일 복사
COPY . /home/ubuntu/appnupan

# Nginx 설정 복사 및 활성화
COPY nginx.conf /etc/nginx/sites-available/default
RUN rm -f /etc/nginx/sites-enabled/default && ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled
RUN echo "daemon off;" >> /etc/nginx/nginx.conf

# 애플리케이션 실행 포트 열기
EXPOSE 80

# Nginx와 Gunicorn을 시작하는 CMD 설정
CMD service nginx start && gunicorn --workers 3 --bind 0.0.0.0:8000 runserver:app