import bcrypt
import mysql.connector
import logging

def register_user(username, password, user_group):
    """
    Register a new user with a hashed password and a user group (H or R).
    """
    conn = mysql.connector.connect(
        host="localhost",
        user="admin",
        password="Anvitha@4",
        database="healthcare_db"
    )
    cursor = conn.cursor()
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    print(hashed_password.decode())
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash, user_group) VALUES (%s, %s, %s)",
            (username, hashed_password.decode(), user_group)
        )
        conn.commit()
        print(f"User {username} registered successfully!")
    except mysql.connector.Error as e:
        print(f"Error registering user: {e}")
    finally:
        conn.close()



def authenticate_user(username, password):
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="admin",
            password="Anvitha@4",
            database="healthcare_db"
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        logging.info(f"User found: {user}")

        if user and bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
            return True
        return False
    except Exception as e:
        logging.error(f"Error during authentication: {e}")
        raise
    finally:
        conn.close()