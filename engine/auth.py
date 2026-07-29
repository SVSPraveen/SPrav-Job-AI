"""
engine/auth.py
==============
Full authentication layer for SPrav Job AI.
- SQLite-based user accounts (permanent, local, no cloud)
- bcrypt password hashing with backward compatibility for legacy hashes
- JWT access tokens (30-day lifetime)
- AES-GCM Encrypted credential storage (with transparent migration for legacy XOR)
"""

import jwt
import sqlite3
import hashlib
import os
import base64
import smtplib
import secrets
import bcrypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from email.message import EmailMessage
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = os.getenv("JWT_SECRET")
if not SECRET_KEY:
    raise ValueError("CRITICAL SECURITY ERROR: JWT_SECRET is missing from your .env file. A unique secret is required for secure authentication.")
ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 30
from engine.utils import get_data_dir

USERS_DB = os.path.join(get_data_dir(), "users.db")

security = HTTPBearer()

# ─── Database Setup ──────────────────────────────────────────────────────────

def init_users_db():
    """Create users and credentials tables if they don't exist."""
    conn = sqlite3.connect(USERS_DB, timeout=30.0)
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
    
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN recovery_key_hash TEXT")
    except sqlite3.OperationalError:
        pass # Column already exists

    conn.commit()
    conn.close()

init_users_db()

# ─── Password Hashing ────────────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    """bcrypt hashing for new passwords."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def _verify_password(password: str, password_hash: str) -> bool:
    """Verifies bcrypt hashes, falls back to legacy SHA-256 for old passwords."""
    if password_hash.startswith("$2b$") or password_hash.startswith("$2a$"):
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    else:
        # Legacy SHA-256 fallback
        salt = SECRET_KEY[:16]
        return hashlib.sha256(f"{salt}{password}".encode()).hexdigest() == password_hash

# ─── Credential Encryption (AES-GCM) ─────────────────────────────────────────

def _get_aes_key() -> bytes:
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b'sprav-credential-encryption',
    )
    return hkdf.derive(SECRET_KEY.encode('utf-8'))

def _simple_encrypt(value: str) -> str:
    """Robust AES-GCM encryption."""
    if not value:
        return ""
    aesgcm = AESGCM(_get_aes_key())
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, value.encode('utf-8'), None)
    return base64.b64encode(nonce + ciphertext).decode('utf-8')

def _simple_decrypt(encrypted: str) -> str:
    """Decrypts AES-GCM, falls back to legacy XOR if formatted differently."""
    if not encrypted:
        return ""
    try:
        data = base64.b64decode(encrypted.encode('utf-8'))
        is_legacy = False
        if len(data) >= 28:
            try:
                aesgcm = AESGCM(_get_aes_key())
                nonce = data[:12]
                ciphertext = data[12:]
                return aesgcm.decrypt(nonce, ciphertext, None).decode('utf-8')
            except Exception:
                is_legacy = True
        else:
            is_legacy = True
            
        if is_legacy:
            key = (SECRET_KEY * 10)[:len(data)]
            return bytes(a ^ b for a, b in zip(data, key.encode('utf-8'))).decode('utf-8')
    except Exception:
        pass
    return ""

# ─── User Account Operations ─────────────────────────────────────────────────

def has_any_account() -> bool:
    conn = sqlite3.connect(USERS_DB, timeout=30.0)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

def create_user(name: str, email: str, password: str) -> dict:
    conn = sqlite3.connect(USERS_DB, timeout=30.0)
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

# Store layout: {email: {"code": otp_code, "time": datetime, "attempts": int, "last_attempt": datetime}}
otp_store = {}

def send_otp(email: str):
    email = email.strip().lower()
    now = datetime.now()
    
    # Rate Limiting
    if email in otp_store:
        limits = otp_store[email]
        if limits.get("attempts", 0) >= 3 and (now - limits.get("last_attempt", now)).total_seconds() < 900:
            raise HTTPException(status_code=429, detail="Too many attempts. Please wait 15 minutes.")
        if (now - limits.get("last_attempt", now)).total_seconds() < 60:
            raise HTTPException(status_code=429, detail="Please wait 60 seconds before requesting another OTP.")
            
        limits["attempts"] = limits.get("attempts", 0) + 1
        limits["last_attempt"] = now
    else:
        otp_store[email] = {"attempts": 1, "last_attempt": now}
    
    conn = sqlite3.connect(USERS_DB, timeout=30.0)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    
    # Generic Anti-Enumeration Response
    success_msg = {"message": "If that email exists in our system, an OTP has been sent."}
    if not row:
        return success_msg
        
    sender_email = os.getenv("EMAIL_SENDER")
    sender_password = os.getenv("EMAIL_PASSWORD")
    
    if not sender_email or not sender_password:
        raise HTTPException(status_code=400, detail="Email OTP requires EMAIL_SENDER and EMAIL_PASSWORD in .env")
        
    otp_code = str(secrets.randbelow(900000) + 100000)
    otp_store[email]["code"] = otp_code
    otp_store[email]["time"] = now
    
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
        
    return success_msg

