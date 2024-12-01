import mysql.connector
import bcrypt

def setup_database():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="admin",
            password="Anvitha@4"
        )
        cursor = conn.cursor()
        print("Connected to MySQL successfully.")

        # Create database
        cursor.execute("CREATE DATABASE IF NOT EXISTS healthcare_db")
        cursor.execute("USE healthcare_db")
        print("Database selected/created successfully.")

        # Create healthcare_info table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS healthcare_info (
                id INT PRIMARY KEY AUTO_INCREMENT,
                first_name VARCHAR(50),
                last_name VARCHAR(50),
                gender BOOLEAN,
                age INT,
                weight FLOAT,
                height FLOAT,
                health_history TEXT
            )
        ''')
        print("Table `healthcare_info` created successfully.")

        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INT PRIMARY KEY AUTO_INCREMENT,
                username VARCHAR(50) UNIQUE,
                password_hash VARCHAR(255),
                user_group ENUM('H', 'R')
            )
        ''')
        print("Table `users` created successfully.")

        # Insert default users
        admin_password = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt())
        user_password = bcrypt.hashpw("user123".encode(), bcrypt.gensalt())
        cursor.execute("INSERT IGNORE INTO users (username, password_hash, user_group) VALUES (%s, %s, %s)",
                       ("admin_h", admin_password.decode(), "H"))
        cursor.execute("INSERT IGNORE INTO users (username, password_hash, user_group) VALUES (%s, %s, %s)",
                       ("user_r", user_password.decode(), "R"))

        conn.commit()
        print("Default users inserted successfully.")

        print("Database setup completed.")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        conn.close()
        print("Connection closed.")

if __name__ == "__main__":
    setup_database()
