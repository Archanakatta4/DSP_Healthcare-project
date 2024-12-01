from flask import Flask, request, jsonify, session, render_template, redirect, url_for, flash
import logging
import mysql.connector
from app.access_control import (
    delete_record,
    query_data_with_checksum,
)
from app.authentication import authenticate_user
from app.integrity import calculate_row_hash, backfill_hashes  # Import backfill_hashes
from app.data_insertion import encrypt_field

app = Flask(__name__)
app.secret_key = "3OtGvowzuC_zvLDJ2HNKCNUZXgE0ddjSW4wbQ7_FtlA="

# Configure logging
logging.basicConfig(level=logging.INFO)

# Home route
@app.route("/", methods=["GET"])
def home():
    return render_template("home.html")

# Health check route
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "OK"}), 200

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        try:
            if authenticate_user(username, password):
                session["username"] = username
                # Assign user roles correctly based on the username
                session["user_role"] = "H" if username.startswith("admin") else "R"
                flash("Login successful!", "success")
                return redirect(url_for("dashboard"))  # Redirect after login
            else:
                flash("Invalid username or password!", "danger")
        except Exception as e:
            logging.error(f"Error during login: {e}")
            flash("An unexpected error occurred. Please try again later.", "danger")

    return render_template("login.html")


@app.route("/dashboard", methods=["GET"])
def dashboard():
    if "username" not in session:
        flash("You must log in first.", "danger")
        return redirect(url_for("login"))

    try:
        data, checksum = query_data_with_checksum(session['user_role'])
        return render_template("dashboard.html", data=data, checksum=checksum, group=session['user_role'])

    except Exception as e:
        logging.error(f"Error loading dashboard: {e}")
        flash("An error occurred while loading the dashboard.", "danger")
        return redirect(url_for("login"))


# Add data route
@app.route("/add", methods=["GET", "POST"])
def add():
    if "username" not in session or session["user_role"] != "H":  # Only admins can add data
        flash("You do not have permission to add data.", "danger")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        try:
            # Collect form data
            first_name = request.form["first_name"]
            last_name = request.form["last_name"]
            gender = encrypt_field(request.form["gender"])  # Encrypt sensitive fields
            age = encrypt_field(request.form["age"])  # Encrypt sensitive fields
            weight = float(request.form["weight"])
            height = float(request.form["height"])
            health_history = request.form["health_history"]

            # Calculate the hash
            record = {
                "first_name": first_name,
                "last_name": last_name,
                "gender": gender,
                "age": age,
                "weight": weight,
                "height": height,
                "health_history": health_history
            }
            row_hash = calculate_row_hash(record)

            # Insert the data into the database
            conn = mysql.connector.connect(
                host="localhost",
                user="admin",
                password="Anvitha@4",
                database="healthcare_db"
            )
            cursor = conn.cursor()
            query = """
                INSERT INTO healthcare_info (first_name, last_name, gender, age, weight, height, health_history, hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (first_name, last_name, gender, age, weight, height, health_history, row_hash))
            conn.commit()
            conn.close()

            logging.info("Data added successfully!")
            flash("Data added successfully!", "success")
            return redirect(url_for("dashboard"))
        except Exception as e:
            logging.error(f"Error adding data: {e}")
            flash("Error adding data. Please try again.", "danger")

    return render_template("add.html")

# Add a route to trigger the backfill process
@app.route("/backfill_hashes", methods=["GET"])
def trigger_backfill_hashes():
    try:
        backfill_hashes()
        flash("Hashes have been backfilled successfully!", "success")
    except Exception as e:
        flash(f"Error during hash backfill: {e}", "danger")
    return redirect(url_for("dashboard"))




@app.route('/edit/<int:record_id>', methods=['GET', 'POST'])
def edit(record_id):
    if 'username' not in session or session['user_role'] != 'H':  # Ensure only admins can update
        flash("You do not have permission to update records.", "danger")
        return redirect(url_for('dashboard'))

    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="admin",
            password="Anvitha@4",
            database="healthcare_db"
        )
        cursor = conn.cursor(dictionary=True)

        if request.method == 'GET':
            # Fetch the record to pre-fill the form
            cursor.execute("SELECT * FROM healthcare_info WHERE id = %s", (record_id,))
            record = cursor.fetchone()
            if not record:
                flash(f"No record found with ID {record_id}.", "danger")
                return redirect(url_for('dashboard'))
            return render_template('edit.html', record=record)

        elif request.method == 'POST':
            # Collect data from the form
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            gender = encrypt_field(request.form['gender'])  # Encrypt gender
            age = encrypt_field(request.form['age'])  # Encrypt age
            weight = request.form['weight']
            height = request.form['height']
            health_history = request.form['health_history']

            # Update the record in the database
            query = """
                UPDATE healthcare_info
                SET first_name = %s, last_name = %s, gender = %s, age = %s,
                    weight = %s, height = %s, health_history = %s
                WHERE id = %s
            """
            cursor.execute(query, (first_name, last_name, gender, age, weight, height, health_history, record_id))
            conn.commit()

            flash(f"Record with ID {record_id} updated successfully!", "success")
            return redirect(url_for('dashboard'))

    except Exception as e:
        logging.error(f"Error updating record: {e}")
        flash("Error updating record. Please try again.", "danger")
        return redirect(url_for('dashboard'))
    finally:
        if conn.is_connected():
            conn.close()




@app.route('/delete/<int:record_id>', methods=['POST'])
def delete(record_id):
    if 'username' not in session or session['user_role'] != 'H':  # Ensure only admins can delete
        flash("You do not have permission to delete records.", "danger")
        return redirect(url_for('dashboard'))

    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="admin",
            password="Anvitha@4",
            database="healthcare_db"
        )
        cursor = conn.cursor()

        # Execute delete query
        query = "DELETE FROM healthcare_info WHERE id = %s"
        cursor.execute(query, (record_id,))
        conn.commit()

        if cursor.rowcount > 0:
            flash(f"Record with ID {record_id} has been deleted successfully!", "success")
        else:
            flash(f"No record found with ID {record_id}.", "danger")

    except Exception as e:
        logging.error(f"Error deleting record: {e}")
        flash("Error deleting record. Please try again.", "danger")
    finally:
        if conn.is_connected():
            conn.close()

    return redirect(url_for('dashboard'))



# Logout route
@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
