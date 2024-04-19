'''
socket_routes
file containing all the routes related to socket.io
'''


from flask_socketio import join_room, emit, leave_room, SocketIO
from flask import request

try:
    from __main__ import socketio
except ImportError:
    from app import socketio

from models import Room, User, Message

import db
from os import urandom
from sqlalchemy.orm import Session

room = Room()

# when the client connects to a socket
# this event is emitted when the io() function is called in JS
@socketio.on('connect')
def connect():
    
    username = request.cookies.get("username")
    room_id = request.cookies.get("room_id")
    if room_id is None or username is None:
        return
    friends = db.get_friends(username)
    if friends:
        emit("friend_list", friends)
    # socket automatically leaves a room on client disconnect
    # so on client connect, the room needs to be rejoined
    join_room(int(room_id))
    emit("incoming", (f"{username} has connected", "green"), to=int(room_id))
    # emit("incoming", (f"message: Hello, this is a test from the server."))

# event when client disconnects
# quite unreliable use sparingly
@socketio.on('disconnect')
def disconnect():
    username = request.cookies.get("username")
    room_id = request.cookies.get("room_id")
    if room_id is None or username is None:
        return
    emit("incoming", (f"{username} has disconnected", "red"), to=int(room_id))

# send message event handler
@socketio.on("send")
def send(username, message, room_id):
    emit("incoming", (f"{username}: {message}"), to=room_id)
    
# join room event handler
# sent when the user joins a room
@socketio.on("join")
def join(sender_name, receiver_name):
    
    receiver = db.get_user(receiver_name)
    if receiver is None:
        return "Unknown receiver!"
    
    sender = db.get_user(sender_name)
    if sender is None:
        return "Unknown sender!"

    room_id = room.get_room_id(receiver_name)

    # if the user is already inside of a room 
    if room_id is not None:
        
        #socketio.emit("friend_request", sender_name, room=room_id)
        room.join_room(sender_name, room_id)
        join_room(room_id)
        # emit to everyone in the room except the sender
        emit("incoming", (f"{sender_name} has joined the room.", "green"), to=room_id, include_self=False)
        # emit only to the sender
        emit("incoming", (f"{sender_name} has joined the room. Now talking to {receiver_name}.", "green"))
        return room_id

    # if the user isn't inside of any room, 
    # perhaps this user has recently left a room
    # or is simply a new user looking to chat with someone
    room_id = room.create_room(sender_name, receiver_name)
    join_room(room_id)
    emit("incoming", (f"{sender_name} has joined the room. Now talking to {receiver_name}.", "green"), to=room_id)
    return room_id

# leave room event handler
@socketio.on("leave")
def leave(username, room_id):
    emit("incoming", (f"{username} has left the room.", "red"), to=room_id)
    leave_room(room_id)
    room.leave_room(username)

# Receive friend request event handler
@socketio.on("friend_request")
def receive_friend_request(sender_name, receiver_name):
    sender = db.get_user(sender_name)
    receiver = db.get_user(receiver_name)
    
    if sender is None or receiver is None:
        if sender is None:
            return f"Unknown sender: {sender_name}"
        else:
            return f"Unknown receiver: {receiver_name}"
    
    room_id = room.get_room_id(receiver_name)
    if room_id is not None:
        # Emit a message to inform the receiver about the friend request
        emit("friend_request", sender_name, to=room_id, include_self=False)
        return "request sent"
    else:
        return "User not in a room"
    
# Accept friend request event handler
@socketio.on("accept_friend_request")
def accept_friend_request(receiver_name, sender_name):
    sender = db.get_user(sender_name)
    receiver = db.get_user(receiver_name)
    
    if sender is None or receiver is None:
        return "Unknown user"
    
    # Add both users as friends in the database
    db.insert_friendship(sender_name, receiver_name)
    db.insert_friendship(receiver_name, sender_name)
    
    # Get updated friend lists for both sender and receiver
    sender_friends = db.get_friends(sender_name)
    receiver_friends = db.get_friends(receiver_name)
    
    # Emit updated friend lists to the respective users
    emit("friend_list", sender_friends, to=sender_name)
    emit("friend_list", receiver_friends, to=receiver_name)

