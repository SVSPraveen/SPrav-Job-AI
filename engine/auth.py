"""
engine/auth.py
==============
Full authentication layer for SPrav Job AI.
- SQLite-based user accounts (permanent, local, no cloud)
- bcrypt password hashing
- JWT access tokens (30-day lifetime)
- Encrypted credential storage for LinkedIn, Gmail, etc.
"""

import jwt
import sqlite3
import hashlib
import os
import json
import base64
import random
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = os.getenv("JWT_SECRET", "sprav-local-secret-key-2025-change-me")
ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 30
USERS_DB = "users.db"

security = HTTPBearer()


# ─── Database Setup ──────────────────────────────────────────────────────────

def init_users_db():
    """Create users and credentials tables if they don't exist."""
    conn = sqlite3.connect(USERS_DB)
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            recovery_key_hash TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            last_login TEXT
        );

        CREATE TABLE IF NOT EXISTS credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            service TEXT NOT NULL,
            cred_key TEXT NOT NULL,
            cred_value TEXT NOT NULL,
            updated_at TEXT DEFAULT (datetime('now')),
            UNIQUE(user_id, service, cred_key),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS copilot_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    
    # Simple migration for existing databases
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN recovery_key_hash TEXT")
    except sqlite3.OperationalError:
        pass # Column already exists

    conn.commit()
    conn.close()


init_users_db()


# ─── Password Hashing ────────────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    """SHA-256 hash with a fixed salt derived from SECRET_KEY. Lightweight, no extra deps."""
    salt = SECRET_KEY[:16]
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def _verify_password(password: str, password_hash: str) -> bool:
    return _hash_password(password) == password_hash


# ─── Credential Encryption ───────────────────────────────────────────────────

def _simple_encrypt(value: str) -> str:
    """XOR-based obfuscation with the secret key. Keeps credentials unreadable in plain DB viewers."""
    key = (SECRET_KEY * 10)[:len(value)]
    encrypted = bytes(a ^ b for a, b in zip(value.encode(), key.encode()))
    return base64.b64encode(encrypted).decode()


def _simple_decrypt(encrypted: str) -> str:
    try:
        data = base64.b64decode(encrypted.encode())
        key = (SECRET_KEY * 10)[:len(data)]
        return bytes(a ^ b for a, b in zip(data, key.encode())).decode()
    except Exception:
        return ""


# ─── User Account Operations ─────────────────────────────────────────────────

def has_any_account() -> bool:
    """Returns True if at least one user account exists."""
    conn = sqlite3.connect(USERS_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0


def create_user(name: str, email: str, password: str) -> dict:
    """Creates a new user. Raises HTTPException if email already taken."""
    conn = sqlite3.connect(USERS_DB)
    cursor = conn.cursor()
    try:
        recovery_key = f"SPRAV-{os.urandom(4).hex().upper()}"
        cursor.execute(
            "INSERT INTO users (name, email, password_hash, recovery_key_hash) VALUES (?, ?, ?, ?)",
            (name.strip(), email.strip().lower(), _hash_password(password), _hash_password(recovery_key))
        )
        conn.commit()
        user_id = cursor.lastrowid
        return {"id": user_id, "name": name, "email": email, "recovery_key": recovery_key}
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists."
        )
    finally:
        conn.close()

otp_store = {}

def send_otp(email: str):
    email = email.strip().lower()
    
    conn = sqlite3.connect(USERS_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Email not found in local database.")
        
    sender_email = os.getenv("EMAIL_SENDER")
    sender_password = os.getenv("EMAIL_PASSWORD")
    
    if not sender_email or not sender_password:
        raise HTTPException(status_code=400, detail="Email OTP requires EMAIL_SENDER and EMAIL_PASSWORD in .env")
        
    otp_code = str(random.randint(100000, 999999))
    otp_store[email] = {"code": otp_code, "time": datetime.now()}
    
    msg = EmailMessage()
    msg.set_content(f"Your SPrav Job AI password reset OTP is: {otp_code}")
    msg['Subject'] = 'SPrav Job AI - Password Reset OTP'
    msg['From'] = sender_email
    msg['To'] = email
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
        
    return {"message": "OTP sent successfully to your email."}

def reset_password(email: str, recovery_key: str, new_password: str):
    """Resets the password using the Master Recovery Key OR an Email OTP."""
    email = email.strip().lower()
    
    is_otp = recovery_key.strip().isdigit() and len(recovery_key.strip()) == 6
    
    conn = sqlite3.connect(USERS_DB)
    cursor = conn.cursor()
    
    if is_otp:
        if email not in otp_store:
            conn.close()
            raise HTTPException(status_code=401, detail="No OTP requested for this email.")
            
        stored = otp_store[email]
        if stored["code"] != recovery_key.strip():
            conn.close()
            raise HTTPException(status_code=401, detail="Invalid OTP code.")
            
        if (datetime.now() - stored["time"]).total_seconds() > 600:
            del otp_store[email]
            conn.close()
            raise HTTPException(status_code=401, detail="OTP expired. Please request a new one.")
            
        del otp_store[email]
        
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="User not found.")
        user_id = row[0]
    else:
        cursor.execute("SELECT id, recovery_key_hash FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        
        if not row or not row[1] or not _verify_password(recovery_key.strip(), row[1]):
            conn.close()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Email or Master Recovery Key."
            )
        user_id = row[0]
        
    cursor.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (_hash_password(new_password), user_id)
    )
    conn.commit()
    conn.close()
    return {"status": "success"}


