import json
from flask import Flask, render_template, jsonify, request
from datetime import datetime
import requests
import sys

app = Flask(__name__)

known_users = []
messages = []

username = "testuser"


@app.route('/', methods=['GET'])
def index():
    return render_template('list.html', users=known_users, name=username)


@app.route('/add', methods=['POST'])
def add():
    body = request.get_json()
    url = body['url']

    if url is None:
        return jsonify({"error": "No URL"}), 400

    for user in known_users:
        if clean_url(user['url']) == clean_url(url):
            return jsonify(known_users), 200

    global username
    r = requests.post(f"{clean_url(url)}/announce",
                      json={"url": request.host, "username": username})
    response = r.json()
    username = response['username']
    url = response['url']
    other_users = response['other_users']

    new_user = {"username": username, "url": clean_url(url)}
    known_users.append(new_user)

    for other_user in other_users:
        other_user_name = other_user['username']
        other_user_url = other_user['url']
        if not contains_user(known_users, other_user):
            known_users.append(
                {"username": other_user_name, "url": clean_url(other_user_url)})

    return jsonify(known_users), 200


def contains_user(users: list, user: dict) -> bool:
    for existing_user in users:
        if existing_user['url'] == user['url']:
            return True
    return False


def clean_url(url: str) -> str:
    if not url.startswith('http'):
        url = f"http://{url}"
    if url[-1] == '/':
        return url[:-1]
    return url


@app.route('/sendmessage', methods=['POST'])
def send_message():
    body = request.get_json()
    message = body['message']

    if message is None:
        return jsonify({"error": "No message"}), 400

    curr_timestamp = datetime.now()

    message_to_send = {"message": message, "timestamp": curr_timestamp}
    messages.append(message_to_send)

    for user in known_users:
        send_message_to_user(user, message_to_send)


@app.route('/onmessage', methods=['POST'])
def on_message():
    body = request.get_json()
    message = body['message']
    timestamp = body['timestamp']

    if message is None:
        return jsonify({"error": "No message"}), 400

    if timestamp is None:
        return jsonify({"error": "No timestamp"}), 400

    cleaned_message = {"message": message, "timestamp": timestamp}
    if is_existing_message(messages, cleaned_message):
        return jsonify({"error": "Message already received"}), 400

    messages.append(cleaned_message)

    for user in known_users:
        send_message_to_user(user, cleaned_message)


def send_message_to_user(user: dict, message: dict) -> None:
    url = user['url']
    r = requests.post(f"{clean_url(url)}/onmessage",
                      json={"message": message, "timestamp": timestamp})


def send_new_user_to_user(user: dict, new_user: dict) -> None:
    url = user['url']
    r = requests.post(f"{clean_url(url)}/announce", json=new_user)


def is_existing_message(messages: list, message: dict) -> bool:
    for existing_message in messages:
        if existing_message['message'] == message["message"] and existing_message['timestamp'] == message["timestamp"]:
            return True
    return False


@app.route('/announce', methods=['POST'])
def announce():
    body = request.get_json()
    new_url = body['url']
    new_username = body['username']

    if new_url is None:
        return jsonify({"error": "No URL"}), 400

    if new_username is None:
        return jsonify({"error": "No username"}), 400

    new_user = {"username": new_username, "url": clean_url(new_url)}
    curr_user = {"username": username,
                 "url": request.host, "other_users": known_users}
    if contains_user(known_users, new_user):
        return jsonify(curr_user), 200

    known_users.append(new_user)

    for user in known_users:
        send_new_user_to_user(user, new_user)

    return jsonify(curr_user), 200


if __name__ == '__main__':
    # get port from command line
    try:
        port = int(sys.argv[1])
    except:
        raise Exception("Please provide a port number")

    try:
        username = str(sys.argv[2])
    except:
        raise Exception("Please provide a username")

    app.run(debug=True, port=port, host='0.0.0.0')
