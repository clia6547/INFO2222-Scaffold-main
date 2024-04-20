'''
app.py contains all of the server application
this is where you'll find all of the get/post request handlers
the socket event handlers are inside of socket_routes.py
'''

from flask import Flask, render_template, request, abort, url_for, jsonify, redirect
from flask_socketio import SocketIO
import db
import secrets
from models import User
from flask import session
from sqlalchemy.orm import Session
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

import os
import ssl

import hashlib
import base64
# import logging

# this turns off Flask Logging, uncomment this to turn off Logging
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)

app = Flask(__name__)

# secret key used to sign the session cookie
app.config['SECRET_KEY'] = secrets.token_hex()
socketio = SocketIO(app)

# don't remove this!!
import socket_routes

# index page
@app.route("/")
def index():
    return render_template("index.jinja")

# login page
@app.route("/login")
def login():    
    return render_template("login.jinja")

# handles a post request when the user clicks the log in button
@app.route("/login/user", methods=["POST"])
def login_user():
    if not request.is_json:
        abort(404)

    username = request.json.get("username")
    password = request.json.get("password")

    user =  db.get_user(username)
    if user is None:
        return "Error: User does not exist!"
    
    stored_password_hash = user.password
    salt = user.salt
    print("stored_password_hash:", stored_password_hash)
    combined_password = password + salt
    hashed_password_bytes = hashlib.sha256(combined_password.encode()).digest()
    hashed_password = base64.b64encode(hashed_password_bytes).decode()
    print("hashed_password:", hashed_password)

    if hashed_password != stored_password_hash:
        return "Error: Password does not match!"
    
    # Reset the session for each new login
    session.clear()
    session['username'] = username  # Correctly setting the username in the session
    # return jsonify({"success": True, "url": url_for('home', username=username)})

    return url_for('home', username=request.json.get("username"))

# handles a get request to the signup page
@app.route("/signup")
def signup():
    return render_template("signup.jinja")

# handles a post request when the user clicks the signup button
@app.route("/signup/user", methods=["POST"])
def signup_user():
    if not request.is_json:
        return jsonify({"success": False, "error": "Invalid request"}), 400

    data = request.get_json()
    print(f"Received signup data: {data}")

    username = request.json.get("username")
    password = request.json.get("password")
    salt = request.json.get("salt")
    public_key = request.json.get("publicKey")
    if public_key is None:
        print("Public key is missing from the data.")
    # print(f"Received public key for {username}: {public_key}")  # Debug log

    if db.get_user(username) is None:
        db.insert_user(username, password, salt, public_key)
        session['username'] = username  # Set up user session
        return jsonify({"success": True, "url": url_for('home', username=username)})
    else:
        return jsonify({"success": False, "error": "User already exists!"})


# handler when a "404" error happens
@app.errorhandler(404)
def page_not_found(_):
    return render_template('404.jinja'), 404

# home page, where the messaging app is
@app.route("/home")
def home():
    # if request.args.get("username") is None:
    #     abort(404)
    # return render_template("home.jinja", username=request.args.get("username"))
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if the user is not in session
    username = session['username']
    return render_template("home.jinja", username=username)

@app.route("/api/get_public_key/<username>", methods=['GET'])
def get_public_key(username):
    user = db.get_user(username)
    if user and user.public_key:
        return jsonify(publicKey=user.public_key)
    else:
        return jsonify(error="User or public key not found"), 404


if __name__ == '__main__':
    cert_file = os.path.join(os.getcwd(), 'localhost.pem')
    key_file = os.path.join(os.getcwd(), 'localhost-key.pem')

    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(certfile=cert_file, keyfile=key_file)

    ssl_context.set_ciphers('ECDHE-RSA-AES256-GCM-SHA384')
    ssl_context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1 | ssl.OP_NO_COMPRESSION | ssl.OP_SINGLE_ECDH_USE

    socketio.run(app, host='127.0.0.1', port=5000, ssl_context=ssl_context)
