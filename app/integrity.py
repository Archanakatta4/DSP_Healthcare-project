import hashlib
import mysql



def calculate_row_hash(row):
    """
    Calculate the hash for a single row of data.
    """
    # Join all values of the record dictionary into a single string
    data_string = "|".join(map(str, row.values()))
    return hashlib.sha256(data_string.encode()).hexdigest()


def verify_row_integrity(row, stored_hash):
    """
    Verify the integrity of a single row using its stored hash.
    """
    return calculate_row_hash(row) == stored_hash

def calculate_query_hash(query_result):
    """
    Calculate a hash for the entire query result to ensure completeness.
    """
    combined_string = "".join([str(row) for row in query_result])
    return hashlib.sha256(combined_string.encode()).hexdigest()

def verify_query_integrity(query_result, expected_hash):
    """
    Verify the integrity of the query result by comparing its hash.
    """
    return calculate_query_hash(query_result) == expected_hash


def backfill_hashes():
    """
    Backfill hash values for existing records in the healthcare_info table.
    """
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
            # Remove `id` and `hash` from the record for hash calculation
            record_data = {
                "first_name": record["first_name"],
                "last_name": record["last_name"],
                "gender": record["gender"],
                "age": record["age"],
                "weight": record["weight"],
                "height": record["height"],
                "health_history": record["health_history"]
            }
            # Calculate hash
            row_hash = calculate_row_hash(record_data)

            # Update the hash column in the database
            update_query = "UPDATE healthcare_info SET hash = %s WHERE id = %s"
            cursor.execute(update_query, (row_hash, record["id"]))

        conn.commit()
        print("Backfill completed successfully!")
    except Exception as e:
        print(f"Error during backfill: {e}")
    finally:
        if conn.is_connected():
            conn.close()