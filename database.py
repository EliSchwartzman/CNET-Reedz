"""
Database connection and CRUD operations
"""
import sqlite3
from datetime import datetime
from typing import List, Optional, Tuple
import bcrypt
from models import User, Bet, Prediction, UserRole, BetStatus, AnswerType

class Database:
    """Database manager for Reedz platform"""
    
    def __init__(self, db_name: str = "reedz.db"):
        self.db_name = db_name
        self.initialize_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    
    def initialize_database(self):
        """Create all necessary tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table (no email field)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'member',
                reedz_balance INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Bets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                week INTEGER NOT NULL,
                answer_type TEXT NOT NULL,
                correct_answer TEXT,
                status TEXT DEFAULT 'open',
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closed_at TIMESTAMP,
                resolved_at TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')
        
        # Predictions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bet_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                answer TEXT NOT NULL,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                points_earned INTEGER,
                FOREIGN KEY (bet_id) REFERENCES bets(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(bet_id, user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # ==================== USER OPERATIONS ====================
    
    def create_user(self, username: str, password: str, 
                   role: UserRole = UserRole.MEMBER) -> Tuple[bool, str, Optional[int]]:
        """Create a new user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Hash password
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
            
            cursor.execute('''
                INSERT INTO users (username, password_hash, role)
                VALUES (?, ?, ?)
            ''', (username, password_hash, role.value))
            
            user_id = cursor.lastrowid
            conn.commit()
            return True, "User created successfully", user_id
        
        except sqlite3.IntegrityError as e:
            if 'username' in str(e):
                return False, "Username already exists", None
            return False, "User creation failed", None
        
        except Exception as e:
            return False, f"Error: {str(e)}", None
        
        finally:
            conn.close()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return User(
                id=row['id'],
                username=row['username'],
                password_hash=row['password_hash'],
                role=UserRole(row['role']),
                reedz_balance=row['reedz_balance'],
                is_active=bool(row['is_active']),
                created_at=row['created_at']
            )
        return None
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return User(
                id=row['id'],
                username=row['username'],
                password_hash=row['password_hash'],
                role=UserRole(row['role']),
                reedz_balance=row['reedz_balance'],
                is_active=bool(row['is_active']),
                created_at=row['created_at']
            )
        return None
    
    def get_all_users(self) -> List[User]:
        """Get all users"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users ORDER BY reedz_balance DESC')
        rows = cursor.fetchall()
        conn.close()
        
        users = []
        for row in rows:
            users.append(User(
                id=row['id'],
                username=row['username'],
                password_hash=row['password_hash'],
                role=UserRole(row['role']),
                reedz_balance=row['reedz_balance'],
                is_active=bool(row['is_active']),
                created_at=row['created_at']
            ))
        return users
    
    def update_user_role(self, user_id: int, new_role: UserRole) -> Tuple[bool, str]:
        """Update user's role"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('UPDATE users SET role = ? WHERE id = ?', 
                         (new_role.value, user_id))
            conn.commit()
            
            if cursor.rowcount > 0:
                return True, "Role updated successfully"
            return False, "User not found"
        
        except Exception as e:
            return False, f"Error: {str(e)}"
        
        finally:
            conn.close()
    
    def update_user_reedz(self, user_id: int, amount: int) -> Tuple[bool, str]:
        """Add or subtract Reedz from user balance"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE users 
                SET reedz_balance = reedz_balance + ? 
                WHERE id = ?
            ''', (amount, user_id))
            conn.commit()
            
            if cursor.rowcount > 0:
                return True, f"Updated balance by {amount} Reedz"
            return False, "User not found"
        
        except Exception as e:
            return False, f"Error: {str(e)}"
        
        finally:
            conn.close()

    def set_user_reedz(self, user_id: int, new_balance: int) -> Tuple[bool, str]:
        """Set user's Reedz balance to a specific amount (admin only)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE users 
                SET reedz_balance = ? 
                WHERE id = ?
            ''', (new_balance, user_id))
            conn.commit()
            
            if cursor.rowcount > 0:
                return True, f"Reedz balance set to {new_balance}"
            return False, "User not found"
        
        except Exception as e:
            return False, f"Error: {str(e)}"
        
        finally:
            conn.close()

    
    def delete_user(self, user_id: int) -> Tuple[bool, str]:
        """Delete a user from the system"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if user exists
            cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            
            if not user:
                return False, "User not found"
            
            username = user['username']
            
            # Delete user's predictions first (foreign key constraint)
            cursor.execute('DELETE FROM predictions WHERE user_id = ?', (user_id,))
            
            # Delete user
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            
            conn.commit()
            return True, f"✅ User '{username}' has been removed from the system"
        
        except Exception as e:
            conn.rollback()
            return False, f"Error: {str(e)}"
        
        finally:
            conn.close()
    
    # ==================== BET OPERATIONS ====================
    
    def create_bet(self, title: str, description: str, week: int, 
                   answer_type: AnswerType, created_by: int) -> Tuple[bool, str, Optional[int]]:
        """Create a new bet"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO bets (title, description, week, answer_type, created_by)
                VALUES (?, ?, ?, ?, ?)
            ''', (title, description, week, answer_type.value, created_by))
            
            bet_id = cursor.lastrowid
            conn.commit()
            return True, "Bet created successfully", bet_id
        
        except Exception as e:
            return False, f"Error: {str(e)}", None
        
        finally:
            conn.close()
    
    def get_bet(self, bet_id: int) -> Optional[Bet]:
        """Get bet by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM bets WHERE id = ?', (bet_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return Bet(
                id=row['id'],
                title=row['title'],
                description=row['description'],
                week=row['week'],
                answer_type=AnswerType(row['answer_type']),
                correct_answer=row['correct_answer'],
                status=BetStatus(row['status']),
                created_by=row['created_by'],
                created_at=row['created_at'],
                closed_at=row['closed_at'],
                resolved_at=row['resolved_at']
            )
        return None
    
    def get_bets_by_status(self, status: BetStatus) -> List[Bet]:
        """Get all bets with specific status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM bets WHERE status = ? ORDER BY week DESC, created_at DESC', 
                      (status.value,))
        rows = cursor.fetchall()
        conn.close()
        
        bets = []
        for row in rows:
            bets.append(Bet(
                id=row['id'],
                title=row['title'],
                description=row['description'],
                week=row['week'],
                answer_type=AnswerType(row['answer_type']),
                correct_answer=row['correct_answer'],
                status=BetStatus(row['status']),
                created_by=row['created_by'],
                created_at=row['created_at'],
                closed_at=row['closed_at'],
                resolved_at=row['resolved_at']
            ))
        return bets
    
    def get_all_bets(self) -> List[Bet]:
        """Get all bets"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM bets ORDER BY week DESC, created_at DESC')
        rows = cursor.fetchall()
        conn.close()
        
        bets = []
        for row in rows:
            bets.append(Bet(
                id=row['id'],
                title=row['title'],
                description=row['description'],
                week=row['week'],
                answer_type=AnswerType(row['answer_type']),
                correct_answer=row['correct_answer'],
                status=BetStatus(row['status']),
                created_by=row['created_by'],
                created_at=row['created_at'],
                closed_at=row['closed_at'],
                resolved_at=row['resolved_at']
            ))
        return bets
    
    def update_bet_status(self, bet_id: int, status: BetStatus) -> Tuple[bool, str]:
        """Update bet status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            timestamp_field = None
            if status == BetStatus.CLOSED:
                timestamp_field = 'closed_at'
            elif status == BetStatus.RESOLVED:
                timestamp_field = 'resolved_at'
            
            if timestamp_field:
                cursor.execute(f'''
                    UPDATE bets 
                    SET status = ?, {timestamp_field} = CURRENT_TIMESTAMP 
                    WHERE id = ?
                ''', (status.value, bet_id))
            else:
                cursor.execute('UPDATE bets SET status = ? WHERE id = ?', 
                             (status.value, bet_id))
            
            conn.commit()
            
            if cursor.rowcount > 0:
                return True, "Bet status updated"
            return False, "Bet not found"
        
        except Exception as e:
            return False, f"Error: {str(e)}"
        
        finally:
            conn.close()
    
    def set_bet_answer(self, bet_id: int, correct_answer: str) -> Tuple[bool, str]:
        """Set the correct answer for a bet"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE bets 
                SET correct_answer = ? 
                WHERE id = ?
            ''', (correct_answer, bet_id))
            conn.commit()
            
            if cursor.rowcount > 0:
                return True, "Answer set successfully"
            return False, "Bet not found"
        
        except Exception as e:
            return False, f"Error: {str(e)}"
        
        finally:
            conn.close()
    
    # ==================== PREDICTION OPERATIONS ====================
    
    def create_prediction(self, bet_id: int, user_id: int, answer: str) -> Tuple[bool, str]:
        """Create a prediction"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO predictions (bet_id, user_id, answer)
                VALUES (?, ?, ?)
            ''', (bet_id, user_id, answer))
            conn.commit()
            return True, "Prediction submitted successfully"
        
        except sqlite3.IntegrityError:
            return False, "You've already submitted a prediction for this bet"
        
        except Exception as e:
            return False, f"Error: {str(e)}"
        
        finally:
            conn.close()
    
    def get_predictions_for_bet(self, bet_id: int) -> List[Prediction]:
        """Get all predictions for a bet"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM predictions WHERE bet_id = ?', (bet_id,))
        rows = cursor.fetchall()
        conn.close()
        
        predictions = []
        for row in rows:
            predictions.append(Prediction(
                id=row['id'],
                bet_id=row['bet_id'],
                user_id=row['user_id'],
                answer=row['answer'],
                submitted_at=row['submitted_at'],
                points_earned=row['points_earned']
            ))
        return predictions
    
    def get_predictions_by_user(self, user_id: int) -> List[Prediction]:
        """Get all predictions by a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM predictions WHERE user_id = ? ORDER BY submitted_at DESC', 
                      (user_id,))
        rows = cursor.fetchall()
        conn.close()
        
        predictions = []
        for row in rows:
            predictions.append(Prediction(
                id=row['id'],
                bet_id=row['bet_id'],
                user_id=row['user_id'],
                answer=row['answer'],
                submitted_at=row['submitted_at'],
                points_earned=row['points_earned']
            ))
        return predictions
    
    def update_prediction_points(self, prediction_id: int, points: int) -> Tuple[bool, str]:
        """Update points earned for a prediction"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE predictions 
                SET points_earned = ? 
                WHERE id = ?
            ''', (points, prediction_id))
            conn.commit()
            
            if cursor.rowcount > 0:
                return True, "Points updated"
            return False, "Prediction not found"
        
        except Exception as e:
            return False, f"Error: {str(e)}"
        
        finally:
            conn.close()
