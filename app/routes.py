from flask import request, jsonify
from app import app, db
from app.models import Chat, Thread, User
from bson.objectid import ObjectId
from dotenv import load_dotenv
import google.generativeai as genai
import os
import requests
load_dotenv()


genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


def generate_sources(response_text):
    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={
                "temperature": 1,
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": 8192,
                "response_mime_type": "text/plain",
            },
        )

        chat_session = model.start_chat(
            history=[
                {
                    "role": "user",
                    "parts": [
                        f"Generate 3 links, and only links (no additional information) based on the following text:\n\n{
                            response_text}\n\nReturn the links in the following format: ['Source 1', 'Source 2', 'Source 3']"
                    ],
                }
            ]
        )

        response = chat_session.send_message(
            f"Generate 3 links related to the following content: {response_text}")
        sources = eval(response.text.strip())

        return sources
    except Exception as e:
        print("Error generating sources:", e)
        return []


def generate_follow_up_questions(response_text):
    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={
                "temperature": 1,
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": 8192,
                "response_mime_type": "text/plain",
            },
        )

        chat_session = model.start_chat(
            history=[
                {
                    "role": "user",
                    "parts": [
                        f"Generate 3 follow up questions based closely to this:\n\n{
                            response_text}\n\nReturn the links in the following format: ['Question 1', 'Question 2', 'Question 3']"
                    ],
                }
            ]
        )

        response = chat_session.send_message(
            f"Generate 3 follow ups related to the following content: {response_text}")
        sources = response.text.strip()

        return sources
    except Exception as e:
        print("Error generating sources:", e)
        return []


@app.route('/api/query', methods=['POST'])
def query():
    data = request.get_json()
    prompt = data.get("prompt", "")
    return_sources = data.get("returnSources", True)
    return_follow_up_questions = data.get("returnFollowUpQuestions", True)

    try:
      
        chat_session = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={
                "temperature": 1,
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": 8192,
                "response_mime_type": "text/plain",
            },
        ).start_chat(
            history=[
                {
                    "role": "user",
                    "parts": [prompt],
                }
            ]
        )

        response = chat_session.send_message(prompt)
        answer = response.text

        response_obj = {"answer": answer}

        if return_follow_up_questions:
            response_obj["followUpQuestions"] = generate_follow_up_questions(
                answer)

        if return_sources:
            response_obj["sources"] = generate_sources(answer)

        return jsonify(response_obj), 200

    except Exception as e:
        print("Error in fetching or generating response:", e)
        return jsonify({"error": "Internal Server Error"}), 500


@app.route('/api/test-db-connection', methods=['GET'])
def test_db_connection():
    try:
        collections = db.list_collection_names()
        return jsonify({"status": "success", "collections": collections}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/chats', methods=['POST'])
def create_chat():
    data = request.get_json()
    app.logger.info(f"Received data: {data}")
    generated_response = "This is a generated response from the AI."

    chat = Chat(
        prompt=data['prompt'],
        response=generated_response,
        thread_id=data['thread_id']
    )

    chat_id = chat.save().inserted_id

    return jsonify({
        "chat_id": str(chat_id),
        "prompt": data['prompt'],
        "response": generated_response
    }), 201


@app.route('/api/chats/<thread_id>', methods=['GET'])
def get_chats_by_thread_id(thread_id):
    try:
        chats = Chat.find_by_thread_id(thread_id)
        chat_list = []
        for chat in chats:
            chat_list.append({
                'id': str(chat['_id']),
                'prompt': chat['prompt'],
                'response': chat['response'],
                'creation_date': chat['creation_date'].isoformat(),
                'thread_id': str(chat['thread_id'])
            })
        return jsonify(chat_list), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/threads', methods=['POST'])
def create_thread():
    data = request.get_json()
    thread = Thread(
        title=data.get('title', 'New Chat'),
        user_id=data.get('user_id')
    )
    thread_id = thread.save().inserted_id
    return jsonify({"thread_id": str(thread_id), "title": thread.title}), 201


@app.route('/api/threads', methods=['GET'])
def get_threads():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400

    threads = Thread.find_by_user_id(user_id)
    return jsonify([{"id": str(thread["_id"]), "title": thread["title"], "creation_date": thread["creation_date"]} for thread in threads]), 200


@app.route('/api/threads/user/<user_id>', methods=['GET'])
def get_threads_by_user_id(user_id):
    try:
        # Fetch threads by user ID
        threads = Thread.find_by_user_id(user_id)
        # If threads are found, return them
        if threads:
            return jsonify([{
                "id": str(thread["_id"]),
                "title": thread["title"],
                "creation_date": thread["creation_date"],
                "user_id": str(thread["user_id"]),
            } for thread in threads]), 200
        else:
            return jsonify({"message": "No threads found for this user."}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/chats', methods=['GET'])
def get_chats():
    thread_id = request.args.get('thread_id')
    if not thread_id:
        return jsonify({"error": "Thread ID is required"}), 400

    chats = Chat.find_by_thread_id(thread_id)
    return jsonify([{
        "id": str(chat["_id"]),
        "prompt": chat["prompt"],
        "response": chat["response"],
        "creation_date": chat["creation_date"]
    } for chat in chats]), 200


@app.route('/api/threads/<thread_id>', methods=['DELETE'])
def delete_thread(thread_id):
    try:
        db.chats.delete_many({"thread_id": ObjectId(thread_id)})
        db.threads.delete_one({"_id": ObjectId(thread_id)})
        return jsonify({"message": "Thread and its chats have been deleted."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/threads/<thread_id>', methods=['PUT'])
def update_thread(thread_id):
    data = request.get_json()
    new_title = data.get('title')
    if not new_title:
        return jsonify({"error": "New title is required"}), 400

    try:
        db.threads.update_one(
            {"_id": ObjectId(thread_id)},
            {"$set": {"title": new_title}}
        )
        return jsonify({"message": "Thread title updated."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/chats/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    try:
        db.chats.delete_one({"_id": ObjectId(chat_id)})
        return jsonify({"message": "Chat has been deleted."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.get_json()
    user = User(
        username=data['username'],
        email=data['email']
    )
    user_id = user.save().inserted_id
    return jsonify({"user_id": str(user_id)}), 201


@app.route('/api/users/<user_id>', methods=['GET'])
def get_user(user_id):
    user = User.find_by_id(user_id)
    if user:
        return jsonify({
            "id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"],
            "creation_date": user["creation_date"]
        }), 200
    return jsonify({"error": "User not found"}), 404


@app.route('/api/users', methods=['GET'])
def get_users():
    users = User.find_all()
    return jsonify([{
        "id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "creation_date": user["creation_date"]
    } for user in users]), 200
