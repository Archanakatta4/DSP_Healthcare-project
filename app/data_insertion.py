import random
import mysql.connector
from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv
import hashlib

# Load environment variables
load_dotenv()
key = os.getenv("FERNET_KEY")
if not key:
    raise ValueError("FERNET_KEY environment variable is not set.")
cipher = Fernet(key.encode())

# Encrypt a single field
def encrypt_field(value):
    return cipher.encrypt(str(value).encode()).decode()



# Calculate row hash
def calculate_row_hash(row):
    """
    Calculate a hash for a single row.
    """
    data_string = "|".join(map(str, row.values()))
    return hashlib.sha256(data_string.encode()).hexdigest()

def insert_sample_data():
    """
    Insert 100 sample records into the healthcare_info table with encrypted sensitive fields.
    """
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="admin",
            password="Anvitha@4",
            database="healthcare_db"
        )
        cursor = conn.cursor()

        # Sample realistic names
        first_names = [
            "John", "Jane", "Alice", "Bob", "Chris", "Diana", "Eve", "Frank",
            "Grace", "Henry", "Ivy", "Jack", "Kelly", "Liam", "Mia", "Noah",
            "Olivia", "Paul", "Quinn", "Rachel"
        ]
        last_names = [
            "Smith", "Johnson", "Brown", "Williams", "Jones", "Garcia", "Miller",
            "Davis", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson",
            "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee"
        ]

        # Generate 100 sample records with encrypted gender and age
        sample_data = []
        for _ in range(100):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            gender = encrypt_field(random.choice([0, 1]))  # 0 for Female, 1 for Male
            age = encrypt_field(random.randint(18, 80))
            weight = round(random.uniform(50.0, 120.0), 1)  # Weight in kg
            height = round(random.uniform(150.0, 200.0), 1)  # Height in cm
            health_history = random.choice(['No issues', 'Asthma', 'Diabetes', 'Hypertension', 'Allergies'])

            # Create a dictionary for the row
            row = {
                "first_name": first_name,
                "last_name": last_name,
                "gender": gender,
                "age": age,
                "weight": weight,
                "height": height,
                "health_history": health_history
            }
            # Calculate the hash for the row
            row_hash = calculate_row_hash(row)

            # Append the row as a tuple including the hash
            sample_data.append((first_name, last_name, gender, age, weight, height, health_history, row_hash))

        # Insert records
        query = """
            INSERT INTO healthcare_info (first_name, last_name, gender, age, weight, height, health_history, hash)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.executemany(query, sample_data)
        conn.commit()
        print(f"{cursor.rowcount} sample records inserted.")
    except Exception as e:
        print(f"Error inserting sample data: {e}")
    finally:
        if conn.is_connected():
            conn.close()


if __name__ == "__main__":
    insert_sample_data()


