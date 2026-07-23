import os.path
import sqlite3
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import base64
import json
from engine.llm_provider import generate

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
DB_PATH = "jobs.db"

def authenticate_gmail():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("Missing credentials.json. Please download it from Google Cloud Console.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    return creds

def get_message_body(payload):
    body = ""
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data', '')
                if data:
                    body += base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
            elif 'parts' in part:
                body += get_message_body(part)
    elif 'body' in payload and 'data' in payload['body']:
        data = payload['body']['data']
        body = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
    return body

def classify_email_with_llm(subject, body):
    prompt = f"""
Analyze the following email and extract the Company Name and the Status of the job application.
The status must be exactly one of: REJECTED, INTERVIEW_REQUEST, or ACKNOWLEDGEMENT.

Email Subject: {subject}
Email Body: {body[:2000]}

Output your response as strict JSON:
{{"company": "Extracted Company Name", "status": "STATUS_ENUM"}}
"""
    try:
        response = generate(prompt, use_case="extraction")
        response = response.replace("```json", "").replace("```", "").strip()
        return json.loads(response)
    except Exception as e:
        print(f"LLM Classification failed: {e}")
        return None

def update_job_status_from_email(company, status):
    if not company or status not in ['REJECTED', 'INTERVIEW_REQUEST']:
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM jobs WHERE company LIKE ? AND status IN ('applied', 'manual_review', 'interviewing', 'new') ORDER BY rowid DESC LIMIT 1", (f"%{company}%",))
    row = cursor.fetchone()
    if row:
        job_id = row[0]
        db_status = 'rejected' if status == 'REJECTED' else 'interviewing'
        cursor.execute("UPDATE jobs SET status = ? WHERE id = ?", (db_status, job_id))
        conn.commit()
        print(f"  -> Updated job {job_id} ({company}) to {db_status}")
    conn.close()

def scan_inbox():
    creds = authenticate_gmail()
    if not creds:
        return
        
    try:
        service = build('gmail', 'v1', credentials=creds)
        print("Connected to Gmail API successfully.")
        
        # Example query: search for rejections, interviews, or confirmations
        query = 'subject:("application" OR "interview" OR "rejected" OR "update")'
        results = service.users().messages().list(userId='me', q=query, maxResults=10).execute()
        messages = results.get('messages', [])

        if not messages:
            print('No recent job-related messages found.')
            return

        print('Scanning recent messages:')
        for msg in messages:
            msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
            payload = msg_data.get('payload', {})
            headers = payload.get('headers', [])
            subject = next((header['value'] for header in headers if header['name'] == 'Subject'), 'No Subject')
            print(f"- {subject}")
            
            body = get_message_body(payload)
            classification = classify_email_with_llm(subject, body)
            
            if classification:
                company = classification.get('company')
                status = classification.get('status')
                print(f"  -> Detected: {company} | Status: {status}")
                if status in ['REJECTED', 'INTERVIEW_REQUEST']:
                    update_job_status_from_email(company, status)

    except Exception as error:
        print(f'An error occurred: {error}')

def generate_digest():
    """Prints a daily digest of database activity."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'")
    if not cursor.fetchone():
        print("Database not initialized yet.")
        conn.close()
        return
        
    cursor.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status")
    rows = cursor.fetchall()
    conn.close()
    
    print("\n--- Daily Application Digest ---")
    status_counts = dict(rows)
    print(f"Total Jobs Discovered (New): {status_counts.get('new', 0)}")
    print(f"Applications Sent: {status_counts.get('applied', 0)}")
    print(f"Needs Manual Review: {status_counts.get('manual_review', 0)}")
    print(f"Failed Submissions: {status_counts.get('failed_submission', 0)}")
    print(f"Interviews Requested: {status_counts.get('interviewing', 0)}")
    print(f"Rejections: {status_counts.get('rejected', 0)}")
    print("--------------------------------\n")
