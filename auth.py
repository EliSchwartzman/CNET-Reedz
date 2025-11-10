"""
Authentication and authorization logic
"""
import bcrypt
from typing import Tuple, Optional
from database import Database
from models import User, UserRole

class AuthManager:
    """Handle authentication operations"""
    
    def __init__(self, db: Database):
        self.db = db
    
    def register(self, username: str, password: str) -> Tuple[bool, str, Optional[int]]:
        """
        Register a new user
        
        Returns: (success, message, user_id)
        """
        # Validation
        if not username or len(username) < 3:
            return False, "Username must be at least 3 characters", None
        
        if not password or len(password) < 6:
            return False, "Password must be at least 6 characters", None
        
        # Create user
        return self.db.create_user(username, password)
    
    def login(self, username: str, password: str) -> Tuple[bool, str, Optional[User]]:
        """
        Authenticate a user
        
        Returns: (success, message, user_object)
        """
        # Get user
        user = self.db.get_user_by_username(username)
        
        if not user:
            return False, "Invalid username or password", None
        
        if not user.is_active:
            return False, "Account is disabled", None
        
        # Verify password
        if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return True, "Login successful", user
        else:
            return False, "Invalid username or password", None
    
    def require_admin(self, user: User) -> Tuple[bool, str]:
        """
        Check if user has admin privileges
        
        Returns: (is_admin, message)
        """
        if user.is_admin():
            return True, "Access granted"
        return False, "Admin access required"
    
    def promote_user(self, admin_user: User, target_user_id: int, 
                     new_role: UserRole) -> Tuple[bool, str]:
        """
        Promote a user to a new role (admin only)
        
        Returns: (success, message)
        """
        # Check admin privileges
        is_admin, msg = self.require_admin(admin_user)
        if not is_admin:
            return False, msg
        
        # Update role
        return self.db.update_user_role(target_user_id, new_role)