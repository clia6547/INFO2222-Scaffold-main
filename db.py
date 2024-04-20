'''
db
database file, containing all the logic to interface with the sql database
'''

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import *
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

from pathlib import Path

# creates the database directory
Path("database") \
    .mkdir(exist_ok=True)

# "database/main.db" specifies the database file
# change it if you wish
# turn echo = True to display the sql output
engine = create_engine("sqlite:///database/main.db", echo=False)
session = Session(bind=engine)

# initializes the database
Base.metadata.create_all(engine)

# inserts a user to the database
def insert_user(username: str, password: str, salt: str, public_key: str):
    with Session(engine) as session:
        print(f"Inserting user {username} with public key: {public_key}")
        user = User(username=username, password=password, salt=salt, public_key=public_key)
        session.add(user)
        try:
            session.commit()
            print(f"User {username} inserted successfully.")
        except Exception as e:
            print(f"Failed to insert user: {e}")
            # session.rollback()

# gets a user from the database
def get_user(username: str):
    with Session(engine) as session:
        return session.get(User, username)
    
# inserts a friendship into the database
def insert_friendship(username1: str, username2: str):
    with Session(engine) as session:
        friendship = Friendship(user1=username1, user2=username2)
        session.add(friendship)
        session.commit()

# gets friends of a user from the database
def get_friends(username: str):
    with Session(engine) as session:
        user = session.query(User).filter(User.username == username).first()
        if user:
            # Assuming User.friends_with represents the list of friends for a user
            return [friendship.user1 for friendship in user.friends_with]
        return None

def generate_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return private_key, public_key.decode('utf-8')

def get_user_public_key(username):
    user = session.query(User).filter_by(username=username).first()
    if user:
        print(f"Public Key for {username}: {user.public_key}")  # Log the public key
        return user.public_key
    else:
        print(f"User not found: {username}")  # Log an error message if user not found
        return None


def get_user_private_key(username):  # Highly insecure to use in real applications
    user = session.query(User).filter_by(username=username).first()
    return user.private_key if user else None  # Assumes private keys are stored, which should NOT be done