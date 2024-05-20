# 가게의 메뉴와 QR코드를 저장하고 조회하는 라우트들을 모아둔 app_store.py
import os
import pymysql
from flask_cors import CORS
from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename
from marshmallow import Schema, fields, validate

from dbconn import dbcon, dbclose


app_order = Blueprint('order', __name__)
CORS(app_order)

class OrderSchema(Schema):
    orderid = fields.Int(dump_only=True)