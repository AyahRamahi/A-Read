from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import os

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def create_users ():
    # create databse for users
    columns = """
        user_id SERIAL PRIMARY KEY,
        username VARCHAR UNIQUE,
        password VARCHAR
    """
    db.execute(f"CREATE TABLE IF NOT EXISTS users ({columns})")
    db.commit()

def create_reviews():
    # create database for book reviews
    columns = """
        id SERIAL PRIMARY KEY,
        book_id INTEGER,
        user_id INTEGER,
        review VARCHAR,
        rate INTEGER
    """
    db.execute(f"CREATE TABLE IF NOT EXISTS reviews ({columns})")
    db.commit()

def user_exist(usr):
    found_users = db.execute("SELECT * FROM users WHERE username = :username",{'username':usr}).fetchall()
    if found_users:
        return True
    return False


def signup_user(usr,pas):
    if user_exist(usr) :
        return False
    db.execute("INSERT INTO users (username,password) VALUES (:username,:password)",{'username':usr,'password':pas})
    db.commit()
    return True
    

def signin_user(usr,pas):
    found_user = db.execute("SELECT * FROM users WHERE username = :username",{'username':usr}).fetchone()
    print(found_user)
    if found_user[2] == pas :
        return found_user
    else :
        return False