from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime

client = MongoClient('mongodb://localhost:27017/')
db = client['aisearch']


class Chat:
    def __init__(self, prompt, response, thread_id):
        self.prompt = prompt
        self.response = response
        self.creation_date = datetime.now()
        self.thread_id = ObjectId(thread_id)

    def save(self):
        chat_data = {
            'prompt': self.prompt,
            'response': self.response,
            'creation_date': self.creation_date,
            'thread_id': self.thread_id
        }
        result = db.chats.insert_one(chat_data)
        print(f"Chat inserted with ID: {result.inserted_id}")  # Debugging line
        return result

    @staticmethod
    def find_by_thread_id(thread_id):
        return list(db.chats.find({'thread_id': ObjectId(thread_id)}))


class Thread:
    def __init__(self, title='New Chat', user_id=None):
        self.title = title
        self.creation_date = datetime.now()
        self.user_id = ObjectId(user_id) if user_id else None

    def save(self):
        thread_data = {
            'title': self.title,
            'creation_date': self.creation_date,
            'user_id': self.user_id
        }
        result = db.threads.insert_one(thread_data)
        print(f"Thread inserted with ID: {
              result.inserted_id}")  # Debugging line
        return result

    @staticmethod
    def find_by_user_id(user_id):
        return list(db.threads.find({'user_id': ObjectId(user_id)}))


class User:
    def __init__(self, username, email):
        self.username = username
        self.email = email
        self.creation_date = datetime.now()

    def save(self):
        user_data = {
            'username': self.username,
            'email': self.email,
            'creation_date': self.creation_date,
        }
        return db.users.insert_one(user_data)

    @staticmethod
    def find_by_id(user_id):
        return db.users.find_one({"_id": ObjectId(user_id)})

    @staticmethod
    def find_by_email(email):
        return db.users.find_one({"email": email})

    @staticmethod
    def find_all():
        return list(db.users.find())
    
    @staticmethod
    def find_by_user_id(user_id):
        return list(db.threads.find({'user_id': ObjectId(user_id)}))