def reset_password(email: str, recovery_key: str, new_password: str):
    email = email.strip().lower()
    is_otp = recovery_key.strip().isdigit() and len(recovery_key.strip()) == 6
    
    conn = sqlite3.connect(USERS_DB, timeout=30.0)
    cursor = conn.cursor()
    
    if is_otp:
        if email not in otp_store or "code" not in otp_store[email]:
            conn.close()
            raise HTTPException(status_code=401, detail="No OTP requested for this email.")
            
        stored = otp_store[email]
        if stored["code"] != recovery_key.strip():
            conn.close()
            raise HTTPException(status_code=401, detail="Invalid OTP code.")
            
        if (datetime.now() - stored["time"]).total_seconds() > 600:
            del otp_store[email]["code"]
            conn.close()
            raise HTTPException(status_code=401, detail="OTP expired. Please request a new one.")
            
        del otp_store[email]["code"]
        
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
        
        # Transparent migration for recovery_key
        if not row[1].startswith("$2b$") and not row[1].startswith("$2a$"):
            cursor.execute("UPDATE users SET recovery_key_hash = ? WHERE id = ?", (_hash_password(recovery_key.strip()), user_id))
        
    cursor.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (_hash_password(new_password), user_id)
    )
    conn.commit()
    conn.close()
    return {"status": "success"}

def authenticate_user(email: str, password: str) -> dict:
    conn = sqlite3.connect(USERS_DB, timeout=30.0)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, email, password_hash FROM users WHERE email = ?",
        (email.strip().lower(),)
    )
    row = cursor.fetchone()

    if not row or not _verify_password(password, row[3]):
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )
        
    user_id, name, user_email, password_hash = row
    
    # Transparent Migration to bcrypt
    if not password_hash.startswith("$2b$") and not password_hash.startswith("$2a$"):
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (_hash_password(password), user_id))

    cursor.execute("UPDATE users SET last_login = datetime('now') WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    return {"id": user_id, "name": name, "email": user_email}

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
    conn = sqlite3.connect(USERS_DB, timeout=30.0)
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
    conn = sqlite3.connect(USERS_DB, timeout=30.0)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT cred_key, cred_value FROM credentials WHERE user_id = ? AND service = ?",
        (user_id, service)
    )
    rows = cursor.fetchall()
    
    result = {}
    
    for row in rows:
        cred_key = row[0]
        enc_value = row[1]
        decrypted = _simple_decrypt(enc_value)
        result[cred_key] = decrypted
        
    conn.close()
    return result

def get_all_credentials(user_id: int) -> dict:
    conn = sqlite3.connect(USERS_DB, timeout=30.0)
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
        result[service][key] = {
            "is_set": bool(decrypted),
            "updated_at": updated_at
        }
    return result

# ─── Copilot History ─────────────────────────────────────────────────────────

def save_copilot_message(user_id: int, role: str, content: str):
    conn = sqlite3.connect(USERS_DB, timeout=30.0)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO copilot_history (user_id, role, content) VALUES (?, ?, ?)",
        (user_id, role, content)
    )
    conn.commit()
    conn.close()

def get_copilot_history(user_id: int, limit: int = 20) -> list:
    conn = sqlite3.connect(USERS_DB, timeout=30.0)
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
    conn = sqlite3.connect(USERS_DB, timeout=30.0)
    cursor = conn.cursor()
    cursor.execute("SELECT email, password_hash FROM users LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0], row[1]
    return "admin@localhost", "admin123"

def get_system_credential(service: str, key: str) -> str | None:
    conn = sqlite3.connect(USERS_DB, timeout=30.0)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
        
    creds = get_credentials(row[0], service)
    return creds.get(key)
