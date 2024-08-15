from flask import Flask
from pymongo import MongoClient
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins="*")

client = MongoClient('mongodb://localhost:27017/')
db = client['aisearch']

from app import routes