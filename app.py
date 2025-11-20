from flask import Flask, request, jsonify
from flask_cors import CORS
import MySQLdb
import smtplib
import requests
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Database connection
def get_db_connection():
    try:
        conn = MySQLdb.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            passwd=os.getenv("DB_PASS"),
            db=os.getenv("DB_NAME"),
            charset="utf8mb4"
        )
        print("✅ Connected to MySQL successfully")
        return conn
    except Exception as e:
        print("❌ Database connection failed:", e)
        return None



def send_email(name, email, phone, subject, message):
    api_key = os.getenv("BREVO_API_KEY")
    receiver = os.getenv("EMAIL_TO")

    url = "https://api.brevo.com/v3/smtp/email"

    payload = {
        "sender": {"name": "Codecype Website", "email": receiver},
        "to": [{"email": receiver}],
        "subject": f"New Contact Message from {name}",
        "htmlContent": f"""
            <h3>New Contact Message</h3>
            <p><strong>Name:</strong> {name}</p>
            <p><strong>Email:</strong> {email}</p>
            <p><strong>Phone:</strong> {phone}</p>
            <p><strong>Subject:</strong> {subject}</p>
            <p><strong>Message:</strong><br>{message}</p>
        """
    }

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": api_key
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        print("📧 Brevo API Response:", response.status_code, response.text)
    except Exception as e:
        print("❌ Email Send Error:", e)



# Route to receive messages
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
        return jsonify({"success": False, "message": "Database not connected"}), 500

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
        print("✅ Message saved to database")

        send_email(name, email, phone, subject, message)
        return jsonify({"success": True, "message": "Message sent successfully!"})

    except Exception as e:
        print("❌ Database error:", e)
        return jsonify({"success": False, "message": "Server error occurred"}), 500


if __name__ == "__main__":
    print("🚀 Flask server starting...")
    print("Loaded ENV:", os.getenv("DB_NAME"), os.getenv("EMAIL_USER"))
    app.run(host="127.0.0.1", port=5000, debug=True)

