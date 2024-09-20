from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os.path

# Define the required OAuth scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/pubsub'
]

def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return build('gmail', 'v1', credentials=creds)

def remove_all_watches(service):
    try:
        service.users().stop(userId='me').execute()
        print("All existing watches removed successfully.")
    except Exception as e:
        print(f"Error removing watches: {e}")

def create_watch(service):
    request_body = {
        'labelIds': ['INBOX'],
        'topicName': 'projects/ai-email-reader/topics/gmail-updates'
    }
    try:
        response = service.users().watch(userId='me', body=request_body).execute()
        print("Watch created successfully. Response:", response)
        return response
    except Exception as e:
        print(f"Error creating watch: {e}")
        return None

def main():
    service = get_gmail_service()
    remove_all_watches(service)
    create_watch(service)

if __name__ == '__main__':
    main()