from flask import Flask, request, jsonify
from flask_cors import CORS
import MySQLdb
import smtplib
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


# Send email via Gmail
def send_email(name, email, phone, subject, message):
    sender = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    receiver = os.getenv("EMAIL_USER")

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = f"New Contact Message from {name}"

    body = f"""
    Name: {name}
    Email: {email}
    Phone: {phone}
    Subject: {subject}

    Message:
    {message}
    """
    msg.attach(MIMEText(body, "plain"))

    try:
        smtp_host = os.getenv("EMAIL_HOST")
        smtp_port = int(os.getenv("EMAIL_PORT"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)

        print("✅ Email sent successfully")

    except Exception as e:
        print("❌ Email error:", e)


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
