'''
models
defines sql alchemy data models
also contains the definition for the room class used to keep track of socket.io rooms

Just a sidenote, using SQLAlchemy is a pain. If you want to go above and beyond, 
do this whole project in Node.js + Express and use Prisma instead, 
Prisma docs also looks so much better in comparison

or use SQLite, if you're not into fancy ORMs (but be mindful of Injection attacks :) )
'''

from sqlalchemy import String, Column, ForeignKey,Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from typing import Dict

# data models
Base = declarative_base()

# model to store user information
class Friendship(Base):
    __tablename__ = "friendship"
    
    user1 = Column(String, ForeignKey('user.username'), primary_key=True)
    user2 = Column(String, ForeignKey('user.username'), primary_key=True)
    
    # Define a bidirectional relationship
    user1_rel = relationship("User", foreign_keys=[user1])
    user2_rel = relationship("User", foreign_keys=[user2])

class User(Base):
    __tablename__ = "user"
    
    username = Column(String, primary_key=True)
    password = Column(String)
    public_key = Column(Text)  # New field to store the public key
    
    # Define a relationship with Friendship table
    friends = relationship("Friendship", foreign_keys=[Friendship.user1], back_populates="user1_rel")
    friends_with = relationship("Friendship", foreign_keys=[Friendship.user2], back_populates="user2_rel")
    

# stateful counter used to generate the room id
class Counter():
    def __init__(self):
        self.counter = 0
    
    def get(self):
        self.counter += 1
        return self.counter

# Room class, used to keep track of which username is in which room
class Room():
    def __init__(self):
        self.counter = Counter()
        # dictionary that maps the username to the room id
        # for example self.dict["John"] -> gives you the room id of 
        # the room where John is in
        self.dict: Dict[str, int] = {}

    def create_room(self, sender: str, receiver: str) -> int:
        room_id = self.counter.get()
        self.dict[sender] = room_id
        self.dict[receiver] = room_id
        return room_id
    
    def join_room(self,  sender: str, room_id: int) -> int:
        self.dict[sender] = room_id

    def leave_room(self, user):
        if user not in self.dict.keys():
            return
        del self.dict[user]

    # gets the room id from a user
    def get_room_id(self, user: str):
        if user not in self.dict.keys():
            return None
        return self.dict[user]
    
class Message(Base):
    __tablename__ = 'message'
    id = Column(String, primary_key=True)
    sender_username = Column(String, ForeignKey('user.username'))
    recipient_username = Column(String, ForeignKey('user.username'))
    encrypted_message = Column(Text)  # Stores the encrypted message content
    hmac = Column(String)  # Stores the HMAC of the encrypted message

    sender = relationship("User", foreign_keys=[sender_username])
    recipient = relationship("User", foreign_keys=[recipient_username])
   