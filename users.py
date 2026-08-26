from database import get_connection
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
import sqlite3
import hashlib

class UserManager:     
    password_hasher = PasswordHasher()
    def hash_password(self, password):
        return self.password_hasher.hash(password)

    def verify_password(self, stored_password, password):
        # New Argon2 passwords
        if stored_password.startswith("$argon2"):
            try:
                self.password_hasher.verify(stored_password, password)

                if self.password_hasher.check_needs_rehash(stored_password):
                    return True, self.hash_password(password)

                return True, None

            except (VerifyMismatchError, InvalidHashError):
                return False, None

        # Legacy SHA-256 password
        legacy_hash = hashlib.sha256(password.encode()).hexdigest()

        if stored_password == legacy_hash:
            # Correct old password: upgrade it to Argon2
            return True, self.hash_password(password)

        return False, None
    
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

        hashed_password = self.hash_password(password)

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

        conn = get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT id, password
                FROM users
                WHERE username = ?
                """,
                (username,)
            )

            user = cursor.fetchone()

            if user is None:
                return False, "Invalid username or password"

            user_id = user[0]
            stored_password = user[1]

            password_valid, upgraded_hash = self.verify_password(
                stored_password,
                password
            )

            if not password_valid:
                return False, "Invalid username or password"

            # Automatically upgrade legacy SHA-256 passwords
            if upgraded_hash is not None:
                cursor.execute(
                    """
                    UPDATE users
                    SET password = ?
                    WHERE id = ?
                    """,
                    (upgraded_hash, user_id)
                )

                conn.commit()

            return True, f"Welcome back, {username}!"

        finally:
            conn.close()
