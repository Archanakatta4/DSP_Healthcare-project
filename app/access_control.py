import hashlib
from cryptography.fernet import Fernet
import mysql.connector
import logging
import os
from dotenv import load_dotenv



# Load environment variables from .env file
load_dotenv()

# Get the FERNET_KEY
key = os.getenv("FERNET_KEY")
print(f"Loaded FERNET_KEY: {key}")

# Get the FERNET_KEY
key = os.getenv("FERNET_KEY")
if not key:
    raise ValueError("FERNET_KEY environment variable is not set.")
cipher = Fernet(key.encode())



def encrypt_field(value):
    return cipher.encrypt(str(value).encode()).decode()


def decrypt_field(encrypted_value):
    """
    Decrypts a single value using Fernet symmetric encryption.
    """
    return cipher.decrypt(encrypted_value.encode()).decode()


def calculate_hash(record):
    """
    Calculates a SHA-256 hash for a record.
    The hash excludes the 'hash' field itself.
    """
    record_string = f"{record['first_name']}|{record['last_name']}|{record['gender']}|{record['age']}|{record['weight']}|{record['height']}|{record['health_history']}"
    return hashlib.sha256(record_string.encode()).hexdigest()


def update_records_with_encryption_and_hash():
    """Encrypt sensitive fields and update records with a hash."""
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="admin",
            password="Anvitha@4",
            database="healthcare_db"
        )
        cursor = conn.cursor(dictionary=True)

        # Fetch all records
        cursor.execute("SELECT * FROM healthcare_info")
        records = cursor.fetchall()

        for record in records:
            try:
                # Encrypt sensitive fields
                encrypted_gender = encrypt_field(record['gender'])
                encrypted_age = encrypt_field(record['age'])

                # Calculate hash for the updated record
                record_hash = calculate_hash({
                    'first_name': record['first_name'],
                    'last_name': record['last_name'],
                    'gender': encrypted_gender,
                    'age': encrypted_age,
                    'weight': record['weight'],
                    'height': record['height'],
                    'health_history': record['health_history']
                })

                # Update the database
                update_query = """
                    UPDATE healthcare_info
                    SET gender = %s, age = %s, hash = %s
                    WHERE id = %s
                """
                cursor.execute(update_query, (encrypted_gender, encrypted_age, record_hash, record['id']))
            except Exception as e:
                logging.error(f"Error encrypting record ID {record['id']}: {e}")
                raise

        conn.commit()
        logging.info("Records updated successfully with encryption and hash.")
    except Exception as e:
        logging.error(f"Error updating records: {e}")
        raise
    finally:
        if conn.is_connected():
            conn.close()


def query_records_with_decryption(user_role):
    """
    Fetch records and decrypt sensitive fields for display.
    """
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="admin",
            password="Anvitha@4",
            database="healthcare_db"
        )
        cursor = conn.cursor(dictionary=True)

        # Query records based on user role
        if user_role == 'H':
            query = "SELECT id, first_name, last_name, gender, age, weight, height, health_history FROM healthcare_info"
        elif user_role == 'R':
            query = "SELECT id, gender, age, weight, height, health_history FROM healthcare_info"
        else:
            raise ValueError("Invalid user role")

        cursor.execute(query)
        records = cursor.fetchall()

        # Decrypt sensitive fields
        for record in records:
            record['gender'] = record['gender']
            record['age'] = record['age']

        print(f"Fetched Records: {records}")  # Debugging
        return records
    except Exception as e:
        logging.error(f"Error querying records: {e}")
        raise
    finally:
        if conn.is_connected():
            conn.close()


def encrypt_existing_records():
    """Encrypt existing records and update their hash."""
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="admin",
            password="Anvitha@4",
            database="healthcare_db"
        )
        cursor = conn.cursor(dictionary=True)

        # Fetch all records
        cursor.execute("SELECT * FROM healthcare_info")
        records = cursor.fetchall()

        for record in records:
            encrypted_gender = encrypt_field(record['gender'])
            encrypted_age = encrypt_field(record['age'])

            # Calculate the hash
            record_hash = calculate_hash({
                'first_name': record['first_name'],
                'last_name': record['last_name'],
                'gender': encrypted_gender,
                'age': encrypted_age,
                'weight': record['weight'],
                'height': record['height'],
                'health_history': record['health_history']
            })

            # Update the database
            cursor.execute("""
                UPDATE healthcare_info
                SET gender = %s, age = %s, hash = %s
                WHERE id = %s
            """, (encrypted_gender, encrypted_age, record_hash, record['id']))

        conn.commit()
        print("Records updated successfully.")
    except Exception as e:
        print(f"Error encrypting records: {e}")
    finally:
        if conn.is_connected():
            conn.close()




# Query data with checksum
def query_data_with_checksum(user_role):
    try:
        # Establish database connection
        conn = mysql.connector.connect(
            host="localhost",
            user="admin",
            password="Anvitha@4",
            database="healthcare_db"
        )
        cursor = conn.cursor(dictionary=True)

        # Adjust query based on user role
        if user_role == 'H':  # Admins see all fields
            query = "SELECT * FROM healthcare_info ORDER BY id DESC LIMIT 100"
        elif user_role == 'R':  # Restricted users see selected fields
            query = """
                SELECT gender, age, weight, height, health_history 
                FROM healthcare_info 
                ORDER BY id DESC LIMIT 100
            """
        else:
            raise ValueError("Invalid user role")

        # Execute the query
        cursor.execute(query)
        records = cursor.fetchall()

        # Check if records exist
        if not records:
            logging.warning("No records found for the user role.")
            return [], None

        # Decrypt sensitive fields
        for record in records:
            try:
                if 'gender' in record:
                    record['gender'] = decrypt_field(record['gender'])
                if 'age' in record:
                    record['age'] = decrypt_field(record['age'])
            except Exception as e:
                logging.error(f"Error decrypting record: {e}")
                raise

        # Calculate checksum for the records
        checksum = hashlib.sha256("".join([str(record.get('gender', '')) for record in records]).encode()).hexdigest()

        logging.debug(f"Fetched records: {records}")
        logging.debug(f"Checksum: {checksum}")

        return records, checksum
    except Exception as e:
        logging.error(f"Error in query_data_with_checksum: {e}")
        raise
    finally:
        if conn.is_connected():
            conn.close()



# Delete a record
def delete_record(record_id):
    """
    Delete a specific record by ID.
    """
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="admin",
            password="Anvitha@4",
            database="healthcare_db"
        )
        cursor = conn.cursor()
        query = "DELETE FROM healthcare_info WHERE id = %s"
        cursor.execute(query, (record_id,))
        conn.commit()
        return True  # Success
    except Exception as e:
        logging.error(f"Error deleting record with ID {record_id}: {e}")
        return False
    finally:
        if conn.is_connected():
            conn.close()


if __name__ == "__main__":
    update_records_with_encryption_and_hash()
