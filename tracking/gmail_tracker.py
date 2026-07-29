import os.path
import os
import sqlite3
import email as email_lib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import base64
import json
from engine.llm_provider import generate

# NOTE: Scope now includes gmail.send for Direct Cold Email outreach to Founders/Recruiters.
# If you are upgrading from an older version, delete token.json and
# re-authorize once to grant the new scope.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
]
from engine.utils import get_data_dir
import os
DB_PATH = os.path.join(get_data_dir(), "jobs.db")

def authenticate_gmail():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    token_path = os.path.join(get_data_dir(), 'token.json')
    creds_path = os.path.join(get_data_dir(), 'credentials.json')
    
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(creds_path):
                print(f"Missing {creds_path}. Please download it from Google Cloud Console.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(
                creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
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

def get_html_body(payload):
    body = ""
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/html':
                data = part['body'].get('data', '')
                if data:
                    body += base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
            elif 'parts' in part:
                body += get_html_body(part)
    elif 'body' in payload and 'data' in payload['body']:
        # If it's a single part email and it's HTML, the payload might not have 'parts'
        if payload.get('mimeType') == 'text/html':
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
        
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
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

def send_email(to: str, subject: str, body_text: str, attachment_path: str = None) -> bool:
    """
    Sends an email via the Gmail API.
    Optionally attaches a file (e.g. a tailored resume PDF).
    Returns True on success, False on failure.
    """
    creds = authenticate_gmail()
    if not creds:
        print("[Gmail] Cannot send — not authenticated.")
        return False

    try:
        service = build('gmail', 'v1', credentials=creds)

        msg = MIMEMultipart()
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body_text, 'plain'))

        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, 'rb') as f:
                part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
            msg.attach(part)

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        service.users().messages().send(
            userId='me',
            body={'raw': raw}
        ).execute()

        print(f"[Gmail] Email sent successfully to {to}")
        return True

    except Exception as e:
        print(f"[Gmail] Failed to send email: {e}")
        return False

def scan_inbox():
    creds = authenticate_gmail()
    if not creds:
        return
        
    try:
        service = build('gmail', 'v1', credentials=creds)
        print("Connected to Gmail API successfully.")
        
        # 1. Scan for Application Updates (Rejections, Interviews)
        query_updates = 'subject:("application" OR "interview" OR "rejected" OR "update") -from:wellfound.com'
        results_updates = service.users().messages().list(userId='me', q=query_updates, maxResults=10).execute()
        messages_updates = results_updates.get('messages', [])

        if messages_updates:
            print('Scanning recent application update messages:')
            for msg in messages_updates:
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

        # 2. Scan for Wellfound Job Alerts (Discovery via Email)
        query_discovery = 'from:wellfound.com subject:("jobs" OR "alert" OR "matches")'
        results_discovery = service.users().messages().list(userId='me', q=query_discovery, maxResults=5).execute()
        messages_discovery = results_discovery.get('messages', [])

        if messages_discovery:
            print('Scanning Wellfound Job Alert emails for discovery:')
            import uuid
            import requests
            from bs4 import BeautifulSoup
            
            for msg in messages_discovery:
                msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
                payload = msg_data.get('payload', {})
                
                # We need the HTML body to extract exact, unhallucinated URLs
                html_body = get_html_body(payload)
                if not html_body:
                    html_body = get_message_body(payload) # Fallback to text if no HTML part exists
                    
                soup = BeautifulSoup(html_body, 'html.parser')
                
                # Extract all Wellfound job links directly from the DOM
                links = soup.find_all('a', href=True)
                job_links = []
                for a in links:
                    href = a['href']
                    text = a.get_text(strip=True)
                    if ('wellfound.com/jobs/' in href or 'angel.co/jobs/' in href) and text:
                        if not any(j['url'] == href for j in job_links):
                            job_links.append({"text": text, "url": href})
                
                if not job_links:
                    continue
                    
                # Use LLM to structure title/company/location from surrounding text, strictly mapping to the provided exact URLs
                prompt = f"""You are a data extractor. I have extracted the following exact job URLs and their link text from a Wellfound digest email.
Please analyze the email content and provide the exact Company Name, Job Title, and Location for each URL. Do NOT change the URLs.

Exact Job Links Found:
{json.dumps(job_links, indent=2)}

Output STRICT JSON as an array of objects: [{{"title": "...", "company": "...", "url": "...", "location": "...", "description": "..."}}]
If you cannot determine the details for a URL, provide your best guess based on the link text."""

                try:
                    res = generate(prompt, use_case="extraction")
                    res = res.replace("```json", "").replace("```", "").strip()
                    extracted_jobs = json.loads(res)
                    
                    if extracted_jobs:
                        formatted = []
                        for j in extracted_jobs:
                            # Verify the URL was one of our exact extracted URLs to prevent hallucinations
                            exact_url = j.get("url", "")
                            if not any(exact_url == l["url"] for l in job_links):
                                continue # Skip hallucinated URLs
                                
                            formatted.append({
                                "id": f"wellfound_email_{uuid.uuid4().hex[:8]}",
                                "title": j.get("title", "Unknown"),
                                "company": j.get("company", "Unknown"),
                                "url": exact_url,
                                "description": j.get("description", "Source: Wellfound Email Alert"),
                                "location": j.get("location", "Remote"),
                                "source": "wellfound_email"
                            })
                        
                        if formatted:
                            print(f"  -> Extracted {len(formatted)} verified jobs from Wellfound email. Sending to pipeline...")
                            resp = requests.post('http://127.0.0.1:8000/api/jobs/bulk', json=formatted)
                            print(f"  -> Ingestion response: {resp.text}")
                except Exception as e:
                    print(f"  -> Failed to parse Wellfound email: {e}")

    except Exception as error:
        print(f'An error occurred: {error}')

def generate_digest():
    """Prints a daily digest of database activity."""
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
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
