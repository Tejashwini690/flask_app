from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import sqlite3
from pydantic import BaseModel
import tweepy

app = FastAPI()

# JWT Configurations
SECRET_KEY = "secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Database Connection
def connect_db():
    conn = sqlite3.connect('mydatabase.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS users
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            password TEXT);''')
    conn.execute('''CREATE TABLE IF NOT EXISTS twitter_profiles
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            bearer_token TEXT,
            consumer_key TEXT,
            consumer_secret TEXT,
            access_token TEXT,
            access_token_secret TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id));''')
    conn.execute('''CREATE TABLE IF NOT EXISTS twitter_followers
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            follower_id TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id));''')
    return conn


# User Model
class User(BaseModel):
    email: str
    password: str


# User Table in DB
class UserTable:
    def __init__(self, conn):
        self.conn = conn

    def create(self, email: str, password: str):
        password_hash = pwd_context.hash(password)
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password_hash))
            self.conn.commit()
            user_id = cursor.lastrowid
            cursor.close()
            return user_id
        except sqlite3.Error as error:
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {error}")

    def get_by_email(self, email: str):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            cursor.close()
            if row is None:
                return None
            user_id, email, password_hash = row
            return {"user_id": user_id, "email": email, "password_hash": password_hash}
        except sqlite3.Error as error:
            raise HTTPException(status_code=500, detail=f"Internal Server Error: {error}")


# Twitter Profile Model
class TwitterProfile(BaseModel):
    bearer_token: str
    consumer_key: str
    consumer_secret: str
    access_token: str
    access_token_secret: str


# Twitter Profile Table in DB
class TwitterProfileTable:
    def __init__(self, conn):
        self.conn = conn

    def create(self, user_id: int, bearer_token: str, consumer_key: str, consumer_secret: str,
               access_token: str, access_token_secret: str):
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO twitter_profiles (user_id, bearer_token, consumer_key, consumer_secret, access_token, access_token_secret) VALUES (?, ?, ?, ?, ?, ?)",
                           (user_id, bearer_token, consumer_key, consumer_secret, access_token, access_token_secret))
            self.conn.commit()
            cursor.close()
        except sqlite3.Error as error:
            raise HTTPException(status_code)

