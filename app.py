from flask import Flask, request, jsonify
from flask_cors import CORS
import MySQLdb
import os
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# -------------------------------
# 🔗 DATABASE CONNECTION
# -------------------------------
def get_db_connection():
    try:
        conn = MySQLdb.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            passwd=os.getenv("DB_PASS"),
            db=os.getenv("DB_NAME"),
            charset="utf8mb4"
        )
        print("✅ DB Connected")
        return conn
    except Exception as e:
        print("❌ DB Connection Error:", e)
        return None


# -------------------------------
# 📧 SEND EMAIL VIA BREVO
# -------------------------------
def send_email(name, email, phone, subject, message):
    try:
        url = "https://api.brevo.com/v3/smtp/email"
        api_key = os.getenv("BREVO_API_KEY")

        payload = {
            "sender": {"email": os.getenv("EMAIL_USER"), "name": "Codechype"},
            "to": [{"email": os.getenv("EMAIL_USER")}],
            "subject": f"New Contact Message – {name}",
            "htmlContent": f"""
                <h2>New Contact Message</h2>
                <p><b>Name:</b> {name}</p>
                <p><b>Email:</b> {email}</p>
                <p><b>Phone:</b> {phone}</p>
                <p><b>Subject:</b> {subject}</p>
                <p><b>Message:</b> {message}</p>
            """
        }

        headers = {
            "accept": "application/json",
            "api-key": api_key,
            "content-type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)
        print("📧 Brevo Response:", response.status_code, response.text)

    except Exception as e:
        print("❌ Email Error:", e)


# -------------------------------
# 📮 SAVE CONTACT FORM MESSAGE
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
        sql = """INSERT INTO contact_messages (name, email, phone, subject, message)
                 VALUES (%s, %s, %s, %s, %s)"""
        cur.execute(sql, (name, email, phone, subject, message))
        conn.commit()
        cur.close()
        conn.close()

        print("✅ Message Saved")

        send_email(name, email, phone, subject, message)

        return jsonify({"success": True, "message": "Message sent successfully!"})

    except Exception as e:
        print("❌ DB Insert Error:", e)
        return jsonify({"success": False, "message": "Server error"}), 500


# -------------------------------
# 📥 FETCH ALL CONTACT MESSAGES
# -------------------------------
@app.route("/api/messages", methods=["GET"])
def get_messages():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"success": False, "message": "DB not connected"}), 500

    try:
        cur = conn.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM contact_messages ORDER BY id DESC")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        return jsonify(rows)

    except Exception as e:
        print("❌ Fetch Error:", e)
        return jsonify({"success": False, "message": "Server error"}), 500


# -------------------------------
# 🗑️ DELETE A MESSAGE
# -------------------------------
@app.route("/api/messages/<int:msg_id>", methods=["DELETE"])
def delete_message(msg_id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"success": False, "message": "DB not connected"}), 500

    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM contact_messages WHERE id = %s", (msg_id,))
        conn.commit()
        cur.close()
        conn.close()

        print(f"🗑️ Deleted message {msg_id}")

        return jsonify({"success": True, "message": "Message deleted successfully"})

    except Exception as e:
        print("❌ Delete Error:", e)
        return jsonify({"success": False, "message": "Delete failed"}), 500


# ----------------------------------------------------
# ❗ IMPORTANT: DO NOT USE app.run() ON RENDER
# Gunicorn will run automatically
# ----------------------------------------------------
