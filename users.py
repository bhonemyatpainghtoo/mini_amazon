from database import get_connection
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
import sqlite3
import hashlib


class UserManager:
    # One shared hasher object reused for every password. Argon2
    # turns a password into a scrambled string you can never
    # reverse back into the original — you can only check whether
    # a *new* password produces the same scrambled result.
    password_hasher = PasswordHasher()

    def hash_password(self, password):
        return self.password_hasher.hash(password)

    def verify_password(self, stored_password, password):
        """
        Checks a typed-in password against what's stored.
        Returns (is_correct, upgraded_hash_or_None).

        This also handles accounts created before Argon2 was
        added: if the stored password is an old SHA-256 hash
        and it still matches, we quietly re-hash it with Argon2
        so that account gets upgraded the next time its owner
        logs in — no forced password reset needed.
        """
        # New-style Argon2 passwords all start with this prefix.
        if stored_password.startswith("$argon2"):
            try:
                self.password_hasher.verify(stored_password, password)

                # Argon2's recommended settings occasionally change;
                # this re-hashes with the current settings if needed.
                if self.password_hasher.check_needs_rehash(stored_password):
                    return True, self.hash_password(password)

                return True, None

            except (VerifyMismatchError, InvalidHashError):
                return False, None

        # Legacy SHA-256 password (from before this app used Argon2)
        legacy_hash = hashlib.sha256(password.encode()).hexdigest()

        if stored_password == legacy_hash:
            # Correct old password: upgrade it to Argon2 now
            return True, self.hash_password(password)

        return False, None

    def check_username(self, username):
        username = username.lower().strip()

        conn = get_connection()
        cursor = conn.cursor()

        try:
            # The "?" here is a placeholder, not a plain text
            # insert. SQLite fills it in safely, which is what
            # protects this from SQL injection — a typed-in
            # username can never be treated as part of the command.
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

        # A slightly stronger rule than "6 characters, anything
        # goes": require a bit more length and at least one digit.
        # any(...) checks each character one by one and returns
        # True as soon as it finds a digit.
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"

        if not any(char.isdigit() for char in password):
            return False, "Password must contain at least one number"

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
            # This fires if the username already exists (the
            # UNIQUE rule on that column in the database rejected it).
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
                # Deliberately the same message as "wrong password"
                # below — this stops someone from being able to
                # figure out which usernames exist just by testing
                # logins.
                return False, "Invalid username or password"

            user_id = user[0]
            stored_password = user[1]

            password_valid, upgraded_hash = self.verify_password(
                stored_password,
                password
            )

            if not password_valid:
                return False, "Invalid username or password"

            # If verify_password() gave us back a freshly-hashed
            # version (upgrading from legacy SHA-256, or refreshing
            # Argon2 settings), save it now.
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