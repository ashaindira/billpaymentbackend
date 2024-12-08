from flask import Flask, request, jsonify,render_template
import sqlite3
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from twilio.rest import Client
import os


app = Flask(__name__)


@app.route('/')
def home():
    
    return render_template('index.html')  # Render the frontend HTML file


# Use PORT environment variable provided by Render
port = int(os.environ.get("PORT", 5000))

# Ensure app listens on 0.0.0.0 to be accessible from outside
app.run(host='0.0.0.0', port=port)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bills.db'
db = SQLAlchemy(app)

class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bill_name = db.Column(db.String(100), nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    notification_sent = db.Column(db.Boolean, default=False)


# Initialize database
def init_db():
    conn = sqlite3.connect('bills.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            due_date TEXT NOT NULL,
            category TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/add-bill', methods=['POST'])
def add_bill():
    data = request.json
    name = data['billName']
    due_date = data['dueDate']
    category = data['category']

    conn = sqlite3.connect('bills.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO bills (name, due_date, category) VALUES (?, ?, ?)',
                   (name, due_date, category))
    conn.commit()
    bill_id = cursor.lastrowid
    conn.close()

    return jsonify({'id': bill_id, 'name': name, 'dueDate': due_date, 'category': category})

@app.route('/get-reminders', methods=['GET'])
def get_reminders():
    # Connect to the database
    conn = sqlite3.connect('bills.db')
    cursor = conn.cursor()

    # Fetch all bills from the database
    cursor.execute('SELECT * FROM bills')
    bills = cursor.fetchall()

    # Prepare reminders for bills due in 3 days or less
    reminders = []
    for bill in bills:
        bill_id, name, due_date, category = bill
        days_remaining = (datetime.strptime(due_date, '%Y-%m-%d') - datetime.now()).days
        if days_remaining <= 3:  # Bills due in 3 days or less
            reminders.append({
                'id': bill_id,
                'name': name,
                'category': category,
                'daysRemaining': days_remaining
            })

    # Close the database connection
    conn.close()

    # Return the reminders as JSON
    return jsonify(reminders)



def check_due_dates():
    upcoming_bills = Bill.query.filter(
        Bill.due_date <= datetime.now() + timedelta(days=2),  # Bills due within 2 days
        Bill.notification_sent == False
    ).all()

    for bill in upcoming_bills:
        send_notification(bill)
        bill.notification_sent = True
        db.session.commit()

scheduler = BackgroundScheduler()
scheduler.add_job(func=check_due_dates, trigger="interval", hours=1)
scheduler.start()

@app.route('/get-due-reminders', methods=['GET'])
def get_due_reminders():
    conn = sqlite3.connect('bills.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM bills')
    bills = cursor.fetchall()

    reminders = []
    for bill in bills:
        bill_id, name, due_date, category = bill
        days_remaining = (datetime.strptime(due_date, '%Y-%m-%d') - datetime.now()).days
        if days_remaining <= 3:
            reminders.append({
                'id': bill_id,
                'name': name,
                'category': category,
                'daysRemaining': days_remaining
            })

    conn.close()
    return jsonify(reminders)


def send_notification(bill):
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        body=f"Reminder: Your bill '{bill.bill_name}' is due on {bill.due_date}.",
        from_='+1234567890',  # Twilio phone number
        to='+0987654321'
    )


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
