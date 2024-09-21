from flask import Flask, request,jsonify
import base64
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import logging
import regex as re
from datetime import datetime, timedelta
import requests
from database import insert_email_data, create_database 
from flask_cors import CORS
from predict import predict_email_read

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
CORS(app)

creds = Credentials.from_authorized_user_file('../config/token.json', ['https://www.googleapis.com/auth/gmail.readonly'])
gmail_service = build('gmail', 'v1', credentials=creds)

# Dictionary to store recently processed message IDs
recently_processed = {}

@app.route('/webhook', methods=['POST'])
def webhook():
    notification = request.get_json()
    message_data = base64.b64decode(notification['message']['data']).decode('utf-8')
    message_json = json.loads(message_data)
    
    logging.info(f"Received notification: {message_json}")
    
    if 'emailAddress' in message_json:
        results = gmail_service.users().messages().list(userId='me', maxResults=1).execute()
        messages = results.get('messages', [])
        
        if messages:
            latest_message_id = messages[0]['id']
            if is_update_category(latest_message_id) and not is_recently_processed(latest_message_id):
                process_email(latest_message_id)
            else:
                logging.info(f"Message {latest_message_id} is either not in the Updates category or was recently processed. Skipping.")
    
    return '', 204  # Acknowledge receipt of the message

def is_update_category(msg_id):
    try:
        message = gmail_service.users().messages().get(userId='me', id=msg_id, format='minimal').execute()
        labels = message.get('labelIds', [])
        return 'CATEGORY_UPDATES' in labels
    except Exception as e:
        logging.error(f"Error checking category for message {msg_id}: {e}")
        return False

def is_recently_processed(msg_id):
    current_time = datetime.now()
    if msg_id in recently_processed:
        if current_time - recently_processed[msg_id] < timedelta(minutes=2):
            return True
    recently_processed[msg_id] = current_time
    return False

def process_email(msg_id):
    try:
        message = gmail_service.users().messages().get(userId='me', id=msg_id, format='full').execute()
        headers = message['payload']['headers']
        
        subject = next((header['value'] for header in headers if header['name'].lower() == 'subject'), 'No subject')
        sender = next((header['value'] for header in headers if header['name'].lower() == 'from'), 'Unknown sender')
        
        # Extract the body
        body = get_email_body(message)
        clean_body = clean_text(body)
        
        # prediction = predict(subject, clean_body, sender)
        
        prediction = predict_email_read(sender, subject, clean_body)
        
        logging.info(f"New Update Email - Message ID: {msg_id}")
        logging.info(f"From: {sender}")
        logging.info(f"Subject: {subject}")
        logging.info(f"Cleaned Body: {clean_body[:500]}...")  # Log first 500 characters of cleaned body
        logging.info(f"Prediction: {prediction}")
        
        conn = create_database()
        insert_email_data(conn, msg_id, sender, subject, clean_body, prediction)
                
    except Exception as e:
        logging.error(f"Error processing email {msg_id}: {e}")

@app.route('/get-recent-predictions', methods=['GET'])
def get_recent_predictions():
    conn = create_database()
    cursor = conn.cursor()
    cursor.execute("SELECT prediction FROM EmailData ORDER BY ROWID DESC LIMIT 50")
    predictions = cursor.fetchall()
    # print(predictions)
    conn.close()
    # Convert the list of tuples to a list of floats
    prediction_values = [float(p[0]) for p in predictions]
    
    return jsonify(prediction_values)

    
def get_email_body(message):
    if 'parts' in message['payload']:
        for part in message['payload']['parts']:
            if part['mimeType'] == 'text/plain':
                return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
    elif 'body' in message['payload']:
        return base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')
    return "No body found"

def clean_text(text):
    # Remove links and images using regex
    text = re.sub(r'http[s]?://\S+', '', text)  # Remove URLs
    text = re.sub(r'<img[^>]*>', '', text)  # Remove image tags
    return text.strip()


if __name__ == '__main__':
    app.run(port=5002)