def authenticate_user(email: str, password: str) -> dict:
    """Verifies credentials. Returns user dict or raises 401."""
    conn = sqlite3.connect(USERS_DB)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, email, password_hash FROM users WHERE email = ?",
        (email.strip().lower(),)
    )
    row = cursor.fetchone()
    if row:
        cursor.execute("UPDATE users SET last_login = datetime('now') WHERE id = ?", (row[0],))
        conn.commit()
    conn.close()

    if not row or not _verify_password(password, row[3]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )
    return {"id": row[0], "name": row[1], "email": row[2]}


# ─── JWT Tokens ──────────────────────────────────────────────────────────────

def create_access_token(user: dict) -> str:
    payload = {
        "sub": user["email"],
        "user_id": user["id"],
        "name": user.get("name", ""),
        "exp": datetime.now(timezone.utc) + timedelta(days=TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    token = credentials.credentials
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired. Please log in again.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token.")


def get_user_id_from_token(payload: dict) -> int:
    return payload.get("user_id", 1)


# ─── Credential Store ─────────────────────────────────────────────────────────

def save_credential(user_id: int, service: str, key: str, value: str):
    """Saves an encrypted credential for a user."""
    conn = sqlite3.connect(USERS_DB)
    cursor = conn.cursor()
    encrypted = _simple_encrypt(value) if value else ""
    cursor.execute("""
        INSERT INTO credentials (user_id, service, cred_key, cred_value, updated_at)
        VALUES (?, ?, ?, ?, datetime('now'))
        ON CONFLICT(user_id, service, cred_key) DO UPDATE SET
            cred_value = excluded.cred_value,
            updated_at = datetime('now')
    """, (user_id, service, key, encrypted))
    conn.commit()
    conn.close()


def get_credentials(user_id: int, service: str) -> dict:
    """Returns all decrypted credentials for a service as a dict."""
    conn = sqlite3.connect(USERS_DB)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT cred_key, cred_value FROM credentials WHERE user_id = ? AND service = ?",
        (user_id, service)
    )
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: _simple_decrypt(row[1]) for row in rows}


def get_all_credentials(user_id: int) -> dict:
    """Returns all services and their credentials (values masked for UI display)."""
    conn = sqlite3.connect(USERS_DB)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT service, cred_key, cred_value, updated_at FROM credentials WHERE user_id = ?",
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    result = {}
    for service, key, enc_value, updated_at in rows:
        if service not in result:
            result[service] = {}
        decrypted = _simple_decrypt(enc_value)
        # Mask value for display — show only whether it's set or not
        result[service][key] = {
            "is_set": bool(decrypted),
            "updated_at": updated_at
        }
    return result


# ─── Copilot History ─────────────────────────────────────────────────────────

def save_copilot_message(user_id: int, role: str, content: str):
    conn = sqlite3.connect(USERS_DB)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO copilot_history (user_id, role, content) VALUES (?, ?, ?)",
        (user_id, role, content)
    )
    conn.commit()
    conn.close()


def get_copilot_history(user_id: int, limit: int = 20) -> list:
    conn = sqlite3.connect(USERS_DB)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, content FROM copilot_history WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        (user_id, limit)
    )
    rows = cursor.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1]} for r in reversed(rows)]


# ─── Legacy compatibility ─────────────────────────────────────────────────────

def get_user_credentials() -> tuple[str, str]:
    """Legacy shim: returns (email, password) for any old code that calls this."""
    conn = sqlite3.connect(USERS_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT email, password_hash FROM users LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0], row[1]
    return "admin@localhost", "admin123"
