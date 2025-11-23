from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# -------------------------------
# PostgreSQL Connection
# -------------------------------
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv("PG_HOST"),
            database=os.getenv("PG_DBNAME"),
            user=os.getenv("PG_USER"),
            password=os.getenv("PG_PASSWORD"),
            port=os.getenv("PG_PORT"),
            sslmode="require"
        )
        print("✅ Connected to PostgreSQL successfully")
        return conn
    except Exception as e:
        print("❌ PostgreSQL Connection Error:", e)
        return None


# -------------------------------
# Brevo Email Sender
# -------------------------------
def send_email(name, email, phone, subject, message):
    url = "https://api.brevo.com/v3/smtp/email"
    api_key = os.getenv("BREVO_API_KEY")

    payload = {
        "sender": {
            "email": os.getenv("EMAIL_FROM"),
            "name": "Codechype"
        },
        "to": [
            {"email": os.getenv("EMAIL_TO")}
        ],
        "subject": f"New Contact Message From {name}",
        "htmlContent": f"""
            <h2>New Contact Form Message</h2>
            <p><strong>Name:</strong> {name}</p>
            <p><strong>Email:</strong> {email}</p>
            <p><strong>Phone:</strong> {phone}</p>
            <p><strong>Subject:</strong> {subject}</p>
            <p><strong>Message:</strong><br>{message}</p>
        """
    }

    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }

    res = requests.post(url, json=payload, headers=headers)
    print("📧 Brevo API Response:", res.status_code, res.text)


# -------------------------------
# SAVE CONTACT MESSAGE
# -------------------------------
@app.route("/api/contact", methods=["POST"])
def contact():
    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")
    subject = data.get("subject")
    message = data.get("message")

    if not all([name, email, phone, subject, message]):
        return jsonify({"success": False, "message": "All fields are required"}), 400

    conn = get_db_connection()
    if conn is None:
        return jsonify({"success": False, "message": "DB not connected"}), 500

    try:
        cur = conn.cursor()
        sql = """
            INSERT INTO contact_messages (name, email, phone, subject, message)
            VALUES (%s, %s, %s, %s, %s)
        """
        cur.execute(sql, (name, email, phone, subject, message))
        conn.commit()
        cur.close()
        conn.close()

        send_email(name, email, phone, subject, message)

        return jsonify({"success": True, "message": "Message sent successfully!"})

    except Exception as e:
        print("❌ Database error:", e)
        return jsonify({"success": False, "message": "Server error"}), 500


# -------------------------------
# FETCH ALL MESSAGES
# -------------------------------
@app.route("/api/messages", methods=["GET"])
def get_messages():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"success": False, "message": "DB not connected"}), 500

    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM contact_messages ORDER BY id DESC")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(rows)
    except Exception as e:
        print("❌ Fetch error:", e)
        return jsonify({"success": False, "message": "Server error"}), 500


# -------------------------------
# DELETE MESSAGE
# -------------------------------
@app.route("/api/messages/<int:id>", methods=["DELETE"])
def delete_msg(id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"success": False, "message": "DB not connected"}), 500

    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM contact_messages WHERE id=%s", (id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        print("❌ Delete error:", e)
        return jsonify({"success": False})

