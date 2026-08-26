from database import get_connection  
import sqlite3
import hashlib  

class UserManager:     
    def secure_password(self, password):
        hashed = hashlib.sha256(password.encode()).hexdigest()
        return hashed
    
    def check_username(self, username):
        username = username.lower().strip()

        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT id FROM users WHERE username = ?",
                (username,)
            )

            user = cursor.fetchone()

            return user is not None

        finally:
            conn.close()
    
    def register_user(self, username, password):

        username = username.lower().strip()

        if not username:
            return False, "Username cannot be empty"

        if len(password) < 6:
            return False, "Password must be at least 6 characters long"

        hashed_password = self.secure_password(password)

        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, hashed_password)
            )

            conn.commit()

            return True, f"Account created successfully! Welcome, {username}!"

        except sqlite3.IntegrityError:
            return False, "Username already exists"

        finally:
            conn.close()
    
    def login_user(self, username, password):

        if not username or not password:
            return False, "Please enter both username and password"

        username = username.lower().strip()
        hashed_password = self.secure_password(password)

        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT password FROM users WHERE username = ?",
                (username,)
            )

            user = cursor.fetchone()

            if user is None:
                return False, "Invalid username or password"

            stored_password = user[0]

            if stored_password == hashed_password:
                return True, f"Welcome back, {username}!"

            return False, "Invalid username or password"

        finally:
            conn.close()
