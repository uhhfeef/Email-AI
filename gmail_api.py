import base64
from email.mime.text import MIMEText
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import os.path
from google.oauth2.credentials import Credentials
import regex as re
import sqlite3
import datetime
import requests
import json

# Define the scope for reading emails
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def create_database():
    conn = sqlite3.connect('emails.db')
    cursor = conn.cursor()
    # Create a table for storing email data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS EmailData (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT NOT NULL,
            sender TEXT NOT NULL,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            prediction INT NOT NULL
        )
    ''')
    conn.commit()
    return conn

def insert_email_data(conn, message_id, sender, subject, body, prediction):
    cursor = conn.cursor()
    cursor.execute('INSERT INTO EmailData (message_id, sender, subject, body, prediction) VALUES (?, ?, ?, ?, ?)', 
                   (message_id, sender, subject, body, prediction))
    conn.commit()


def clean_text(text):
    # Remove links and images using regex
    text = re.sub(r'http[s]?://\S+', '', text)  # Remove URLs
    text = re.sub(r'<img[^>]*>', '', text)  # Remove image tags
    return text.strip()

def predict(subject, body, sender):
    data = {
    "from_address": sender,
    "subject": subject,
    "body": body
    }
    url = "http://localhost:5001/predict"
    headers = {'Content-Type': 'application/json'}

    res = requests.post(url, data=json.dumps(data), headers=headers)
    return res.text


def main():
    creds = None
    # Check if token.json exists to store user credentials
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If there are no valid credentials, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        # Build the Gmail service
        service = build('gmail', 'v1', credentials=creds)

        conn = create_database()
        
        # Fetch the list of messages in the "Updates" category
        query = 'category:updates'
        results = service.users().messages().list(userId='me', q=query, maxResults=50).execute()
        messages = results.get('messages', [])
        
        email_count=0

        if not messages:
            print('No messages found in Updates category.')
        else:
            for message in messages:
                # Get the ID of the last message
                msg_id = message['id']
                message = service.users().messages().get(userId='me', id=msg_id).execute()

                # print(message.keys())
                
                headers = message['payload']['headers']
                # print(headers)
                for header in headers:
                    if header['name'] == 'Subject':
                        subject = header['value']
                    # print('-'*40)
                    if header['name'] == 'From':
                        sender = header['value']
                
                # Decode and extract text content from the message body
                payload = message['payload']
                parts = payload.get('parts', [])
                full_text = ""

                if not parts:  # If there are no parts, get the body directly
                    print('no parts')
                    data = payload['body']['data']
                    full_text += base64.urlsafe_b64decode(data.encode('ASCII')).decode()
                else:
                    for part in parts:
                        # print('part:', parts.index(part)+1)
                        if part['mimeType'] == 'text/plain':
                            data = part['body']['data']
                            full_text += base64.urlsafe_b64decode(data).decode()

                # Clean up the text by removing links and images
                body = clean_text(full_text)
                # print(cleaned_text)
                
                prediction = predict(subject, body, sender)
                
                insert_email_data(conn, msg_id, sender, subject, body, prediction)
                print(email_count)
                email_count+=1
            conn.close()   

    except Exception as error:
        print(f'An error occurred: {error}')
        
     


if __name__ == "__main__":
  main()
