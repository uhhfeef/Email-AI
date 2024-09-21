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
from database import insert_email_data, create_database 
from predict import predict_email_read

# Define the scope for reading emails
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

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
    if os.path.exists('../config/token.json'):
        creds = Credentials.from_authorized_user_file('../config/token.json', SCOPES)

    # If there are no valid credentials, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('../config/client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open('../config/token.json', 'w') as token:
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
            message_ids = [msg['id'] for msg in messages]
            
            for msg_id in message_ids[49::-1]:  # Start from index 49 and go backwards
                # Get the ID of the last message
                # msg_id = message['id']
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
                
                # prediction = predict(subject, body, sender)
                prediction = predict_email_read(sender, subject, body)
                print(sender)
                insert_email_data(conn, msg_id, sender, subject, body, prediction)
                print(email_count)
                email_count+=1
            conn.close()   

    except Exception as error:
        print(f'An error occurred: {error}')
        
     


if __name__ == "__main__":
  main()
