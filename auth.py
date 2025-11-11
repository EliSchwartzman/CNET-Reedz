import hashlib
import hmac
from supabase_db import SupabaseDatabase
from models import UserRole

db = SupabaseDatabase()

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == password_hash

def register_user(username: str, password: str, role: UserRole = UserRole.MEMBER) -> tuple[bool, str, int]:
    """Register a new user"""
    if not username or not password:
        return False, "Username and password required", 0
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters", 0
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters", 0
    
    # Check if user exists
    existing_user = db.get_user_by_username(username)
    if existing_user:
        return False, "Username already exists", 0
    
    # Create user with the specified role
    password_hash = hash_password(password)
    success, message, user_id = db.create_user(username, password_hash, role)
    
    return success, message, user_id or 0

def login_user(username: str, password: str) -> tuple[bool, str, int]:
    """Login a user"""
    if not username or not password:
        return False, "Username and password required", 0
    
    user = db.get_user_by_username(username)
    if not user:
        return False, "Invalid username or password", 0
    
    if not user.is_active:
        return False, "Account is inactive", 0
    
    if not verify_password(password, user.password_hash):
        return False, "Invalid username or password", 0
    
    return True, "Login successful", user.id
